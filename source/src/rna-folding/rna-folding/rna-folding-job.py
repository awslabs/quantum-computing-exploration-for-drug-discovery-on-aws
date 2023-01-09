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

from utility.RNAParser import RNAData
from utility.RNAQUBO import RNAQUBO
from utility.AnnealerOptimizer import Annealer
from utility.ResultProcess import ResultParser

from braket.aws import AwsDevice
from braket.jobs import save_job_result
from braket.jobs.metrics import log_metric
from braket.tracking import Tracker

import time

logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                    datefmt='%Y-%m-%d:%H:%M:%S',
                    level=logging.INFO)

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
    raw_path = dir_name
    data_path, mol_data = _prepare_data(raw_path, hyperparameters)
    for file_name in dir_list:
        target_name = file_name.split('.')[0]
        # step 2: create model
        model_path = _build_model(data_path, mol_data, hyperparameters)
        # step 3: optimize model
        task_id = _optimize(model_path, target_name, hyperparameters)
        # step 4: post process
        result = _post_process(raw_path, data_path, hyperparameters)
        # print(f"Tree structure: {list_files(input_dir)}")
        logging.info(f"finish experiment for file {target_name}")
        complete_results[target_name] = result

    save_job_result(complete_results)

    logging.info("Saved results. All done.")

def _prepare_data(raw_path, hyperparameters):
    mol_data = RNAData(raw_path)
    
    data_path = mol_data.save("latest")

    return data_path, mol_data

def _build_model(data_path, mol_data, hyperparameters):
    # initial the RNAQUBO object
    init_param = {}
    method = ["qc"]

    for mt in method:
        if mt == "qc":
            init_param[mt] = {}
            init_param[mt]["params"] = ["PKP", "S", "O"]
        
    
    rna_qubo = RNAQUBO(data_path, method, **init_param)
    # set the parameters for model
    model_param = {}

    method = "qc"
    model_param[method] = {}

    model_param[method]["PKP"] = [float(hyperparameters["PKP"])]
    model_param[method]["S"] = [int(hyperparameters["S"])]
    model_param[method]["O"] = [int(float(hyperparameters["O"]))]

    rna_qubo.build_models(**model_param)
    # describe the model parameters
    model_info = rna_qubo.describe_models()
    # save the model
    model_path = rna_qubo.save("latest")

    logging.info(f"You have built the QUBO model and saved it as {model_path}")

    return model_path

def _optimize(model_path, target_name, hyperparameters):
    rna_qubo_optimize = RNAQUBO.load(model_path)
    PKP = hyperparameters["PKP"]
    S = hyperparameters["S"]
    O = hyperparameters["O"]
    rna_name = target_name

    model_name = "{}+{}+{}+{}+".format(rna_name, PKP, O, S)
    method = "qc"

    qubo_model = rna_qubo_optimize.get_model(rna_name, method, model_name)

    method = 'neal-sa'

    optimizer_param = {}
    optimizer_param['shots'] = int(hyperparameters['shots'])

    sa_optimizer = Annealer(qubo_model, method, **optimizer_param)

    sa_optimize_result = sa_optimizer.fit()

    logging.info(f"dwave-sa run time {sa_optimize_result['time']}")

def _post_process(raw_path, data_path, hyperparameters):
    method = "neal-sa"
    sa_param = {}
    sa_param["raw_path"] = raw_path
    sa_param["data_path"] = data_path

    sa_process_result = ResultParser(method, **sa_param)

    local_time, _ , _, _= sa_process_result.get_time()

    print(f"time for {method}: \n local time is {local_time}")

    sa_atom_pos_data = sa_process_result.generate_optimize_pts()
    # save unfold file for visualization and parameters for experiment: 1. volume value 2. relative improvement
    timestamp = time.strftime("%Y%m%d-%H")
    sa_result_json = sa_process_result.save_file(f"{timestamp}")

    logging.info(f"result optimization file path is {sa_result_json}")

    process_result = {}
    process_result["time"] = local_time
    process_result["hypermeter"] = hyperparameters
    process_result["result"] = sa_process_result.parameters 

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