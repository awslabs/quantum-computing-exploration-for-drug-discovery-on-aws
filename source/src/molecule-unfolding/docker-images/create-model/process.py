import argparse
import logging
import boto3
import time
import json
from utility.QMUQUBO import QMUQUBO
from utility.MoleculeParser import MoleculeData

logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                    datefmt='%Y-%m-%d:%H:%M:%S',
                    level=logging.INFO)

DEFAULT_M = 4
DEFAULT_D = 4
DEFAULT_AWS_REGION = 'us-east-1'


def build_input_data():
    logging.info("build_input_data() enter")
    mol_file_name = './molecule-data/Aspirin.mol2'
    mol_data = MoleculeData(mol_file_name, 'qmu')
    logging.info("build_input_data() done")
    return mol_data


def create_model(mol_data, m):
    logging.info("create_model() enter, m={}".format(m))
    model_param = {}
    method = 'pre-calc'
    if method == 'pre-calc':
        model_param['M'] = m  # mol_data.bond_graph.rb_num
        model_param['D'] = 4
        model_param['A'] = 300
        model_param['hubo_qubo_val'] = 200
    qmu_qubo = QMUQUBO(mol_data, method, **model_param)
    logging.info("create_model() done, m={}".format(m))
    return qmu_qubo, model_param


def save_model_data(model_data, model_param, bucket, s3_prefix, m):
    if s3_prefix[-1] == '/':
        s3_prefix = s3_prefix[:-1]

    s3 = boto3.client('s3')

    model_file = "./qubo.json"
    with open(model_file, 'w') as outfile:
        json.dump(model_data, outfile)

    param_file = "./qubo_param.json"
    with open(param_file, 'w') as outfile:
        json.dump(model_param, outfile)

    key = "{}/model/m{}/qubo.json".format(s3_prefix, m)
    s3.upload_file(model_file, bucket, key)
    logging.info("save_model_data() s3://{}/{}".format(bucket, key))

    key = "{}/model/m{}/param.json".format(s3_prefix, m)
    s3.upload_file(param_file, bucket, key)
    logging.info("save_model_data() s3://{}/{}".format(bucket, key))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--s3-bucket', type=str)
    parser.add_argument('--aws-region', type=str, default=DEFAULT_AWS_REGION)
    args, _ = parser.parse_known_args()

    aws_region = args.aws_region
    s3_bucket = args.s3_bucket

    s3_prefix = "molecule-unfolding"
    boto3.setup_default_session(region_name=aws_region)

    logging.info("s3_folder: s3://{}/{}".format(s3_bucket, s3_prefix))

    input_data = build_input_data()
    max_m = input_data.bond_graph.rb_num

    for m in range(1, max_m+1):
       qmu_qubo_model, model_param = create_model(input_data, m)
       save_model_data(qmu_qubo_model.qubo, model_param, s3_bucket, s3_prefix, m)

    logging.info("Done")
