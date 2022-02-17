########################################################################################################################
#   The following class is the construction of QUBO model
########################################################################################################################
import dimod
from .MolGeoCalc import update_pts_distance

from collections import defaultdict
import time
import logging
import pickle
import os

log = logging.getLogger()
log.setLevel('INFO')


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
            elif mt == "after-calc":
                logging.info(
                    "initial after calculate for constructing molecule QUBO not implemented !!")
            else:
                logging.info(f"only pre-calculate(method='pre-calc') and after-calculate(method='after-calc') are supported, \
                method {mt} not support !!")

    def build_model(self, **param):
        for method, config in param.items():
            model_param = config
            if method == "pre-calc":
                self._build_pre_calc_model(**model_param)
        return 0

    def _build_pre_calc_model(self, **model_param):
        for M in model_param["M"]:
            for D in model_param["D"]:
                for A in model_param["A"]:
                    for hubo_qubo_val in model_param["hubo_qubo_val"]:
                        # update var_map
                        # prepare variables
                        self.var, self.var_rb_map, self.rb_var_map = self._prepare_var(
                            self.mol_data, D)
                        # check availability
                        if self._check_duplicate([M, D, A, hubo_qubo_val], ["M", "D", "A", "hubo_qubo_val"], "pre-calc"):
                            logging.info(
                                f"duplicate model !! pass !! M:{M},D:{D},A:{A},hubo_qubo_val {hubo_qubo_val}")
                            continue
                        start = time.time()
                        hubo = {}
                        theta_option = [x * 360/D for x in range(D)]
                        hubo_constraints, hubo_distances = self._build_qubo_pre_calc(self.mol_data, M, D, A, self.var,
                                                                                     self.rb_var_map, self.var_rb_map,
                                                                                     theta_option)
                        hubo.update(hubo_constraints)
                        hubo.update(hubo_distances)
                        # transfer hubo to qubo
                        # TODO why make_quadratic not work?
                        # qubo_raw = dimod.make_quadratic(
                        #     hubo, hubo_qubo_val, dimod.BINARY).to_qubo()
                        qubo_raw = dimod.make_quadratic(
                            hubo, hubo_qubo_val, dimod.BINARY)
                        qubo = self._manual_qubo(qubo_raw.to_qubo())
                        end = time.time()
                        model_name = f"{M}_{D}_{A}_{hubo_qubo_val}"
                        self.model_qubo["pre-calc"][model_name] = {}
                        self.model_qubo["pre-calc"][model_name]["qubo"] = qubo
                        self.model_qubo["pre-calc"][model_name]["var"] = self.var
                        self.model_qubo["pre-calc"][model_name]["var_rb_map"] = self.var_rb_map
                        self.model_qubo["pre-calc"][model_name]["rb_var_map"] = self.rb_var_map
                        self.model_qubo["pre-calc"][model_name]["time"] = end-start
                        self.model_qubo["pre-calc"][model_name]["model_name"] = model_name
                        ris_name = list(
                            self.mol_data.bond_graph.sort_ris_data[str(M)].keys()).copy()
                        valid_rb_name = []
                        for name in ris_name:
                            if len(name.split(',')) == 1:
                                valid_rb_name.append(name)
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

    def _check_duplicate(self, values, names, method):
        initial_size = 0
        update_size = 0
        for value, name in zip(values, names):
            initial_size = initial_size + len(self.model_info[method][name])
            self.model_info[method][name].add(value)
            update_size = update_size + len(self.model_info[method][name])
        if initial_size == update_size:
            return True
        else:
            return False

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
            return pickle.load(f)

    def _prepare_var(self, mol_data, D):

        var = {}
        var_rb_map = {}
        rb_var_map = {}

        for m, name in enumerate(mol_data.bond_graph.rb_name):
            x_d = {}
            var_rb_map[str(m+1)] = name
            rb_var_map[str(name)] = str(m+1)
            for d in range(D):
                x_d[str(d+1)] = f"x_{m+1}_{d+1}"
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
                    final_list = up_list + \
                        [var[rb_var_map[torsion_group[0]]][str(d+1)]]
                    # distance
                    final_list_name = []
                    if len(final_list) == 1:
                        final_list_name = final_list + final_list
                    else:
                        final_list_name = final_list

                    # update temp points and distance
                    self._init_mol_file()

                    rb_set = self.mol_data.bond_graph.sort_ris_data[str(
                        M)][ris]

                    distance = update_pts_distance(
                        self.atom_pos_data, rb_set, final_list, var_rb_map, theta_option, True, True)

                    hubo_distances[tuple(final_list_name)] = -distance
                    logging.debug(
                        f"final list {final_list} with distance {distance}")
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
