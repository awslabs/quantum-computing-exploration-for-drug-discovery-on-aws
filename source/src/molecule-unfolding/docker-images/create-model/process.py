import argparse
import logging
import boto3
import pickle
import botocore
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

    model_file = "./qubo.pickle"
    with open(model_file, 'bw') as outfile:
        pickle.dump(model_data, outfile)

    param_file = "./qubo_param.json"
    with open(param_file, 'w') as outfile:
        json.dump(model_param, outfile)

    key = "{}/model/m{}/qubo.pickle".format(s3_prefix, m)
    s3.upload_file(model_file, bucket, key)
    logging.info("save_model_data() s3://{}/{}".format(bucket, key))

    key = "{}/model/m{}/param.json".format(s3_prefix, m)
    s3.upload_file(param_file, bucket, key)
    logging.info("save_model_data() s3://{}/{}".format(bucket, key))


def is_model_exist(bucket, s3_prefix, m):
    try:
        s3.head_object(Bucket=bucket, Key=f'{s3_prefix}/{m}/qubo.pickle')
        return True
    except botocore.exceptions.ClientError:
        return False


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--s3-bucket', type=str)
    parser.add_argument('--aws-region', type=str, default=DEFAULT_AWS_REGION)
    parser.add_argument('--force-update', type=int, default=1)
    args, _ = parser.parse_known_args()

    aws_region = args.aws_region
    s3_bucket = args.s3_bucket
    force_update = args.force_update

    s3_prefix = "molecule-unfolding"
    boto3.setup_default_session(region_name=aws_region)
    s3 = boto3.client('s3')

    logging.info("s3_folder: s3://{}/{}".format(s3_bucket, s3_prefix))

    input_data = build_input_data()
    max_m = input_data.bond_graph.rb_num
    logging.info("max_m={}".format(max_m))

    for m in range(1, max_m+1):
        if force_update or not is_model_exist(s3_bucket, s3_prefix, m):
            qmu_qubo_model, model_param = create_model(input_data, m)
            save_model_data(qmu_qubo_model.qubo, model_param,
                            s3_bucket, s3_prefix, m)
        else:
            logging.info(f"model file for M: {m} already exist, skip ...")

    logging.info("Done")
