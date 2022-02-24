########################################################################################################################
#   The following class is for different kinds of annealing optimizer
########################################################################################################################
from pickletools import optimize #nosec
import boto3
import json
import pickle #nosec
import os
import datetime
import logging
import re

from .MolGeoCalc import update_pts_distance
from .MoleculeParser import MoleculeData

s3_client = boto3.client("s3")

log = logging.getLogger()
log.setLevel('INFO')


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
        self.atom_pos_data_raw = {}
        self.atom_pos_data_temp = {}
        self.mol_file_name = param["raw_path"]
        logging.info("MoleculeData.load()")
        self.mol_data = MoleculeData.load(param["data_path"])
        logging.info("init mol data for final position")
        self._init_mol_file(self.atom_pos_data)
        logging.info("init mol data for raw position")
        self._init_mol_file(self.atom_pos_data_raw)
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
        logging.info("_init_parameters")
        # TODO: leave for future post process
        # van_der_waals_check = 'initial'
        # self.parameters["volume"] = {}
        # self.parameters["volume"]["initial"], _, self.set = mol_distance_func(
        #     self.atom_pos_data, van_der_waals_check, self.set)
        self.parameters["volume"] = {}
        self.parameters["volume"]["optimize"] = 0
        self.parameters["volume"]["initial"] = 0

    def _init_mol_file(self, pos_data):
        for pt, info in self.mol_data.atom_data.items():
            pos_data[pt] = {}
            pos_data[pt]['pts'] = [info['x'], info['y'], info['z']]
            pos_data[pt]['idx'] = ([0, 0, 0], [0, 0, 0])
            pos_data[pt]['vdw-radius'] = info['vdw-radius']

    def _init_temp_mol_file(self):
        logging.info("_init_mol_file")
        for pt, info in self.mol_data.atom_data.items():
            self.atom_pos_data_temp[pt] = {}
            self.atom_pos_data_temp[pt]['pts'] = [
                info['x'], info['y'], info['z']]
            self.atom_pos_data_temp[pt]['idx'] = ([0, 0, 0], [0, 0, 0])
            self.atom_pos_data_temp[pt]['vdw-radius'] = info['vdw-radius']

    def _read_result_obj(self, bucket, prefix, task_id, file_name):
        logging.info("_read_result_obj")
        key = f"{prefix}/{task_id}/{file_name}"
        logging.info(f"_read_result_obj: {key}")
        obj = s3_client.get_object(Bucket=bucket, Key=key)
        return obj

    def _load_raw_result(self):
        logging.info("_load_raw_result")
        if self.method == "dwave-sa":
            logging.info("load simulated annealer raw result")
            full_path = "./sa_result.pickle"
            with open(full_path, "rb") as f:
                self.raw_result = pickle.load(f) #nosec
        elif self.method == "dwave-qa":
            logging.info("load quantum annealer raw result")
            obj = self._read_result_obj(
                self.bucket, self.prefix, self.task_id, "qa_result.pickle") #nosec
            self.raw_result = pickle.loads(obj["Body"].read()) #nosec

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
        logging.info("_parse_model_info")
#         logging.info("_parse_model_info() model_info = {}".format(self.raw_result["model_info"]))

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
#         logging.info(f"valid var for this model is {self.valid_var_name}")

        return 0

    def generate_optimize_pts(self):
        logging.info("generate_optimize_pts()")
        # get best configuration
        pddf_sample_result = self.raw_result["response"].aggregate(
        ).to_pandas_dataframe()

        pddf_best_result = pddf_sample_result.iloc[pddf_sample_result['energy'].idxmin(
        ), :]

        logging.debug("generate_optimize_pts model_info={}".format(
            self.raw_result["model_info"]))

        best_config = pddf_best_result.filter(items=self.valid_var_name)

        chosen_var = set(best_config[best_config == 1].index.tolist())
        initial_var = set()

        # change chose var to dict
        var_dict = {}
        for valid_var in chosen_var:
            var_name = valid_var.split("_")[1]
            var_angle = valid_var.split("_")[2]
            var_dict[var_name] = var_angle
            initial_name = f"X_{var_name}_1"
            initial_var.add(initial_name)

        logging.debug(f"var_dict is {var_dict}")

        # calculate optimized position
        f_distances_raw = {}
        f_distances_optimize = {}

        missing_var = set()

        for ris in self.mol_data.bond_graph.sort_ris_data[str(self.M)].keys():
            # ris: '30+31', '29+30', '30+31,29+30'
            #             atom_pos_data_temp = self.atom_pos_data_raw.copy()
            self._init_mol_file(self.atom_pos_data_temp)
            logging.debug(f"ris group {ris} ")
            torsion_group = ris.split(",")
            # update points
            rb_set = self.mol_data.bond_graph.sort_ris_data[str(
                self.M)][ris]

            tor_list = []
            for rb_name in torsion_group:
                var_name = self.rb_var_map[rb_name]
                var_angle = 1
                if var_name in var_dict.keys():
                    var_angle = var_dict[var_name]
                else:
                    logging.info(f"missing result for {var_name}")
                    missing_var.add(f"X_{var_name}_1")
                    initial_var.add(f"X_{var_name}_1")
                    chosen_var.add(f"X_{var_name}_1")

                tor_list.append(f'X_{var_name}_{var_angle}')

            logging.debug(f"theta_option {self.theta_option}")
            logging.debug(f"rb_set {rb_set}")

            optimize_distance = update_pts_distance(
                self.atom_pos_data_temp, rb_set, tor_list, self.var_rb_map, self.theta_option, True, True)
            raw_distance = update_pts_distance(
                self.atom_pos_data_raw, rb_set, None, None, None, False, True)

            update_pts_distance(self.atom_pos_data, rb_set, tor_list,
                                self.var_rb_map, self.theta_option, True, False)

            f_distances_optimize[tuple(ris)] = optimize_distance
            f_distances_raw[tuple(ris)] = raw_distance
            self.parameters["volume"]["optimize"] = self.parameters["volume"]["optimize"] + \
                optimize_distance
            self.parameters["volume"]["initial"] = self.parameters["volume"]["initial"] + raw_distance
        logging.debug(f"finish update optimize points for {chosen_var}")
        logging.debug(f_distances_optimize)
        logging.debug(f_distances_raw)

        # update mol distance metrics
        # van_der_waals_check = 'test'
        # self.parameters["volume"]["optimize"], _, _ = mol_distance_func(
        #     self.atom_pos_data, van_der_waals_check, self.set)
        # update relative improvement
        optimize_gain = self.parameters["volume"]["optimize"] / \
            self.parameters["volume"]["initial"]

        optimize_state = False
        if optimize_gain < 1.0:
            logging.info("Fail to find optimized shape, return to original one")
            self.parameters["volume"]["optimize"] = self.parameters["volume"]["initial"]
            self.parameters["volume"]["gain"] = 1.0
            self.parameters["volume"]["unfolding_results"] = list(initial_var)
            optimize_state = False
        else:
            self.parameters["volume"]["gain"] = optimize_gain
            # update optimized results
            self.parameters["volume"]["unfolding_results"] = list(chosen_var)
            optimize_state = True
        
        self.parameters["volume"]["optimize_info"] = {}
        self.parameters["volume"]["optimize_info"]["missing_var"] = list(missing_var)
        self.parameters["volume"]["optimize_info"]["optimize_state"] = optimize_state

        return 0

    def save_mol_file(self, save_name):
        logging.info(f"save_mol_file {save_name}")
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

        return [mol_save_name, file_save_name]
