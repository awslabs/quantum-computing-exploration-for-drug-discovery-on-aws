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
                        model_name = f"{rna_name}_{pkp_penalty}_{overlap_penalty}_{short_penalty}"

                        # check availability
                        if model_name in self.models[rna_name]['model_qubo']["qc"].keys():
                            logging.info(
                                f"duplicate model !! pass !! rna: {rna_name}, pkp:{pkp_penalty},O:{overlap_penalty},S:{short_penalty}")
                            continue
                        else:
                            self._update_model_info(rna_name, [pkp_penalty, overlap_penalty, short_penalty], [
                                                    "PKP", "O", "S"], "qc")


                        start = time.time()
                        stems_p = self._potential_stems(self.rna_data[rna_name]['rna_strand'])
                        pks_p = self._potential_pseudoknots(stems_p[0], pkp_penalty)
                        ols_p = self._potential_overlaps(stems_p[0])
                        qubo_data = self._model(stems_p[0], pks_p, ols_p, stems_p[1])
                        qubo = dimod.BinaryQuadraticModel(qubo_data[0], qubo_data[1], vartype = 'BINARY', offset = 0.0)
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

        for rna_name in self.models:
            save_name = f"{rna_name}_{version}.pickle"

            if path != None:
                save_path = os.path.join(path, save_name)
            else:
                save_path = os.path.join(".", save_name)

            with open(save_path, "wb") as f:
                pickle.dump(self.models[rna_name], f)
            logging.info(f"finish save {save_name}")

    # function to read in .fasta file and generate list of potential stems at least 3 base-pairs long:
    def _potential_stems(self, rna_strand):
        
        rna = rna_strand
        
        matrix = np.zeros((len(rna),len(rna)))

        for diag in range(0, len(matrix)):
            for row in range(0, len(matrix)-diag):
                col = row + diag
                base1 = rna[row]
                base2 = rna[col]
                if row != col:
                    if ((base1 == ("A" or "a")) and (base2 == ("U" or "u"))) or ((base1 == ("U" or "u")) and (base2 == ("A" or "a"))) or ((base1 == ("G" or "g")) and (base2 == ("U" or "u"))) or ((base1 == ("U" or "u")) and (base2 == ("G" or "g"))):
                        matrix[row][col] = 2
                    if ((base1 == ("G" or "g")) and (base2 == ("C" or "c"))) or ((base1 == ("C" or "c")) and (base2 == ("G" or "g"))):
                        matrix[row][col] = 3
        stems_potential = []
        mu = 0

        for row in range(0, len(matrix)):
            for col in range (row, len(matrix)):
                if row != col:
                    if matrix[row][col] != 0:
                        temp_row = row
                        temp_col = col
                        stem = [row+1,col+1,0,0]
                        length_N = 0
                        length_H = 0
                        while (matrix[temp_row][temp_col] != 0) and (temp_row != temp_col):
                            length_N+=1
                            length_H+=matrix[temp_row][temp_col]
                            temp_row+=1
                            temp_col-=1
                            if length_N >= 3:
                                stem[2] = int(length_H)
                                stem[3] = int(length_N)
                                stems_potential.append(stem.copy())
                        if length_H > mu:
                            mu = length_H
        
        return [stems_potential, mu, rna, len(rna)]

    # function to generate list of potential stem pairs that form pseudoknots:

    def _potential_pseudoknots(self, stems_potential, pkp):

        pseudoknots_potential = []
        pseudoknot_penalty = pkp

        for i in range(len(stems_potential)):
            for j in range(i + 1, len(stems_potential)):
                
                stem1 = stems_potential[i]
                stem2 = stems_potential[j]
        
                i_a = stem1[0]
                j_a = stem1[1]
                i_b = stem2[0]
                j_b = stem2[1]
        
                pseudoknot = [i,j,1]
        
                if (i_a < i_b and i_b < j_a and j_a < j_b):
            
                    pseudoknot[2] = pseudoknot_penalty
        
                pseudoknots_potential.append(pseudoknot)
                
        return pseudoknots_potential

    # function to generate list of stem pairs that overlap:

    def _potential_overlaps(self, stems_potential):
        
        overlaps_potential = []
        overlap_penalty = 1e6

        for i in range(len(stems_potential)):
            for j in range(i+1, len(stems_potential)):
        
                stem1 = stems_potential[i]
                stem2 = stems_potential[j]
        
                overlap = [i, j, 0]
        
                stem1_cspan1 = set(range(stem1[1]-int(stem1[3])+1, stem1[1]+1))
                stem2_cspan1 = set(range(stem2[1]-int(stem2[3])+1, stem2[1]+1))
                
                stem1_cspan2 = set(range(stem1[0], stem1[0]+int(stem1[3])))
                stem2_cspan2 = set(range(stem2[0], stem2[0]+int(stem2[3])))
        
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
