# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

########################################################################################################################
#   The following class is the construction of Protein Model
########################################################################################################################
import dimod

import numpy as np
from collections import defaultdict
import time
import logging
import pickle  # nosec
import os

from .proteinParser import ProteinData
from .proteinGeoCalc import *

import metropolis
import quantumMetropolis
import time
import collections, functools, operator

import copy
import math

from Metropolis import ClassicalMetropolis, QuantumMetropolis

log = logging.getLogger()
log.setLevel('INFO')
config_variables = tools.get_config_variables()
angleInitializer = initializer.Initializer(
    psi4_path = config_variables['psi4_path'],
    input_file_energies_psi4 = config_variables['input_filename_energy_psi4'], 
    output_file_energies_psi4 = config_variables['output_filename_energy_psi4'],
    energy_method = config_variables['energy_method'],
    precalculated_energies_path = config_variables['precalculated_energies_path'], 
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
    config_variables['precalculated_energies_path'], 
    config_variables['energy_method'], 
    config_variables['n_threads_pool'],
    config_variables['basis'])

#Check if it existes a precalculated energy file with the same parameters, if not call initializer to calculate it
#The format should be energies[args.protein_name][numberBitsForRotation] ex: energiesGlycylglycine2.json
try:
    f = open(config_variables['precalculated_energies_path']+'delta_energies_'+args.protein_name+'_'+str(args.bits)+'_'+args.initialization+'.json')
    f.close()
except IOError:
    print('<!> Info: No precalculated energies file', config_variables['precalculated_energies_path']+'delta_energies_'+args.protein_name+'_'+str(args.bits)+'_'+args.initialization+'.json','found => Calculating energies\n')
    angleInitializer.calculate_delta_energies(args.protein_name, args.bits, args.initialization, args.aminoacids, args.id)

[deltas_dict, psi4_min_energy, initial_min_energy, index_min_energy, initialization_stats] = psi.readEnergyJson(args.protein_name, args.bits, args.initialization)

print('## 3D STRUCTURE CALCULATOR FOR', args.protein_name,'with', args.bits,'bits and', args.initialization,'initialization##\n')

angleCalculator = angleCalculator.AngleCalculator(tools, angleInitializer, initialization_stats)
[min_q_tts, min_c_tts] = angleCalculator.calculate3DStructure(deltas_dict, index_min_energy)

execution_time = time.time() - start_time

class ProteinModel():

    def __init__(self, data_path, method, **param):

        # prepare parameters
        self.param = param
        self.data_path = data_path
        self.method = method

        self.models = {}

        # self.protein_data = ProteinData.load(self.data_path).protein_files

        # prepare common parameters
        self._update_common_param()

        # check whether file exists
        # TODO

        self.protein_data = ['aadd', 'alanylalanine']
        
        for protein_name in self.protein_data:
            self.models[protein_name] = {}
            self.models[protein_name]['model_info'] = {}
            self.models[protein_name]['model_qubo'] = {}
            for method in self.method:
                self.models[protein_name]['model_info'][method] = {}
                self.models[protein_name]['model'][method] = {}

                for param in self.param[method]["param"]:
                    self.models[protein_name]['model_info'][param] = set()
                logging.info(f"Initial parameters for {method}")

    def _update_common_param(self):
        config_path = './config/config.json'
        self.tools = utils.Utils(config_path)
        config_variables = self.tools.get_config_variables()
        self.n_angles = (len(self.tools.args.aminoacids) -1)*2

        angleInitializer = initializer.Initializer(
            psi4_path = config_variables['psi4_path'],
            input_file_energies_psi4 = config_variables['input_filename_energy_psi4'], 
            output_file_energies_psi4 = config_variables['output_filename_energy_psi4'],
            energy_method = config_variables['energy_method'],
            precalculated_energies_path = config_variables['precalculated_energies_path'], 
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
            config_variables['precalculated_energies_path'], 
            config_variables['energy_method'], 
            config_variables['n_threads_pool'],
            config_variables['basis'])

    def build_models(self, **param):

        for method, config in param.items():
            model_param = config

            if method == "qfold-cc":
                self._build_qfold_cc_models(**model_param)
            elif method == "qfold-qc":
                self._build_qfold_qc_models(**model_param)
            
        return 0

    def _build_qfold_cc_models(self, **model_param):

        for protein_name in models_param["peptide_name"]:
            for bits in model_param["bits"]:
                for initialization in model_param["initilization"]:
                    model_name = f"{protein_name}+{bits}+{initialization}"

                    # check availability
                    if model_name in self.models[protein_name]['qfold-cc'].keys():
                        logging.info(
                            f"duplicate model !! pass !! model {model_name} already exists")
                        continue
                    else:
                        self._update_model_info(protein_name, [protein_name, bits, initialization], [
                                                "peptide_name", "bits", "initialization"], "qfold-cc")

                    [deltas_dict, psi4_min_energy, initial_min_energy, index_min_energy, initialization_stats] = \
                    psi.readEnergyJson(protein_name, bits, initialization)

                    qfold_classical_metropolis = ClassicalMetropolis(self.n_angles, deltas_dict, self.tools)

                    self.models[protein_name]['qfold-cc'][model_name] = {}
                    self.models[protein_name]['qfold-cc'][model_name]["model_name"] = model_name
                    self.models[protein_name]['qfold-cc'][model_name]["version"] = str(int(time.time()))
                    self.models[protein_name]['qfold-cc'][model_name]["model"] = qfold_classical_metropolis
    
    def _build_qfold_qc_models(self, **model_param):

        for protein_name in models_param["peptide_name"]:
            for bits in model_param["bits"]:
                for initialization in model_param["initilization"]:
                    model_name = f"{protein_name}+{bits}+{initialization}"

                    # check availability
                    if model_name in self.models[protein_name]['qfold-qc'].keys():
                        logging.info(
                            f"duplicate model !! pass !! model {model_name} already exists")
                        continue
                    else:
                        self._update_model_info(protein_name, [protein_name, bits, initialization], [
                                                "peptide_name", "bits", "initialization"], "qfold-qc")

                    [deltas_dict, psi4_min_energy, initial_min_energy, index_min_energy, initialization_stats] = \
                    psi.readEnergyJson(protein_name, bits, initialization)

                    qfold_quantum_metropolis = QuantumMetropolis(self.n_angles, deltas_dict, self.tools)

                    self.models[protein_name]['qfold-qc'][model_name] = {}
                    self.models[protein_name]['qfold-qc'][model_name]["model_name"] = model_name
                    self.models[protein_name]['qfold-qc'][model_name]["version"] = str(int(time.time()))
                    self.models[protein_name]['qfold-qc'][model_name]["model"] = qfold_quantum_metropolis 

    def describe_models(self):

        # information for model
        for protein_name in self.models:
            for method, info in self.models[protein_name]['model_info'].items():
                logging.info(f"method: {method}")
                if method == "qc":
                    logging.info(
                        "The model_name should be " + protein_name + "_{PKP}_{O}_{S}")
                for param, value in info.items():
                    logging.info("param: {}, value {}".format(param, value))
            
            print()

    def _update_model_info(self, protein_name, values, names, method):
        for value, name in zip(values, names):
            self.models[protein_name]['model_info'][method][name].add(value)

    def get_model(self, protein_name, method, model_name):
        return self.models[protein_name]['model_qubo'][method][model_name]

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