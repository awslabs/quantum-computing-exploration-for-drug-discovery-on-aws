import argparse
import logging
from posixpath import basename
import boto3
import pickle
import botocore
import json
from utility.QMUQUBO import QMUQUBO
from utility.MoleculeParser import MoleculeData

logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                    datefmt='%Y-%m-%d:%H:%M:%S',
                    level=logging.INFO)


def prepare_molecule_data(mol_file: str):
    logging.info("prepare_molecule_data() enter")
    if mol_file:
        if mol_file.startswith("s3://"):
            b = mol_file.split("/")[2]
            k = "/".join(mol_file.split("/")[3:])
        else:
            b = s3_bucket
            k = mol_file

        logging.info(f"download mol_file from s3://{b}/{k}")
        mol_file_name = s3.download_file(b, k)

    else:
        mol_file_name = './molecule-data/Aspirin.mol2'

    mol_data = MoleculeData(mol_file_name, 'qmu')
    logging.info("build_input_data() done")
    return mol_data


def create_qubo_model(mol_data):
    logging.info("create_model() enter")
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

    method = 'pre-calc'
    model_param[method] = {}
    model_param[method]['M'] = range(1, num_rotation_bond+1)
    # model_param[method]['M'] = [4]
    model_param[method]['D'] = [4]
    model_param[method]['A'] = [300]
    model_param[method]['hubo_qubo_val'] = [200]

    qmu_qubo.build_model(**model_param)
    return qmu_qubo


def save_model(qmu_qubo, bucket, s3_prefix, version):
    if s3_prefix[-1] == '/':
        s3_prefix = s3_prefix[:-1]
    model_path = qmu_qubo.save(version)

    key = "{}/model/{}".format(s3_prefix, basename(model_path))
    s3.upload_file(model_path, bucket, key)
    logging.info("save_model() s3://{}/{}".format(bucket, key))
    info_key = "{}/executions/{}/model_info.txt".format(
        s3_prefix, execution_id)
    string_to_s3(content=str(key), bucket=bucket, key=info_key)


def string_to_s3(content, bucket, key):
    s3.put_object(
        Body=content.encode("utf-8"),
        Bucket=bucket,
        Key=key
    )
    logging.info("put file s3://{}/{}".format(bucket, key))


def read_user_input(execution_id, bucket, s3_prefix):
    key = f"{s3_prefix}/executions/{execution_id}/user_input.json"
    logging.info("read: s3://{}/{}".format(bucket, key))
    obj = s3.get_object(Bucket=bucket, Key=key)
    return json.loads(obj['Body'].read())


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--s3-bucket', type=str)
    parser.add_argument('--aws-region', type=str)
    parser.add_argument('--execution-id', type=str)

    args, _ = parser.parse_known_args()
    logging.info(args)

    aws_region = args.aws_region
    s3_bucket = args.s3_bucket
    execution_id = args.execution_id

    s3_prefix = "molecule-unfolding"
    boto3.setup_default_session(region_name=aws_region)
    s3 = boto3.client('s3')

    logging.info("s3_folder: s3://{}/{}".format(s3_bucket, s3_prefix))
    logging.info("execution_id: {}".format(execution_id))

    user_input = read_user_input(execution_id, s3_bucket, s3_prefix)

    logging.info(f"user_input:{user_input}")

    mol_file = user_input['user_input'].get("molFile", None)
    version = user_input['user_input'].get("modelVersion", 'latest')

    molecule_data = prepare_molecule_data(mol_file)
    qubo_model = create_qubo_model(molecule_data)
    save_model(qubo_model, s3_bucket, s3_prefix, version)
    logging.info("Done")
