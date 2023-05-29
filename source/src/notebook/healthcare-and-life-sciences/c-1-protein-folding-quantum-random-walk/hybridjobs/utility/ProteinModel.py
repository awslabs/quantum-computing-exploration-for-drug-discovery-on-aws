# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

########################################################################################################################
#   The following class is the construction of Protein Model
########################################################################################################################
import numpy as np
import time
import logging
import pickle  # nosec
import os
import sys

__dir__ = os.path.dirname(os.path.abspath(__file__))
sys.path.append(__dir__)

from Metropolis import ClassicalMetropolis, QuantumMetropolis
import utils
import initializer
import psiFour

class ProteinModel():

    def __init__(self, data_path, method, config_path, **param):

        # prepare parameters
        self.param = param
        self.data_path = data_path
        self.config_path = config_path
        self.method = method

        self.models = {}

        # self.protein_data = ProteinData.load(self.data_path).protein_files

        # prepare common parameters
        self.psi, self.angleInitializer = self._update_common_param()

        # check whether file exists
        # TODO

        self.protein_data = ['glycylglycine_3_GG', 'glycylglycine_4_GG']
        
        for protein_name in self.protein_data:
            self.models[protein_name] = {}
            self.models[protein_name]['model_info'] = {}
            self.models[protein_name]['model'] = {}
            for method in self.method:
                self.models[protein_name]['model_info'][method] = {}
                self.models[protein_name]['model'][method] = {}

                for param in self.param[method]["params"]:
                    self.models[protein_name]['model_info'][method][param] = set()
                
                logging.info(f"Initial parameters for protein {protein_name} using {method}")

    def _update_common_param(self):
        self.tools = utils.Utils(self.config_path)

        config_variables = self.tools.get_config_variables()

        precalculated_energies_path = self.data_path + config_variables['precalculated_energies_path']
        angleInitializer = initializer.Initializer(
            psi4_path = config_variables['psi4_path'],
            input_file_energies_psi4 = config_variables['input_filename_energy_psi4'], 
            output_file_energies_psi4 = config_variables['output_filename_energy_psi4'],
            energy_method = config_variables['energy_method'],
            precalculated_energies_path = precalculated_energies_path, 
            model_path = config_variables['model_path'], 
            window_size = config_variables['window_size'], 
            max_aa_length = config_variables['maximum_aminoacid_length'],
            initialization_option = config_variables['methods_initialization'],
            n_threads = config_variables['n_threads_pool'],
            basis = config_variables['basis']
            )

        psi = psiFour.PsiFour(
            config_variables['psi4_path'], 
            config_variables['input_filename_energy_psi4'], 
            config_variables['output_filename_energy_psi4'], 
            precalculated_energies_path, 
            config_variables['energy_method'], 
            config_variables['n_threads_pool'],
            config_variables['basis'])
        
        return psi, angleInitializer

    def build_models(self, **param):

        for method, config in param.items():
            model_param = config

            if method == "qfold-cc":
                self._build_qfold_models(method, ClassicalMetropolis, **model_param)
            elif method == "qfold-qc":
                self._build_qfold_models(method, QuantumMetropolis, **model_param)
            
        return 0

    def _build_qfold_models(self, method, build_model, **model_param):

        for protein_name in self.models:
            for initialization in model_param["initialization"]:
                parse_name = protein_name.split('_')
                pure_protein_name = parse_name[0]
                bits = parse_name[1]
                aminoacids = parse_name[2]

                model_name = f"{protein_name}+{initialization}"
                # check availability
                if model_name in self.models[protein_name]['model'][method].keys():
                    logging.info(
                        f"duplicate model !! pass !! model {model_name} already exists")
                    continue
                else:
                    self._update_model_info(protein_name, [initialization], ["initialization"], method)

                [deltas_dict, psi4_min_energy, initial_min_energy, index_min_energy, initialization_stats] = \
                self.psi.readEnergyJson(pure_protein_name, bits, initialization)

                self.n_angles = (len(aminoacids) -1)*2

                print(f"deltas_dict length for {protein_name}: {len(deltas_dict)}")

                qfold_metropolis = build_model(self.n_angles, deltas_dict, initialization, int(bits), self.tools)

                self.models[protein_name]['model'][method][model_name] = {}
                self.models[protein_name]['model'][method][model_name]["model_name"] = model_name
                self.models[protein_name]['model'][method][model_name]["model_params"] = {}
                self.models[protein_name]['model'][method][model_name]["model_params"]["index_min_energy"] = index_min_energy
                self.models[protein_name]['model'][method][model_name]["model_params"]["initilization_stats"] = initialization_stats
                self.models[protein_name]['model'][method][model_name]["version"] = str(int(time.time()))
                self.models[protein_name]['model'][method][model_name]["model"] = qfold_metropolis
    
    def describe_models(self):
        # information for model
        logging.info("debug describe")
        for protein_name in self.models:
            for method, info in self.models[protein_name]['model_info'].items():
                logging.info(f"model name: {protein_name}, method: {method}")
                # if method == "qc":
                #     logging.info(
                #         "The model_name should be " + protein_name + "_{PKP}_{O}_{S}")
                for param, value in info.items():
                    logging.info("param: {}, value {}".format(param, value))

    def _update_model_info(self, protein_name, values, names, method):
        for value, name in zip(values, names):
            self.models[protein_name]['model_info'][method][name].add(value)

    def get_model(self, protein_name, method, model_name):
        return self.models[protein_name]['model'][method][model_name]

    def save(self, version, path=None):

        save_path = None
        save_name = f"protein_folding_{version}.pickle"

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