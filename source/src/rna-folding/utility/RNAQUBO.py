# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

########################################################################################################################
#   The following class is the construction of QUBO model
########################################################################################################################
import dimod

import numpy as np
from collections import defaultdict
import time
import logging
import pickle  # nosec
import os

from .RNAParser import RNAData
from .RNAGeoCalc import *

log = logging.getLogger()
log.setLevel('INFO')


class RNAQUBO():

    def __init__(self, data_path, method, **param):

        # prepare parameters
        self.param = param
        self.data_path = data_path
        self.method = method

        self.models = {}

        self.rna_data = RNAData.load(self.data_path).rna_files
        for rna_name in self.rna_data:
            self.models[rna_name] = {}
            self.models[rna_name]['model_info'] = {}
            self.models[rna_name]['model_qubo'] = {}
            for method in self.method:
                self.models[rna_name]['model_info'][method] = {}
                self.models[rna_name]['model_qubo'][method] = {}

                if method == 'qc':
                    logging.info(
                    "initial qc for constructing rna QUBO")
                    for param in self.param[method]["params"]:
                        self.models[rna_name]['model_info'][method][param] = set()


    def build_models(self, **param):

        for method, config in param.items():
            model_param = config

            if method == "qc":
                self._build_qc_models(**model_param)
                
            return 0
        
    def _build_qc_models(self, **model_param):

        for rna_name in self.models:
            for pkp_penalty in model_param["PKP"]:
                for overlap_penalty in model_param["O"]:
                    for short_penalty in model_param["S"]:
                        model_name = f"{rna_name}+{pkp_penalty}+{overlap_penalty}+{short_penalty}+"

                        # check availability
                        if model_name in self.models[rna_name]['model_qubo']["qc"].keys():
                            logging.info(
                                f"duplicate model !! pass !! rna: {rna_name}, pkp:{pkp_penalty},O:{overlap_penalty},S:{short_penalty}")
                            continue
                        else:
                            self._update_model_info(rna_name, [pkp_penalty, overlap_penalty, short_penalty], [
                                                    "PKP", "O", "S"], "qc")


                        start = time.time()
                        stems_p = self.rna_data[rna_name]['potential_stems']
                        pks_p = potential_pseudoknots(stems_p[0], pkp_penalty)
                        ols_p = self._potential_overlaps(stems_p[0])
                        qubo_data = self._model(stems_p[0], pks_p, ols_p, stems_p[1])
                        qubo_raw = dimod.BinaryQuadraticModel(qubo_data[0], qubo_data[1], vartype = 'BINARY')
                        qubo = self._manual_qubo(qubo_raw.to_qubo())
                        end = time.time()

                        self.models[rna_name]['model_qubo']["qc"][model_name] = {}
                        self.models[rna_name]['model_qubo']["qc"][model_name]["qubo"] = qubo
                        self.models[rna_name]['model_qubo']["qc"][model_name]["time"] = end-start
                        self.models[rna_name]['model_qubo']["qc"][model_name]["model_name"] = model_name
    #                 
    #                 # # optimize results
    #                 # self.model_qubo["pre-calc"][model_name]["optimizer"] = {}
    #                 # self.model_qubo["pre-calc"][model_name]["optimizer"]["post"] = {}

    #                 logging.info(
    #                     f"Construct model for PKP:{pkp_penalty},O:{overlap_penalty},S:{short_penalty} {(end-start)/60} min")

    def _manual_qubo(self, qubo_raw):
        qubo = defaultdict(float)

        for key, value in qubo_raw[0].items():
            qubo[key] = value

        return qubo

    def describe_models(self):

        # information for model
        for rna_name in self.models:
            for method, info in self.models[rna_name]['model_info'].items():
                logging.info(f"method: {method}")
                if method == "qc":
                    logging.info(
                        "The model_name should be " + rna_name + "_{PKP}_{O}_{S}")
                for param, value in info.items():
                    logging.info("param: {}, value {}".format(param, value))
            
            print()

    def _update_model_info(self, rna_name, values, names, method):
        for value, name in zip(values, names):
            self.models[rna_name]['model_info'][method][name].add(value)

    def get_model(self, rna_name, method, model_name):
        return self.models[rna_name]['model_qubo'][method][model_name]

    def save(self, version, path=None):

        save_path = None
        save_name = f"rna_folding_{version}.pickle"

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

    # function to generate list of stem pairs that overlap:

    def _potential_overlaps(self, stems_potential):
        
        overlaps_potential = []
        overlap_penalty = 1e6

        for i in range(len(stems_potential)):
            for j in range(i+1, len(stems_potential)):
        
                stem1 = stems_potential[i]
                stem2 = stems_potential[j]
        
                overlap = [i, j, 0]
        
                stem1_cspan1 = set(range(stem1[1]-int(stem1[2])+1, stem1[1]+1))
                stem2_cspan1 = set(range(stem2[1]-int(stem2[2])+1, stem2[1]+1))
                
                stem1_cspan2 = set(range(stem1[0], stem1[0]+int(stem1[2])))
                stem2_cspan2 = set(range(stem2[0], stem2[0]+int(stem2[2])))

                # stem1_cspan1 = set(range(stem1[1]-int(stem1[3])+1, stem1[1]+1))
                # stem2_cspan1 = set(range(stem2[1]-int(stem2[3])+1, stem2[1]+1))
                
                # stem1_cspan2 = set(range(stem1[0], stem1[0]+int(stem1[3])))
                # stem2_cspan2 = set(range(stem2[0], stem2[0]+int(stem2[3])))
        
                if (len(stem1_cspan1 & stem2_cspan1) != 0) or (len(stem1_cspan2 & stem2_cspan2) != 0)  or (len(stem1_cspan1 & stem2_cspan2) != 0) or (len(stem1_cspan2 & stem2_cspan1) != 0):
            
                    overlap[2] = overlap_penalty
            
                overlaps_potential.append(overlap)
                
        return overlaps_potential

    # function to generate the Hamiltonian of a given RNA structure from potential stems, overlaps, and pseudoknots:

    def _model(self, stems_potential, pseudoknots_potential, overlaps_potential, mu):
        
        L = {}
        Q = {}
        cl = 1
        cb = 1
        k = 0

        for i in range(0, len(stems_potential)):
            L[str(i)] = cl*((stems_potential[i][2]**2)-2*mu*stems_potential[i][2]+mu**2)-cb*(stems_potential[i][2]**2)
            for j in range(i+1, len(stems_potential)):
                Q[(str(i), str(j))] = -2*cb*stems_potential[i][2]*stems_potential[j][2]*pseudoknots_potential[k][2]+overlaps_potential[k][2]
                k += 1
        
        return L, Q
