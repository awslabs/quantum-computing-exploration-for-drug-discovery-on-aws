# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

########################################################################################################################
#   Hybrid job for RNA Folding experiments
########################################################################################################################


import logging
import boto3
import json
import os
import sys

__dir__ = os.path.dirname(os.path.abspath(__file__))
sys.path.append(__dir__)

from utility.ProteinParser import ProteinData
from utility.ProteinModel import ProteinModel
from utility.ProteinStructurePrediction import ProteinStructurePrediction

from braket.aws import AwsDevice
from braket.jobs import save_job_result
from braket.jobs.metrics import log_metric
from braket.tracking import Tracker

import time

logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                    datefmt='%Y-%m-%d:%H:%M:%S',
                    level=logging.INFO)
root_path = "./customer_code/extracted/hybridjobs/"

def main():
    t = Tracker().start()
    
    input_dir = os.environ["AMZN_BRAKET_INPUT_DIR"]
    hyperparameters = load_hyperparameters()
    logging.info(f"Hyperparameters are: {hyperparameters}")

    device_string = hyperparameters["device"]
    device_string = device_string.replace("\'", "\"")

    quantum_device_state = json.loads(device_string)["qc"]

    if quantum_device_state is None:
        logging.info("Pure classical mode")

    logging.info(f"Loading dataset from: {input_dir}")

    list_files(input_dir)

    dir_name = f"{input_dir}/input/"
    dir_list = os.listdir(dir_name)

    complete_results = {}
    # step 1: prepare data
    # raw_path = dir_name
    # data_path = _prepare_data(raw_path, hyperparameters)
    data_path = dir_name
    for file_name in dir_list:
        target_name = file_name.split('.')[0]
        # step 2: create model
        model_path = _build_model(data_path, hyperparameters)
        # step 3: optimize model
        result = _optimize(model_path, target_name, hyperparameters)
        # # step 4: post process
        # result = _post_process(raw_path, data_path, hyperparameters)
        # # print(f"Tree structure: {list_files(input_dir)}")
        logging.info(f"finish experiment for file {target_name}")
        complete_results[target_name] = result

    save_job_result(complete_results)

    logging.info("Saved results. All done.")

def _prepare_data(raw_path, hyperparameters):
    # TODO

    data_path = "protein-folding-data"

    return data_path

def _build_model(data_path, hyperparameters):
    # initial the RNAQUBO object
    init_param = {}

    method = hyperparameters["method"]

    if method == 'qfold-cc':
        init_param[method] = {}
        init_param[method]['params'] = ["initialization"]
    elif method == 'qfold-qc':
        init_param[method] = {}
        init_param[method]['params'] = ["initialization"]

    config_path = f"{root_path}config/config.json"
    logging.info(f"param {init_param}")
    protein_model = ProteinModel(data_path, [method], config_path, **init_param)

    # set the parameters for model
    model_param = {}

    model_param[method] = {}

    model_param[method]["initialization"] = [(hyperparameters["initialization"])]

    protein_model.build_models(**model_param)

    # save the model
    model_path = protein_model.save("latest")

    logging.info(f"You have built the Protein model and saved it as {model_path}")

    return model_path

def _optimize(model_path, target_name, hyperparameters):
    protein_model = ProteinModel.load(model_path)

    # get the model you want to optimize
    protein_name = 'glycylglycine_3_GG'
    initialization = hyperparameters["initialization"]
    method = hyperparameters["method"]
    mode = hyperparameters["mode"]

    model_name = "{}+{}".format(protein_name, initialization)

    protein_model = protein_model.get_model(protein_name, method, model_name)

    data_path = 'data'
    # psp_param stands for the parameters for predicting protein structure
    psp_param = {}
    psp_param["data_path"] = data_path
    psp_param["mode"] = mode
    psp_param["model_name"] = model_name
    psp_param["model_path"] = model_path

    config_path = f"{root_path}config/config.json"
    psp = ProteinStructurePrediction(protein_model, method, config_path, **psp_param)

    psp.run()

    logging.info(f"Finish run protein structure prediction")

    process_result = {}
    process_result["hypermeter"] = hyperparameters
    process_result["result"] = psp.result

    return process_result

def _post_process(raw_path, data_path, hyperparameters):
    # TODO

    process_result = {}

    return process_result

def _save_job_result():
    return None

def list_files(startpath):
    for root, dirs, files in os.walk(startpath):
        level = root.replace(startpath, '').count(os.sep)
        indent = ' ' * 4 * (level)
        print('{}{}/'.format(indent, os.path.basename(root)))
        subindent = ' ' * 4 * (level + 1)
        for f in files:
            print('{}{}'.format(subindent, f))

def load_hyperparameters():
    """Load the Hybrid Job hyperparameters"""
    hp_file = os.environ["AMZN_BRAKET_HP_FILE"]
    with open(hp_file) as f:
        hyperparameters = json.load(f)
    return hyperparameters