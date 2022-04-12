# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import argparse
import logging
from os.path import basename
import boto3
import json
from utility.QMUQUBO import QMUQUBO
from utility.MoleculeParser import MoleculeData


logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                    datefmt='%Y-%m-%d:%H:%M:%S',
                    level=logging.INFO)


def download_file(bucket, key, dir="/tmp/"): #nosec
    file_name = dir + key.split("/")[-1]

    with open(file_name, 'wb') as f:
        s3.download_fileobj(bucket, key, f)
    print("download_file: {} -> {}".format(key, file_name))
    return file_name


def prepare_molecule_data(mol_file: str, execution_id, version):
    logging.info("prepare_molecule_data() enter")
    if mol_file:
        if mol_file.startswith("s3://"):
            b = mol_file.split("/")[2]
            k = "/".join(mol_file.split("/")[3:])
        else:
            b = s3_bucket
            k = mol_file

        logging.info(f"download mol_file from s3://{b}/{k}")
        mol_file_name = download_file(b, k)
        raw_model_s3_path = f"s3://{b}/{k}"

    else:
        mol_file_name = './molecule-data/117_ideal.mol2'
        mol2_name = basename(mol_file_name)
        raw_model_s3_path = upload_file(bucket=s3_bucket, key=f"{s3_prefix}/executions/{execution_id}/models/raw/{mol2_name}",
                                        file_name=mol_file_name)

    logging.info(f"mol_file_name: {mol_file_name}")
    mol_data = MoleculeData(mol_file_name, 'qmu')
    logging.info(
        f"build_input_data() done, raw_model_s3_path: {raw_model_s3_path}")

    data_file_s3_path = save_model_data(execution_id, mol_data, s3_bucket, s3_prefix, 'data', version)    
    return mol_data, raw_model_s3_path, data_file_s3_path


def upload_file(bucket, key, file_name):
    s3.upload_file(file_name, bucket, key)
    logging.info(f"upload_file {file_name} -> s3://{bucket}/{key}")
    return f"s3://{bucket}/{key}"


def create_qubo_model(mol_data, execution_id, version, model_params):
    logging.info("create_model() enter")
    
    max_param_M = max(model_params.get('M', [5]))
    param_D = model_params.get('D', [8])
    param_A = model_params.get('A', [300])
    param_HQ = model_params.get('HQ', [200])

    print(f"max_param_M={max_param_M}")

    init_param = {}
    method = ['pre-calc']

    for mt in method:
        if mt == 'pre-calc':
            init_param[mt] = {}
            init_param[mt]['param'] = ['M', 'D', 'A', 'hubo_qubo_val']

    qmu_qubo = QMUQUBO(mol_data, method, **init_param)

    model_param = {}
    # parameters
    num_rotation_bond = mol_data.bond_graph.rb_num

    print(f"num_rotation_bond: {num_rotation_bond}")

    method = 'pre-calc'
    model_param[method] = {}
    model_param[method]['M'] = range(1, min(num_rotation_bond+1, max_param_M + 1))
    # model_param[method]['M'] = [4]
    model_param[method]['D'] = param_D
    model_param[method]['A'] = param_A
    model_param[method]['hubo_qubo_val'] = param_HQ

    qmu_qubo.build_model(**model_param)

    model_file_s3_path = save_model_data(execution_id, qmu_qubo, s3_bucket, s3_prefix, 'model', version)   
    return qmu_qubo, model_file_s3_path


def save_model_data(execution_id, saveable, bucket, s3_prefix, category, version):
    if s3_prefix[-1] == '/':
        s3_prefix = s3_prefix[:-1]
    model_path = saveable.save(version)

    key = "{}/executions/{}/models/{}/{}".format(s3_prefix, execution_id, category, basename(model_path))
    s3.upload_file(model_path, bucket, key)
    s3_path = "s3://{}/{}".format(bucket, key)
    logging.info("save_model_data() {}".format(s3_path))
    return s3_path


def record_execution_model_info(execution_id, raw_s3_path, data_s3_path, model_s3_path):
    info_key = "{}/executions/{}/model_info.json".format(
        s3_prefix, execution_id)

    string_to_s3(content=json.dumps({
        "model": str(model_s3_path),
        "data": str(data_s3_path),
        "raw": str(raw_s3_path),
    }), bucket=s3_bucket, key=info_key)


def string_to_s3(content, bucket, key):
    s3.put_object(
        Body=content.encode("utf-8"),
        Bucket=bucket,
        Key=key
    )
    logging.info("put file s3://{}/{}".format(bucket, key))


def read_context(execution_id, bucket, s3_prefix):
    key = f"{s3_prefix}/executions/{execution_id}/user_input.json"
    logging.info("read: s3://{}/{}".format(bucket, key))
    obj = s3.get_object(Bucket=bucket, Key=key)
    context = json.loads(obj['Body'].read())
    logging.info(f"context={context}")
    return context


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
