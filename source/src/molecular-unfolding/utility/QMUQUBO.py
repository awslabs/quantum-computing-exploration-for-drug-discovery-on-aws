# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

########################################################################################################################
#   The following class is the construction of QUBO model
########################################################################################################################
import dimod
from .MolGeoCalc import update_pts_distance, get_same_direction_set, rot_mat_value

from pyqubo import Array
from pyqubo import Num
from pyqubo import Binary

import math

from collections import defaultdict
import time
import logging
import pickle  # nosec
import os

# log = logging.getLogger()
# log.setLevel('INFO')
logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

class QMUQUBO():

    def __init__(self, mol_data, method, **param):

        # prepare parameters
        self.param = param

        self.mol_data = mol_data

        self.name = f"qmu_{self.mol_data.name}_model"

        # init model_info to store the information for model of different methods
        # init model_qubo to store the qubo for model of different methods
        self.model_info = {}
        self.model_qubo = {}
        self.atom_pos_data = {}
        # define vars/var_rb_map/rb_var_map for different models
        self.var = None
        self.var_rb_map = None
        self.rb_var_map = None

        for mt in method:
            self.model_info[f"{mt}"] = {}
            self.model_qubo[f"{mt}"] = {}

            if mt == "pre-calc":
                logging.info(
                    "initial pre-calculate for constructing molecule QUBO")
                for param in self.param[mt]["param"]:
                    self.model_info[mt][param] = set()
            elif mt == "symbolic":
                logging.info(
                    "initial symbolic calculate for constructing molecule QUBO")
                for param in self.param[mt]["param"]:
                    self.model_info[mt][param] = set()
            else:
                logging.info(f"only pre-calculate(method='pre-calc') and symbolic-calculate(method='symbolic') are supported, \
                method {mt} not support !!")

    def build_model(self, **param):
        for method, config in param.items():
            model_param = config
            if method == "pre-calc":
                self._build_pre_calc_model(**model_param)
            elif method == "symbolic":
                self._build_symbolic_model(**model_param)
        return 0

    def _build_symbolic_model(self, **model_param):
        for M in model_param["M"]:
            for D in model_param["D"]:
                for A in model_param["A"]:
                    for strength in model_param["strength"]:
                        # update var_map
                        # prepare variables
                        self.var, self.var_rb_map, self.rb_var_map = self._prepare_var(
                            self.mol_data, D, "symbolic")
                        model_name = f"{M}_{D}_{A}_{strength}"
                        # check availability
                        if model_name in self.model_qubo["symbolic"].keys():
                            logging.info(
                                f"duplicate model !! pass !! M:{M},D:{D},A:{A},strength {strength}")
                            continue
                        else:
                            self._update_model_info([M, D, A, strength], [
                                                    "M", "D", "A", "strength"], "symbolic")
                        start = time.time()
                        logging.info("debug for symbolic 1")
                        hubo_constraints, hubo_distances = self._build_qubo_symbolic(self.mol_data, M, D, A, self.var,
                                                                                     self.rb_var_map)
                        logging.info("debug for symbolic 2")

                        hubo_model = hubo_distances + hubo_constraints

                        model = None
                        if strength == -1:
                            model = hubo_model.compile()
                        else:
                            model = hubo_model.compile(strength)
                        logging.info("debug for symbolic 3")
                        
                        qubo = model.to_bqm()
                        end = time.time()
                        logging.info("debug for symbolic 4")

                        self.model_qubo["symbolic"][model_name] = {}
                        self.model_qubo["symbolic"][model_name]["qubo"] = qubo
                        self.model_qubo["symbolic"][model_name]["var"] = self.var
                        self.model_qubo["symbolic"][model_name]["var_rb_map"] = self.var_rb_map
                        self.model_qubo["symbolic"][model_name]["rb_var_map"] = self.rb_var_map
                        self.model_qubo["symbolic"][model_name]["time"] = end-start
                        self.model_qubo["symbolic"][model_name]["model_name"] = model_name
                        ris_name = list(
                            self.mol_data.bond_graph.sort_ris_data[str(M)].keys()).copy()
                        logging.info("debug for symbolic 5")
                        valid_rb_name = []
                        for name in ris_name:
                            if len(name.split(',')) == 1:
                                valid_rb_name.append(name)
                        self.model_qubo["symbolic"][model_name]["rb_name"] = valid_rb_name
                        logging.info("debug for symbolic 6")

                        logging.info(
                            f"Construct model for M:{M},D:{D},A:{A},strength:{strength} {(end-start)/60} min")

    def _build_pre_calc_model(self, **model_param):
        for M in model_param["M"]:
            for D in model_param["D"]:
                for A in model_param["A"]:
                    for hubo_qubo_val in model_param["hubo_qubo_val"]:
                        # update var_map
                        # prepare variables
                        self.var, self.var_rb_map, self.rb_var_map = self._prepare_var(
                            self.mol_data, D)
                        model_name = f"{M}_{D}_{A}_{hubo_qubo_val}"
                        # check availability
                        if model_name in self.model_qubo["pre-calc"].keys():
                            logging.info(
                                f"duplicate model !! pass !! M:{M},D:{D},A:{A},hubo_qubo_val {hubo_qubo_val}")
                            continue
                        else:
                            self._update_model_info([M, D, A, hubo_qubo_val], [
                                                    "M", "D", "A", "hubo_qubo_val"], "pre-calc")
                        start = time.time()
                        hubo = {}
                        theta_option = [x * 360/D for x in range(D)]
                        logging.info("debug for pre-calc 1")
                        hubo_constraints, hubo_distances = self._build_qubo_pre_calc(self.mol_data, M, D, A, self.var,
                                                                                     self.rb_var_map, self.var_rb_map,
                                                                                     theta_option)
                        logging.info("debug for pre-calc 2")
                        hubo.update(hubo_constraints)
                        hubo.update(hubo_distances)
                        # transfer hubo to qubo
                        # TODO why make_quadratic not work?
                        # qubo_raw = dimod.make_quadratic(
                        #     hubo, hubo_qubo_val, dimod.BINARY).to_qubo()
                        qubo_raw = dimod.make_quadratic(
                            hubo, hubo_qubo_val, dimod.BINARY)
                        logging.info("debug for pre-calc 3")
                        qubo = self._manual_qubo(qubo_raw.to_qubo())
                        logging.info("debug for pre-calc 4")
                        end = time.time()

                        self.model_qubo["pre-calc"][model_name] = {}
                        self.model_qubo["pre-calc"][model_name]["qubo"] = qubo
                        self.model_qubo["pre-calc"][model_name]["var"] = self.var
                        self.model_qubo["pre-calc"][model_name]["var_rb_map"] = self.var_rb_map
                        self.model_qubo["pre-calc"][model_name]["rb_var_map"] = self.rb_var_map
                        self.model_qubo["pre-calc"][model_name]["time"] = end-start
                        self.model_qubo["pre-calc"][model_name]["model_name"] = model_name
                        ris_name = list(
                            self.mol_data.bond_graph.sort_ris_data[str(M)].keys()).copy()
                        logging.info("debug for pre-calc 5")
                        valid_rb_name = []
                        for name in ris_name:
                            if len(name.split(',')) == 1:
                                valid_rb_name.append(name)
                        logging.info("debug for pre-calc 6")
                        self.model_qubo["pre-calc"][model_name]["rb_name"] = valid_rb_name
                        # # optimize results
                        # self.model_qubo["pre-calc"][model_name]["optimizer"] = {}
                        # self.model_qubo["pre-calc"][model_name]["optimizer"]["post"] = {}

                        logging.info(
                            f"Construct model for M:{M},D:{D},A:{A},hubo_qubo_val:{hubo_qubo_val} {(end-start)/60} min")

    def _manual_qubo(self, qubo_raw):
        qubo = defaultdict(float)

        for key, value in qubo_raw[0].items():
            qubo[key] = value

        return qubo

    def _update_model_info(self, values, names, method):
        for value, name in zip(values, names):
            self.model_info[method][name].add(value)

    def clear_model(self, method):
        for mt in method:
            self.model_info[f"{mt}"] = {}
            self.model_qubo[f"{mt}"] = {}

        return 0

    def describe_model(self):

        # information for model
        for method, info in self.model_info.items():
            logging.info(f"method: {method}")
            if method == "pre-calc":
                logging.info(
                    "The model_name should be {M}_{D}_{A}_{hubo_qubo_val}")
            for param, value in info.items():
                logging.info("param: {}, value {}".format(param, value))

        return self.model_info

    def get_model(self, method, model_name):

        return self.model_qubo[method][model_name]

    def save(self, version, path=None):
        save_path = None
        save_name = f"{self.name}_{version}.pickle"

        if path != None:
            save_path = os.path.join(path, save_name)
        else:
            save_path = os.path.join(".", save_name)

        with open(save_path, "wb") as f:
            pickle.dump(self, f)
        logging.info(f"finish save {save_name}")
        return save_path

    @classmethod
    def load(cls, filename):
        with open(filename, "rb") as f:
            return pickle.load(f)  # nosec

    def _prepare_var(self, mol_data, D, method='pre-calc'):

        var = {}
        var_rb_map = {}
        rb_var_map = {}

        if method == 'pre-calc':
            for m, name in enumerate(mol_data.bond_graph.rb_name):
                x_d = {}
                var_rb_map[str(m+1)] = name
                rb_var_map[str(name)] = str(m+1)
                for d in range(D):
                    x_d[str(d+1)] = f"x_{m+1}_{d+1}"
                var[str(m+1)] = x_d
        elif method == 'symbolic':
            for m, name in enumerate(mol_data.bond_graph.rb_name):
                x_d = {}
                var_rb_map[str(m+1)] = name
                rb_var_map[str(name)] = str(m+1)
                d = 0
                exec (f"x_{m+1}_{d+1} = Binary(f'x_{m+1}_{d+1}')") 
                exec (f"x_d[str({d+1})] = x_{m+1}_{d+1}") 

                exec (f"s_value = math.sin(2*math.pi*{d}/({D}))")
                exec (f"x_{m+1}_s_1 = x_{m+1}_{d+1} * s_value")
                exec (f"s_value = math.cos(2*math.pi*{d}/({D}))")
                exec (f"x_{m+1}_c_1 = x_{m+1}_{d+1} * s_value")

                for d in range(1, D):
                    exec (f"x_{m+1}_{d+1} = Binary(f'x_{m+1}_{d+1}')") 
                    exec (f"x_d[str({d+1})] = x_{m+1}_{d+1}") 

                    exec (f"s_value = math.sin(2*math.pi*{d}/({D}))")
                    exec (f"x_{m+1}_s_1 = x_{m+1}_s_1 + x_{m+1}_{d+1} * s_value")
                    exec (f"s_value = math.cos(2*math.pi*{d}/({D}))")
                    exec (f"x_{m+1}_c_1 = x_{m+1}_c_1 + x_{m+1}_{d+1} * s_value")
                exec(f"x_d['s_1'] = x_{m+1}_s_1")
                exec(f"x_d['c_1'] = x_{m+1}_c_1")
                var[str(m+1)] = x_d

        return var, var_rb_map, rb_var_map

    def _init_mol_file(self):
        for pt, info in self.mol_data.atom_data.items():
            self.atom_pos_data[pt] = {}
            self.atom_pos_data[pt]['pts'] = [info['x'], info['y'], info['z']]
            self.atom_pos_data[pt]['idx'] = ([0, 0, 0], [0, 0, 0])
            self.atom_pos_data[pt]['vdw-radius'] = info['vdw-radius']

    def _build_qubo_pre_calc(self, mol_data, M, D, A, var, rb_var_map, var_rb_map, theta_option):
        # initial constraint
        hubo_constraints = {}

        def update_constraint(ris, hubo_constraints):
            for d1 in range(D):
                var_1 = var[rb_var_map[ris]][str(d1+1)]
                for d2 in range(D):
                    var_2 = var[rb_var_map[ris]][str(d2+1)]
                    if (var_2, var_1) in hubo_constraints.keys():
                        hubo_constraints[(var_2, var_1)] = hubo_constraints[(
                            var_2, var_1)] + A
                    elif var_1 == var_2:
                        hubo_constraints[(var_1, var_1)] = -A
                    else:
                        hubo_constraints[(var_1, var_2)] = A

        # update distance term
        hubo_distances = {}

        def _gen_pts_pos_list(pt_set, atom_pos_data):
            return [atom_pos_data[pt]['pts'] for pt in pt_set]

        def _gen_pts_list(pt_set, atom_pos_data):
            return [atom_pos_data[pt] for pt in pt_set]

        def update_hubo(torsion_group, up_list, ris):
            if len(torsion_group) == 1:
                for d in range(D):
                    tor_list = up_list + \
                        [var[rb_var_map[torsion_group[0]]][str(d+1)]]
                    # distance
                    final_list_name = []
                    if len(tor_list) == 1:
                        final_list_name = tor_list + tor_list
                    else:
                        final_list_name = tor_list

                    # update temp points and distance
                    self._init_mol_file()

                    rb_set = self.mol_data.bond_graph.sort_ris_data[str(
                        M)][ris]

                    # build map for affected tor
                    tor_map = {}
                    tor_len = len(tor_list)
                    for base_idx in range(tor_len):
                        tor_name = tor_list[base_idx]
                        tor_map[tor_name] = set()
                        base_rb_name = var_rb_map[tor_list[base_idx].split('_')[
                            1]]

                        # get direction set
                        direction_set = get_same_direction_set(
                            rb_set['f_1_set'], self.mol_data.bond_graph.rb_data, base_rb_name)

                        for candi_idx in range(base_idx, tor_len):
                            candi_rb_name = var_rb_map[tor_list[candi_idx].split('_')[
                                1]].split('+')
                            for rb in candi_rb_name:
                                if rb in direction_set:
                                    tor_map[tor_name].add(rb)

                    distance = update_pts_distance(
                        self.atom_pos_data, rb_set, tor_map, var_rb_map, theta_option, True, True)

                    hubo_distances[tuple(final_list_name)] = -distance
                    logging.debug(
                        f"final list {tor_list} with distance {distance}")
            else:
                for d in range(D):
                    final_list = up_list + \
                        [var[rb_var_map[torsion_group[0]]][str(d+1)]]
                    update_hubo(torsion_group[1:], final_list, ris)

        for ris in mol_data.bond_graph.sort_ris_data[str(M)].keys():
            start = time.time()
            logging.debug(f"ris group {ris} ")
            end = time.time()
            torsion_group = ris.split(",")
            if len(torsion_group) == 1:
                # update constraint
                update_constraint(ris, hubo_constraints)
            logging.debug(torsion_group)
            # update hubo terms
            update_hubo(torsion_group, [], ris)
            logging.debug(
                f"elapsed time for torsion group {ris} : {(end-start)/60} min")

        return hubo_constraints, hubo_distances

    def _build_qubo_symbolic(self, mol_data, M, D, A, var, rb_var_map):
        self._init_mol_file()
        atom_pos_data = self.atom_pos_data
        # qmu_qubo._init_mol_file()
        # atom_pos_data = qmu_qubo.atom_pos_data

        hubo_constraints = Num(0)
        hubo_distance = Num(0)

        def update_constraint(ris, hubo_constraints):
            # implement variable for one torsion
            for d1 in range(D):
                var_1 = var[rb_var_map[ris]][str(d1+1)]
                for d2 in range(D):
                    var_2 = var[rb_var_map[ris]][str(d2+1)]
                    if var_1 == var_2:
                        hubo_constraints = hubo_constraints + var_1 * var_1 * -A
                    else:
                        hubo_constraints = hubo_constraints + var_1 * var_2 * 2 * A
            
            return hubo_constraints

        def update_hubo(torsion_group, hubo_distance, tor_points):
            rot_mat = None

            logging.info("update hubo 1")
            for tor in torsion_group:
                c = var[rb_var_map[tor]]['c_1']
                s = var[rb_var_map[tor]]['s_1']
                start_pts = atom_pos_data[tor.split('+')[0]]
                end_pts = atom_pos_data[tor.split('+')[1]]
                if rot_mat is None:
                    rot_mat, _ = rot_mat_value(start_pts['pts'], end_pts['pts'], c, s)
                else:
                    new_mat, _ = rot_mat_value(start_pts['pts'], end_pts['pts'], c, s)
                    rot_mat = new_mat.matmul(rot_mat)
            logging.info("update hubo 2")
            # update points distance
            tor_points_f_0_set = tor_points['f_0_set']
            tor_points_f_1_set = tor_points['f_1_set']

            avg_a_sum = [0]*3
            avg_b_sum = [0]*3
            logging.info("update hubo 3")
            for f_0 in tor_points_f_0_set:
                avg_a_sum[0] = avg_a_sum[0] + atom_pos_data[f_0]['pts'][0]
                avg_a_sum[1] = avg_a_sum[1] + atom_pos_data[f_0]['pts'][1]
                avg_a_sum[2] = avg_a_sum[2] + atom_pos_data[f_0]['pts'][2]
            for f_1 in tor_points_f_1_set:
                avg_b_sum[0] = avg_b_sum[0] + atom_pos_data[f_1]['pts'][0]
                avg_b_sum[1] = avg_b_sum[1] + atom_pos_data[f_1]['pts'][1]
                avg_b_sum[2] = avg_b_sum[2] + atom_pos_data[f_1]['pts'][2]
            
            logging.info("update hubo 4")
            avg_a = [v/len(tor_points_f_0_set) for v in avg_a_sum]
            avg_b = [v/len(tor_points_f_1_set) for v in avg_b_sum]
            a_homo_pos = Array([[avg_a[0]], [avg_a[1]], [avg_a[2]], [1]])
            b_homo_pos = Array([[avg_b[0]], [avg_b[1]], [avg_b[2]], [1]])
            result_array = a_homo_pos - rot_mat.matmul(b_homo_pos)
            distance = result_array.T.matmul(result_array)
            hubo_distance = hubo_distance - distance[0][0]

            logging.info("update hubo 5")
            # for f_0 in tor_points_f_0_set:
            #     for f_1 in tor_points_f_1_set:
            #         a_pos = atom_pos_data[f_0]['pts']
            #         b_pos = atom_pos_data[f_1]['pts']
            #         a_homo_pos = Array([[a_pos[0]], [a_pos[1]], [a_pos[2]], [1]])
            #         b_homo_pos = Array([[b_pos[0]], [b_pos[1]], [b_pos[2]], [1]])
            #         result_array = a_homo_pos - rot_mat.matmul(b_homo_pos)
            #         distance = result_array.T.matmul(result_array)
            #         hubo_distance = hubo_distance - distance[0][0]
            
            return hubo_distance

        for ris in mol_data.bond_graph.sort_ris_data[str(M)].keys():
            start = time.time()
            logging.info(f"Rotables influence set(ris) group {ris}")
            end = time.time()
            torsion_group = ris.split(",")
            if len(torsion_group) == 1:
                # update constraint
                hubo_constraints = update_constraint(ris, hubo_constraints)

            ris_data = mol_data.bond_graph.sort_ris_data[str(M)][ris]
            hubo_distances = update_hubo(torsion_group, hubo_distance, ris_data)
        
        return hubo_constraints, hubo_distances