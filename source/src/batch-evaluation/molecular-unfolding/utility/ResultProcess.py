# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

########################################################################################################################
#   The following class is for different kinds of annealing optimizer
########################################################################################################################
from pickletools import optimize  # nosec
import boto3
import json
import pickle  # nosec
import os
import datetime
import logging
import re

from .MolGeoCalc import update_pts_distance, get_same_direction_set, calc_distance_between_pts
from .MoleculeParser import MoleculeData

import py3Dmol
import time
from ipywidgets import interact, fixed, IntSlider
import ipywidgets

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
        self.data_path = param["data_path"]
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
        self.valid_var_angle = []
        self._parse_model_info()
        # initial parameter file
        self.parameters = {}
        self._init_parameters()

        # parameters
        self.physical_check = True
        if self.physical_check == True:
            self.non_contact_atom_map = self._init_non_contact_atom()

        # keep N recent results
        self.N = 100
        self.tried_combination = set()
        if self.method == "dwave-sa" or self.method == "neal-sa":
            logging.info("parse simulated annealer result")
            self.result = None
        elif self.method == "dwave-qa":
            logging.info("parse quantum annealer result")
            obj = self._read_result_obj(
                self.bucket, self.prefix, self.task_id, "results.json")
            self.result = json.loads(obj["Body"].read())

    def _init_non_contact_atom(self):
        mol_graph = self.mol_data.bond_graph.mol_ug

        non_contact_atom_map = {}

        for node_main in mol_graph.nodes:
            non_contact_atom = []
            for node_candidate in mol_graph.nodes:
                if node_candidate != node_main and node_candidate not in mol_graph.neighbors(node_main):
                    non_contact_atom.append(node_candidate)
            non_contact_atom_map[node_main] = non_contact_atom

        return non_contact_atom_map

    def _init_parameters(self):
        logging.info("_init_parameters")
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
        if self.method != "dwave-qa":
            logging.info(f"load simulated annealer {self.method} raw result")
            full_path = f"./{self.method}_result.pickle"
            with open(full_path, "rb") as f:
                self.raw_result = pickle.load(f)  # nosec
        elif self.method == "dwave-qa":
            logging.info("load quantum annealer raw result")
            obj = self._read_result_obj(
                self.bucket, self.prefix, self.task_id, "qa_result.pickle")  # nosec
            self.raw_result = pickle.loads(obj["Body"].read())  # nosec

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
                self.valid_var_angle.append(f'x_{var}_{d+1}')
            self.valid_var_name.append(f'{var}')
#         logging.info(f"valid var for this model is {self.valid_var_name}")

        return 0

    def generate_optimize_pts(self):
        logging.info("generate_optimize_pts()")
        # get best configuration
        pddf_sample_result = self.raw_result["response"].aggregate(
        ).to_pandas_dataframe()

        pddf_head_sample = pddf_sample_result.sort_values(
            by=['energy']).head(self.N)

        evaluate_loop_result = False
        max_optimize_gain = 1.0
        chosen_var = None
        actual_var = None
        max_tor_list = None
        max_ris = None
        max_volume = 0

        for index, row in pddf_head_sample.iterrows():
            generate_row = self._generate_row_data(row)

            max_optimize_gain = 1.0
            evaluate_loop_result = False
            for complete_tor_info in generate_row:
                logging.info(f"chosen var {complete_tor_info['chosen_var']}")
                logging.info(f"tor list {complete_tor_info['actual_var']}")
#                 logging.info(f"max_ris {complete_tor_info['max_ris']}")
#                 logging.info(f"max_tor_list {complete_tor_info['max_tor_list']}")
                if tuple(complete_tor_info['actual_var']) in self.tried_combination:
                    logging.info(f"pass current duplicate var")
                    continue
                else:
                    self.tried_combination.add(
                        tuple(complete_tor_info['actual_var']))
                optimize_gain, optimize_volume = self._evaluate_one_result(
                    complete_tor_info['tor_list'])
                if optimize_gain > max_optimize_gain:
                    # update final position for visualization
                    self._init_mol_file(self.atom_pos_data)
                    self._update_physical_position(
                        complete_tor_info['max_ris'], complete_tor_info['max_tor_list'])

                    physical_check_result = True
                    if self.physical_check == True:
                        logging.info(f"start physical check")

                        physical_check_result = self._physical_check_van_der_waals(
                            self.atom_pos_data)

                        if physical_check_result == False:
                            evaluate_loop_result = False
                            logging.info(f"physical check not pass!")
                        else:
                            evaluate_loop_result = True
                            max_optimize_gain = optimize_gain
                            max_volume = optimize_volume
                            chosen_var = complete_tor_info['chosen_var']
                            actual_var = complete_tor_info['actual_var']
                            max_tor_list = complete_tor_info['max_tor_list']
                            max_ris = complete_tor_info['max_ris']

            if evaluate_loop_result == True:
                break

        if evaluate_loop_result == False:
            logging.info(
                f"Fail to find optimized shape for {self.N} results, return to original one")
            self.parameters["volume"]["optimize"] = self.parameters["volume"]["initial"]
            self.parameters["volume"]["gain"] = 1.0
            initial_var = set()
            for var_name in self.valid_var_name:
                initial_var.add(f"X_{var_name}_1")
            self.parameters["volume"]["unfolding_results"] = list(initial_var)
            chosen_var = initial_var
        else:
            self.parameters["volume"]["optimize"] = max_volume
            self.parameters["volume"]["gain"] = max_optimize_gain
            # update optimized results
            self.parameters["volume"]["unfolding_results"] = list(actual_var)
            #         if True:

        self.parameters["volume"]["annealing_results"] = list(chosen_var)
        self.parameters["volume"]["optimize_info"] = {}
        self.parameters["volume"]["optimize_info"]["optimize_state"] = evaluate_loop_result
        self.parameters["volume"]["optimize_info"]["result_rank"] = index+1

    def _update_physical_position(self, max_ris, max_tor_list):
        #         temp for debugging
        #         max_ris = '4+5'
        #         self.M = '1'
        #         max_tor_list = ['x_3_8']
        #         max_ris = '4+5,2+4,1+2,10+11'
        #         self.M = '4'
        #         max_tor_list = ['x_3_3', 'x_2_1', 'x_1_1', 'x_4_1']
        #         max_ris = '4+5,2+4,1+2,10+11'
        #         self.M = '1'
        #         max_tor_list = ['x_3_3', 'x_1_1', 'x_2_1', 'x_4_1']
        rb_set = self.mol_data.bond_graph.sort_ris_data[str(
            self.M)][max_ris]
        for tor in max_tor_list:
            tor_map = {}
            base_rb_name = self.var_rb_map[tor.split('_')[1]]
            # get direction set
            tor_map[tor] = get_same_direction_set(
                rb_set['f_1_set'], self.mol_data.bond_graph.rb_data, base_rb_name)

            update_pts_distance(self.atom_pos_data, rb_set, tor_map,
                                self.var_rb_map, self.theta_option, True, False)

    def _generate_row_data(self, candidate_result):
        M = self.M
        D = self.D

        generate_row = []

        logging.debug("generate_optimize_pts model_info={}".format(
            self.raw_result["model_info"]))

        best_config = candidate_result.filter(items=self.valid_var_angle)

        chosen_var = set(best_config[best_config == 1].index.tolist())

        # change chose var to dict
        var_dict_list = []
        var_dict_raw = {}
        for valid_var in chosen_var:
            var_name = valid_var.split("_")[1]
            var_angle = valid_var.split("_")[2]
            if var_name not in var_dict_raw.keys():
                var_dict_raw[var_name] = []
                var_dict_raw[var_name].append(var_angle)
            else:
                var_dict_raw[var_name].append(var_angle)

        var_diff = M - len(var_dict_raw)

        var_diff_offset = 1
        max_generate = D

        if var_diff == 1:
            candi_angle = [str(d+1) for d in range(D)]
            for var_name in self.valid_var_name:
                if var_name not in var_dict_raw.keys():
                    var_dict_raw[var_name] = candi_angle
        elif var_diff > 1:
            for var_name in self.valid_var_name:
                if var_name not in var_dict_raw.keys():
                    var_dict_raw[var_name] = ['1']

        def _update_var_dict_list(var_dict, key_list):
            if len(var_dict_list) > max_generate:
                return
            key_value = str(key_list[0])
            for angle in var_dict_raw[key_value]:
                local_var_dict = var_dict.copy()
                local_var_dict[key_value] = str(angle)
                if len(key_list) == 1:
                    var_dict_list.append(local_var_dict)
                else:
                    _update_var_dict_list(local_var_dict, key_list[1:])

        key_list = list(var_dict_raw.keys())

        _update_var_dict_list({}, key_list)

        # use to generate final position
        logging.info(
            f"var_dict_raw {var_dict_raw} var_dict_list {var_dict_list}")

        for var_dict in var_dict_list:
            complete_tor_info = {}
            max_tor_list = []
            max_ris_num = 1
            max_ris = None
            actual_var = set()
            for var, angle in var_dict.items():
                actual_var.add(f"X_{var}_{angle}")
            complete_tor_list = []

            for ris in self.mol_data.bond_graph.sort_ris_data[str(M)].keys():
                # ris: '30+31', '29+30', '30+31,29+30'
                #             atom_pos_data_temp = self.atom_pos_data_raw.copy()
                logging.debug(f"ris group {ris} ")
                torsion_group = ris.split(",")
                # update points
                rb_set = self.mol_data.bond_graph.sort_ris_data[str(
                    self.M)][ris]

                tor_list = []
                for rb_name in torsion_group:
                    var_name = self.rb_var_map[rb_name]
                    var_angle = var_dict[var_name]

                    tor_list.append(f'X_{var_name}_{var_angle}')

                logging.debug(f"theta_option {self.theta_option}")
                logging.debug(f"rb_set {rb_set}")

                complete_tor_list.append((tor_list, rb_set))

                # update for final position
                current_ris_num = len(torsion_group)
                if current_ris_num >= max_ris_num:
                    max_ris_num = current_ris_num
                    max_ris = ris
                    max_tor_list = tor_list

            complete_tor_info['tor_list'] = complete_tor_list
            complete_tor_info['chosen_var'] = chosen_var
            complete_tor_info['actual_var'] = actual_var
            complete_tor_info['max_tor_list'] = max_tor_list
            complete_tor_info['max_ris'] = max_ris

            generate_row.append(complete_tor_info)

        return generate_row

    def _evaluate_one_result(self, complete_tor_list):

        optimize_volume = 0
        raw_volume = 0
        for tor in complete_tor_list:
            # build map for affected tor
            tor_list = tor[0]
            rb_set = tor[1]
#             print(f"tor list is {tor_list} and rb set is {rb_set}")
            tor_map = {}
            tor_len = len(tor_list)
            for base_idx in range(tor_len):
                tor_name = tor_list[base_idx]
                tor_map[tor_name] = set()
                base_rb_name = self.var_rb_map[tor_list[base_idx].split('_')[
                    1]]

                # get direction set
                direction_set = get_same_direction_set(
                    rb_set['f_1_set'], self.mol_data.bond_graph.rb_data, base_rb_name)

                for candi_idx in range(base_idx, tor_len):
                    candi_rb_name = self.var_rb_map[tor_list[candi_idx].split('_')[
                        1]].split('+')
                    for rb in candi_rb_name:
                        if rb in direction_set:
                            tor_map[tor_name].add(rb)

            logging.debug(f"tor_map {tor_map}")

            self._init_mol_file(self.atom_pos_data_temp)

            optimize_distance = update_pts_distance(
                self.atom_pos_data_temp, rb_set, tor_map, self.var_rb_map, self.theta_option, True, True)
            optimize_volume = optimize_volume + optimize_distance

            if self.parameters["volume"]["initial"] == 0:
                raw_distance = update_pts_distance(
                    self.atom_pos_data_raw, rb_set, None, None, None, False, True)
                raw_volume = raw_volume + raw_distance

        if self.parameters["volume"]["initial"] == 0:
            self.parameters["volume"]["initial"] = raw_volume

        optimize_gain = optimize_volume / \
            self.parameters["volume"]["initial"]

        logging.info(f"initial {self.parameters['volume']['initial']}")
        logging.info(f"optimize {optimize_volume}")
        logging.info(f"optimize_gain {optimize_gain}")

        return optimize_gain, optimize_volume

    def _physical_check_van_der_waals(self, atom_raw):
        check_result = True
        for atom_index, atom_info in atom_raw.items():
            vdw_radius = atom_info['vdw-radius']
            atom_pos = atom_info['pts']
            if check_result == False:
                break
            for non_contact_atom in self.non_contact_atom_map[atom_index]:
                non_contact_atom_pos = atom_raw[non_contact_atom]['pts']
                distance = calc_distance_between_pts(
                    [atom_pos], [non_contact_atom_pos])
#                 if non_contact_atom == '14' and atom_index == '1':
#                       logging.info(f"fail at {atom_index} to {non_contact_atom} for distance {distance}")
                if distance < vdw_radius:
                    logging.info(f"fail at {atom_index} to {non_contact_atom}")
                    check_result = False
                    break

        return check_result

    def save_mol_file(self, save_name):
        logging.info(f"save_mol_file {save_name}")
        raw_f = open(self.mol_file_name, "r")
        lines = raw_f.readlines()

        start_parse = 0

        def _update_atom_pos(line, atom_pos_data):
            atom_idx_name = re.findall(r"\d+ +[A-Za-z]+\d+", line)[0]
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

    def View3DMol(self, mol, size=(600, 600), style="stick", surface=False, opacity=0.5, type="mol2"):
        assert style in ('line', 'stick', 'sphere', 'carton')
        viewer = py3Dmol.view(width=size[0], height=size[1])
        viewer.addModel(open(mol, 'r').read(), type)
        viewer.setStyle({style: {}})
        if surface:
            viewer.addSurface(py3Dmol.SAS, {'opacity': opacity})
        viewer.zoomTo()
        return viewer

    def StyleSelector(self, mol, size, style):
        return self.View3DMol(mol, size=(size, size), style=style).show()

    def InteractView(self, mol, size):
        interact(self.StyleSelector,
                 mol=mol,
                 size=size,
                 style=ipywidgets.Dropdown(
                     options=['line', 'stick', 'sphere'],
                     value='stick',
                     description='Style:'))
