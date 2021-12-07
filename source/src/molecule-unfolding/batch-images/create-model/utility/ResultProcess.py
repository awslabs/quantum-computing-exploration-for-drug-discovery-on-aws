########################################################################################################################
#   The following class is for different kinds of annealing optimizer
########################################################################################################################
import boto3
import json
import pickle
import os
import datetime
import logging
import re

from .MolGeoCalc import atom_distance_func, update_pts
from .MolGeoCalc import mol_distance_func
from .MoleculeParser import MoleculeData

s3_client = boto3.client("s3")


class ResultParser():
    def __init__(self, method, **param):
        self.agg_response = None
        self.method = method
        self.set = set()
        # raw_result, load from pickle file, maintain by dwave
        self.raw_result = None
        if self.method == "dwave-qa":
            self.bucket = param["bucket"]
            self.prefix = param["prefix"]
            self.task_id = param["task_id"]
        self._load_raw_result()
        # result: get by task_id, maintain by braket api
        self.result = None
        # initial mol file
        self.atom_pos_data = {}
        self.mol_file_name = param["raw_path"]
        self.mol_data = MoleculeData.load(param["data_path"])
        self._init_mol_file()
        # parse model_info
        self.rb_var_map = None
        self.var_rb_map = None
        self.M = None
        self.D = None
        self.theta_option = None
        self.valid_var_name = []
        self._parse_model_info()
        # initial parameter file
        self.parameters = {}
        self._init_parameters()

        if self.method == "dwave-sa":
            logging.info("parse simulated annealer result")
            self.result = None
        elif self.method == "dwave-qa":
            logging.info("parse quantum annealer result")
            obj = self._read_result_obj(
                self.bucket, self.prefix, self.task_id, "results.json")
            self.result = json.loads(obj["Body"].read())

    def _init_parameters(self):
        van_der_waals_check = 'initial'
        self.parameters["volume"] = {}
        self.parameters["volume"]["initial"], _, self.set = mol_distance_func(
            self.atom_pos_data, van_der_waals_check, self.set)

    def _init_mol_file(self):
        for pt, info in self.mol_data.atom_data.items():
            self.atom_pos_data[pt] = {}
            self.atom_pos_data[pt]['pts'] = [info['x'], info['y'], info['z']]
            self.atom_pos_data[pt]['idx'] = ([0, 0, 0], [0, 0, 0])
            self.atom_pos_data[pt]['vdw-radius'] = info['vdw-radius']

    def _read_result_obj(self, bucket, prefix, task_id, file_name):
        key = f"{prefix}/{task_id}/{file_name}"
        obj = s3_client.get_object(Bucket=bucket, Key=key)
        return obj

    def _load_raw_result(self):
        if self.method == "dwave-sa":
            logging.info("load simulated annealer raw result")
            full_path = "./sa_result.pickle"
            with open(full_path, "rb") as f:
                self.raw_result = pickle.load(f)
        elif self.method == "dwave-qa":
            logging.info("load quantum annealer raw result")
            obj = self._read_result_obj(
                self.bucket, self.prefix, self.task_id, "qa_result.pickle")
            self.raw_result = pickle.loads(obj["Body"].read())

    def get_all_result(self):
        return self.raw_result, self.result

    def get_time(self):
        if self.method == "dwave-qa":
            local_time = self.raw_result["time"]
            # task_time
            date_time_str = self.result["taskMetadata"]["createdAt"]
            start = datetime.datetime.strptime(
                date_time_str, "%Y-%m-%dT%H:%M:%S.%fZ")
            date_time_str = self.result["taskMetadata"]["endedAt"]
            end = datetime.datetime.strptime(
                date_time_str, "%Y-%m-%dT%H:%M:%S.%fZ")
            task_time = (end-start).total_seconds()
            # reference https://docs.dwavesys.com/docs/latest/c_qpu_timing.html
            # qa_total_time = qpu_program_time + sampling_time + qpu_access_overhead_time + total_post_processing_time
            qpu_programming_overtime = self.result["additionalMetadata"][
                "dwaveMetadata"]["timing"]["qpuProgrammingTime"]
            qpu_sampling_time = self.result["additionalMetadata"]["dwaveMetadata"]["timing"]["qpuSamplingTime"]
            qpu_access_overhead_time = self.result["additionalMetadata"][
                "dwaveMetadata"]["timing"]["qpuAccessOverheadTime"]
            total_post_processing_time = self.result["additionalMetadata"][
                "dwaveMetadata"]["timing"]["totalPostProcessingTime"]
            qa_total_time = qpu_programming_overtime + qpu_sampling_time + \
                qpu_access_overhead_time + total_post_processing_time
            qa_total_time = qa_total_time/1000.0
            qa_total_time = qa_total_time/1000.0
            qa_access_time = self.result["additionalMetadata"]["dwaveMetadata"]["timing"]["qpuAccessTime"]/1000.0
            qa_access_time = qa_access_time/1000.0
            return local_time, task_time, qa_total_time, qa_access_time
        else:
            local_time = self.raw_result["time"]
            logging.info("sa only has local_time!")
            return local_time, None, None, None

    def _parse_model_info(self):
        self.rb_var_map = self.raw_result["model_info"]["rb_var_map"]
        self.var_rb_map = self.raw_result["model_info"]["var_rb_map"]

        # parse D from model_name
        model_name = self.raw_result["model_info"]["model_name"]
        self.M = int(model_name.split("_")[0])
        self.D = int(model_name.split("_")[1])
        self.theta_option = [x * 360/self.D for x in range(self.D)]

        for rb in self.raw_result["model_info"]["rb_name"]:
            var = self.rb_var_map[rb]
            for d in range(self.D):
                self.valid_var_name.append(f'x_{var}_{d+1}')
        logging.info(f"valid var for this model is {self.valid_var_name}")

        return 0

    def generate_optimize_pts(self):
        # get best configuration
        pddf_sample_result = self.raw_result["response"].aggregate(
        ).to_pandas_dataframe()

        pddf_best_result = pddf_sample_result.iloc[pddf_sample_result['energy'].idxmin(
        ), :]

        logging.debug(self.raw_result["model_info"])

        logging.debug(self.raw_result["response"].variables)

        best_config = pddf_best_result.filter(items=self.valid_var_name)

        def _gen_pts_list(pt_set, atom_pos_data):
            return [atom_pos_data[pt] for pt in pt_set]

        chosen_var = best_config[best_config == 1].index.tolist()
        for valid_var in chosen_var:
            var = valid_var.split("_")[1]
            d = valid_var.split("_")[2]
            rb_name = self.var_rb_map[var]
            rb_set = self.mol_data.bond_graph.sort_ris_data[str(
                self.M)][rb_name]
            print(valid_var)
            start_pts = self.atom_pos_data[rb_name.split('+')[0]]
            end_pts = self.atom_pos_data[rb_name.split('+')[1]]
            rotate_list = update_pts([start_pts], [end_pts], _gen_pts_list(
                rb_set['f_1_set'], self.atom_pos_data), self.theta_option[int(d)-1])
            for pt_name, pt_value in zip(rb_set['f_1_set'], rotate_list):
                self.atom_pos_data[pt_name]['pts'] = pt_value

        logging.info(f"finish update optimize points for {chosen_var}")

        # update mol distance metrics
        van_der_waals_check = 'test'
        self.parameters["volume"]["optimize"], _, _ = mol_distance_func(
            self.atom_pos_data, van_der_waals_check, self.set)
        # update relative improvement
        self.parameters["volume"]["gain"] = self.parameters["volume"]["optimize"] / \
            self.parameters["volume"]["initial"]

        return 0

    def save_mol_file(self, save_name):
        raw_f = open(self.mol_file_name, "r")
        lines = raw_f.readlines()

        start_parse = 0

        def _update_atom_pos(line, atom_pos_data):
            atom_idx_name = re.findall(r"\d+ [A-Z]\d+", line)[0]
            logging.debug("atom id name is {}".format(atom_idx_name))
            atom_idx = atom_idx_name.split(' ')[0]

            regrex = re.compile(
                r"[-+]?\d+\.\d+ +[-+]?\d+\.\d+ +[-+]?\d+\.\d+", re.IGNORECASE)

            update_pos_x = atom_pos_data[atom_idx]['pts'][0]
            update_pos_y = atom_pos_data[atom_idx]['pts'][1]
            update_pos_z = atom_pos_data[atom_idx]['pts'][2]

            update_pos = "{}    {}    {}".format(
                update_pos_x, update_pos_y, update_pos_z)

            update_line = regrex.sub(update_pos, line)

            return update_line

        mol_save_name = f"{self.mol_file_name.split('mol2')[0][:-1]}_{self.method}_{save_name}.mol2"
        file_save_name = f"{self.mol_file_name.split('mol2')[0][:-1]}_{self.method}_{save_name}.json"

        update_f = open(mol_save_name, 'w')

        for line in lines:
            logging.debug(line)

            if line.startswith("@<TRIPOS>BOND"):
                logging.debug("finish atom part")
                start_parse = 0

            if start_parse == 1:
                update_line = _update_atom_pos(line, self.atom_pos_data)
                update_f.write(update_line)
            else:
                update_f.write(line)

            if line.startswith("@<TRIPOS>ATOM"):
                logging.debug("found atom start position")
                start_parse = 1

        raw_f.close()
        update_f.close()

        # update_parameters
        with open(file_save_name, "w") as outfile:
            json.dump(self.parameters, outfile)

        logging.info(f"finish save {mol_save_name} and {file_save_name}")

        return 0
