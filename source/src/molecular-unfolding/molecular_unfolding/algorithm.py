# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

########################################################################################################################
#   The following class is for different kinds of annealing optimizer
########################################################################################################################


import argparse
import logging
from os.path import basename
import boto3
import json

from utility.MoleculeParser import MoleculeData
from utility.QMUQUBO import QMUQUBO
from utility.AnnealerOptimizer import Annealer
from utility.ResultProcess import ResultParser

import time

logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                    datefmt='%Y-%m-%d:%H:%M:%S',
                    level=logging.INFO)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--s3-bucket', type=str)
    parser.add_argument('--aws-region', type=str)
    parser.add_argument('--execution-id', type=str)
    parser.add_argument('--s3_prefix', type=str)

    args, _ = parser.parse_known_args()
    logging.info(args)

    aws_region = args.aws_region
    s3_bucket = args.s3_bucket
    execution_id = args.execution_id
    s3_prefix = args.s3_prefix

    boto3.setup_default_session(region_name=aws_region)
    s3 = boto3.client('s3')

    logging.info("s3_folder: s3://{}/{}".format(s3_bucket, s3_prefix))
    logging.info("execution_id: {}".format(execution_id))

    user_input = read_context(execution_id, s3_bucket, s3_prefix)

    logging.info(f"user_input:{user_input}")

    mol_file = user_input['user_input'].get("molFile", None)
    version = user_input['user_input'].get("modelVersion", 'latest')
    

    logging.info(f"create model, modelVersion:{version}")

    modelParams = user_input['user_input']["modelParams"]

    logging.info(f"modelParams={modelParams}")

    molecule_data, raw_s3_path, data_s3_path = prepare_molecule_data(
        mol_file, execution_id, version)

    qubo_model, model_s3_path = create_qubo_model(molecule_data, execution_id, version, modelParams)
   
    record_execution_model_info(
        execution_id, raw_s3_path, data_s3_path, model_s3_path)

    logging.info("Done")
