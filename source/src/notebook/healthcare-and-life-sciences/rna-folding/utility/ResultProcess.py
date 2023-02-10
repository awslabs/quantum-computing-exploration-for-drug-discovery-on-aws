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
from os.path import exists
import datetime
import logging
import re
import matplotlib.pyplot as plt
import forgi.visual.mplotlib as fvm
import forgi 
import sys

from .RNAParser import RNAData
from .RNAGeoCalc import *

# import py3Dmol
import time
# from ipywidgets import interact, fixed, IntSlider
# import ipywidgets

s3_client = boto3.client("s3")

log = logging.getLogger()
log.setLevel('INFO')
logging._srcfile = None

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

        # parse model_info
        self.data_name = None
        self.pkp = None
        self._parse_model_info()

        self.predicted_stem = None

        # result: get by task_id, maintain by braket api
        self.result = None
        # initial mol file
        self.atom_pos_data = {}
        self.atom_pos_data_raw = {}
        self.atom_pos_data_temp = {}
        self.mol_file_name = '/'.join([param["raw_path"],self.data_name])
        logging.info("Data.load()")
        self.data_path = param["data_path"]
        self.rna_name = self.data_name
        self.rna_data = RNAData.load(param["data_path"]).rna_files
        # calculate actual energy
        self.actual_stems = self.rna_data[self.rna_name]['actual_stems']
        self.actual_energy = self._energy(self.rna_data[self.rna_name]['actual_stems'], self.pkp)
        logging.info(f"actual energy is {self.actual_energy}")

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
        
        # initial parameters
        self.parameters = {}
        self._init_parameters()
    
    def generate_optimize_pts(self):
        logging.info("generate_optimize_pts()")
        # get best configuration
        pddf_sample_result = self.raw_result["response"].aggregate(
        ).to_pandas_dataframe()

        pddf_head_sample = pddf_sample_result.sort_values(
            by=['energy']).head(self.N)

        evaluate_loop_result = False
        min_energy_score = sys.maxsize
        best_opt_ans = None
        max_volume = 0
        best_stem = None

        for index, row in pddf_head_sample.iterrows():
            predicted_energy = row['energy']
            generate_row = self._generate_row_data(row)

            logging.debug(f"predicted stem {generate_row} with energy {predicted_energy}")

            if predicted_energy < min_energy_score:
                min_energy_score = predicted_energy
                best_stem = generate_row
        
        self.predicted_stem = best_stem

        self.parameters["structure"]["predict"]["stems"] = self.predicted_stem
        self.parameters["structure"]["predict"]["energy"] = min_energy_score
        # calculate parameters for predicted stem
        bp_specificity, bp_sensitivity = self._evaluation_bp(self.actual_stems, self.predicted_stem)
        bases_specificity, bases_sensitivity = self._evaluation_bases(self.actual_stems, self.predicted_stem)

        self.parameters["structure"]["predict"]["bp-specificity"] = bp_specificity
        self.parameters["structure"]["predict"]["bp-sensitivity"] = bp_sensitivity
        self.parameters["structure"]["predict"]["bases-specificity"] = bases_specificity
        self.parameters["structure"]["predict"]["bases-sensitivity"] = bases_sensitivity

    # function to generate list of potential stem pairs that form pseudoknots:
    def potential_pseudoknots(self, stems_potential, pkp):

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
        
                if (i_a < i_b and i_b < j_a and j_a < j_b) or (i_b < i_a and i_a < j_b and j_b < j_a):
            
                    pseudoknot[2] = pseudoknot_penalty
        
                pseudoknots_potential.append(pseudoknot)
                
        return pseudoknots_potential

    # function to evaluate the energy of the known structure under the model Hamiltonian:
    def _energy(self, stems_actual, pkp):
        
        cl = 1
        cb = 1
        k = 0
        
        pseudoknots_actual = potential_pseudoknots(stems_actual, pkp)
        cost = 0
        mu = max(list(map(list, zip(*stems_actual)))[2])
        
        for i in range(0, len(stems_actual)):
            cost += cl*((stems_actual[i][2]**2)-2*mu*stems_actual[i][2]+mu**2)-cb*(stems_actual[i][2]**2)
            for j in range(i+1, len(stems_actual)):
                cost -= 2*cb*stems_actual[i][2]*stems_actual[j][2]*pseudoknots_actual[k][2]
                k += 1
        
        return cost

    # function to compare actual and predicted structure based on comparison of base-pairs:
    def _evaluation_bp(self, stems_actual, stems_potential):
       
        bp_actual = []
        bp_predicted = []

        for i in range(0, len(stems_actual)):
            for j in range(0, stems_actual[i][2]):
                bp_actual.append((stems_actual[i][0]+j, stems_actual[i][1]-j))
           
        for i in range(0, len(stems_potential)):
            for j in range(0, stems_potential[i][2]):
                bp_predicted.append((stems_potential[i][0]+j, stems_potential[i][1]-j))
               
        C = 0    # number of correctly identified base pairs
        M = 0    # number of the predicted base pairs missing from the known structure
        I = 0    # number of non-predicted base pairs present in the known structure

        for i in range(0, len(bp_predicted)):
            if bp_predicted[i] in bp_actual:
                C += 1
            else:
                M += 1

        for i in range(0, len(bp_actual)):
            if bp_actual[i] not in bp_predicted:
                I += 1
               
        sensitivity = C/(C+M)
        specificity = C/(C+I)

        return specificity, sensitivity
   
    # function to compare actual and predicted structure based on comparison of bases involved in pairing:
    def _evaluation_bases(self, stems_actual, stems_predicted):
       
        b_actual = []
        b_predicted = []

        for i in range(0, len(stems_actual)):
            for j in range(0, stems_actual[i][2]):
                b_actual.append(stems_actual[i][0]+j)
                b_actual.append(stems_actual[i][1]-j)
           
        for i in range(0, len(stems_predicted)):
            for j in range(0, stems_predicted[i][2]):
                b_predicted.append(stems_predicted[i][0]+j)
                b_predicted.append(stems_predicted[i][1]-j)
               
        C = 0    # number of correctly identified bases that are paired
        M = 0    # number of the predicted paired bases missing from the known structure
        I = 0    # number of non-predicted paired bases present in the known structure

        for i in range(0, len(b_predicted)):
            if b_predicted[i] in b_actual:
                C += 1
            else:
                M += 1

        for i in range(0, len(b_actual)):
            if b_actual[i] not in b_predicted:
                I += 1
               
        sensitivity = C/(C+M)
        specificity = C/(C+I)

        return specificity, sensitivity
       

    def _parse_pseudoknot(self, ctList):
        """
        ctList              -- paired-bases: [(3, 8), (4, 7)]

        Parse pseusoknots from clList
        Return:
            [ [(3, 8), (4, 7)], [(3, 8), (4, 7)], ... ]
        """
        ctList.sort(key=lambda x:x[0])
        ctList = [ it for it in ctList if it[0]<it[1] ]
        paired_bases = set()
        for lb,rb in ctList:
            paired_bases.add(lb)
            paired_bases.add(rb)

        # Collect duplex
        duplex = []
        cur_duplex = [ ctList[0] ]
        for i in range(1, len(ctList)):
            bulge_paired = False
            for li in range(ctList[i-1][0]+1, ctList[i][0]):
                if li in paired_bases:
                    bulge_paired = True
                    break
            if ctList[i][1]+1>ctList[i-1][1]:
                bulge_paired = True
            else:
                for ri in range(ctList[i][1]+1, ctList[i-1][1]):
                    if ri in paired_bases:
                        bulge_paired = True
                        break
            if bulge_paired:
                duplex.append(cur_duplex)
                cur_duplex = [ ctList[i] ]
            else:
                cur_duplex.append(ctList[i])
        if cur_duplex:
            duplex.append(cur_duplex)

        # Discriminate duplex are pseudoknot
        Len = len(duplex)
        incompatible_duplex = []
        for i in range(Len):
            for j in range(i+1, Len):
                bp1 = duplex[i][0]
                bp2 = duplex[j][0]
                if bp1[0]<bp2[0]<bp1[1]<bp2[1] or bp2[0]<bp1[0]<bp2[1]<bp1[1]:
                    incompatible_duplex.append((i, j))

        pseudo_found = []
        while incompatible_duplex:
            # count pseudo
            count = {}
            for l,r in incompatible_duplex:
                count[l] = count.get(l,0)+1
                count[r] = count.get(r,0)+1
            
            # find most possible pseudo
            count = list(count.items())
            count.sort( key=lambda x: (x[1],-len(duplex[x[0]])) )
            possible_pseudo = count[-1][0]
            pseudo_found.append(possible_pseudo)
            i = 0
            while i<len(incompatible_duplex):
                l,r = incompatible_duplex[i]
                if possible_pseudo in (l,r):
                    del incompatible_duplex[i]
                else:
                    i += 1

        pseudo_duplex = []
        for i in pseudo_found:
            pseudo_duplex.append(duplex[i])

        return pseudo_duplex 

    def _ct2dot(self, ctList, length):
        """
        ctList              -- paired-bases: [(3, 8), (4, 7)]
        length              -- Length of structure
        
        Convert ctlist structure to dot-bracket
        [(3, 8), (4, 7)]  => ..((..))..
        """
        dot = ['.']*length
        if len(ctList) == 0:
            return "".join(dot)
        ctList = sorted(ctList, key=lambda x:x[0])
        ctList = [ it for it in ctList if it[0]<it[1] ]
        pseudo_duplex = self._parse_pseudoknot(ctList)
        for l,r in ctList:
            dot[l-1] = '('
            dot[r-1] = ')'
        dottypes = [ '<>', r'{}', '[]' ]
        if len(pseudo_duplex)>len(dottypes):
            print("Warning: too many psudoknot type: %s>%s" % (len(pseudo_duplex),len(dottypes)))
        for i,duplex in enumerate(pseudo_duplex):
            for l,r in duplex:
                dot[l-1] = dottypes[i%3][0]
                dot[r-1] = dottypes[i%3][1]
        return "".join(dot)
    
    def _generate_base_pair(self, lines, fasta_lines):
    
        rna = fasta_lines[1]
            
        stems_actual = []

        sip = False                       # stem in progress?
        sl = 0                            # stem length
        last_line = [0, 0, 0, 0, 0, 0]    # initiate last line

        base_pair = []

        for i in range(0, len(lines)):
            line = lines[i].strip().split()
            # print(line)
            
            if (int(line[4]) != 0 and sip == False):
                sip = True
                temp = [int(line[0]), int(line[4])]
                temp_base = [(int(line[0]), int(line[4]))]
                # print(f"temp is {temp}")
            if (int(line[4]) != 0 and sip == True and (int(last_line[4])-int(line[4]) == 1)):
                temp_base.append((int(line[0]), int(line[4])))
            if (int(line[4]) == 0 and sip == True):
                sip = False
                if temp[1] > temp[0]:
                    stems_actual.append(temp)
                    base_pair = base_pair + temp_base
            if ((int(last_line[4])-int(line[4]) != 1) and int(last_line[4]) != 0  and sip == True):
                if temp[1] > temp[0]:
                    stems_actual.append(temp)
                    base_pair = base_pair + temp_base
                temp = [int(line[0]), int(line[4])]
                temp_base = [(int(line[0]), int(line[4]))]
        
        return base_pair

    def parse_results(self):
        logging.info("parse annealing results")

    def _init_parameters(self):
        logging.info("_init_parameters")
        self.parameters["rna-strand"] = self.rna_data[self.rna_name]["rna_strand"]
        self.parameters["rna-name"] = self.rna_name
        self.parameters["structure"] = {}
        self.parameters["structure"]["actual"] = {}
        self.parameters["structure"]["actual"]["stems"] = self.rna_data[self.rna_name]["actual_stems"]
        self.parameters["structure"]["actual"]["energy"] = self.actual_energy
        self.parameters["structure"]["predict"] = {}
        self.parameters["structure"]["predict"]["stems"] = 0
        self.parameters["structure"]["predict"]["energy"] = 0
        self.parameters["structure"]["predict"]["bp-specificity"] = 0
        self.parameters["structure"]["predict"]["bp-sensitivity"] = 0
        self.parameters["structure"]["predict"]["bases-specificity"] = 0
        self.parameters["structure"]["predict"]["bases-sensitivity"] = 0

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

        model_name = self.raw_result["model_info"]["model_name"]

        pure_model_name_list = model_name[:-1].split(model_name[-1])

        self.data_name = pure_model_name_list[0]
        self.pkp = pure_model_name_list[1]

        return 0

    def _generate_row_data(self, candidate_result):
        # logging.info("generate_optimize_pts model_info={}".format(
        #     self.raw_result["model_info"]))
        f_stems = []
        rna_name = self.rna_name
        stems_p = self.rna_data[rna_name]['potential_stems'][0]
        for j in range(0, len(stems_p)):
            if candidate_result[str(j)] == 1:
                f_stems.append(stems_p[j])
        return f_stems

    def save_file(self, save_name):
        logging.info(f"save_file {save_name}")
        file_save_name = f"{self.rna_name}_{self.method}_{save_name}.json"

        # update_parameters
        with open(file_save_name, "w") as outfile:
            json.dump(self.parameters, outfile)

        logging.info(f"finish save {file_save_name}")

        return file_save_name

    def RNAFoldingView(self, data = 'raw', path = 'rna-data'):
        # construct file name (.fx)
        rna_name = self.rna_name
        file_name = f"{path}/{rna_name}-{data}.fx"

        exists_result = exists(file_name)

        if exists_result == False:
            stems_show = []
            if data == 'raw':
                stems_p = self.rna_data[rna_name]['potential_stems'][0]
                stems_a = self.actual_stems
                for stem_a in stems_a:
                    for stem_p in stems_p:
                        if stem_a == stem_p[:3]:
                            stems_show.append(stem_p)
            else:
                stems_show = self.predicted_stem

            base_pair = []

            for stem in stems_show:
                stem_len = stem[3]
                head = stem[0]
                tail = stem[1]
                for i in range(stem_len):
                    base_pair.append((head+i,tail-i))
            
            logging.info(f"base_pair is {base_pair}")

            rna = self.rna_data[rna_name]['rna_strand']

            rna_len = len(rna)

            dc = self._ct2dot(base_pair, rna_len)

            file_lines = []
            head_name = f'>{rna_name}'
            file_lines.append(head_name)
            file_lines.append(rna)
            file_lines.append(dc)

            f = open(file_name, "w")

            for line in file_lines:
                f.write(line + '\n')
            
            f.close()
        
        bg = forgi.load_rna(file_name, allow_many=False)

        ax,_ = fvm.plot_rna(bg, text_kwargs={"fontweight":"black"}, lighten=0.7,
             backbone_kwargs={"linewidth":3})

        plt.show()