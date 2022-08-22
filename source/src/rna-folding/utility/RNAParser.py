# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

########################################################################################################################
#   The following class is the parser for different types of molecule files
########################################################################################################################


from biopandas.mol2 import PandasMol2
import pandas as pd
import numpy as np
import re

import logging
import pickle  # nosec
import os

log = logging.getLogger()
log.setLevel('INFO')


class RNAData():

    def __init__(self, rna_folder):
        # split folder
        self.folder = rna_folder
        self.subdirectory = self.folder + '/'

        ct = [f for f in os.listdir(self.subdirectory) if f.endswith('.ct.txt')]
        fasta = [f for f in os.listdir(self.subdirectory) if f.endswith('.fasta.txt')]

        self.rna_files = {}

        for f in fasta:
            self.rna_name = f.split('/')[-1].split('.')[0]
            self.rna_files[self.rna_name] = {}

            self.rna_files[self.rna_name]['fasta_file'] = [f for f in fasta if (f.rfind(self.rna_name) != -1)][0]
            self.rna_files[self.rna_name]['ct_file'] = None if len([ct for ct in ct if (ct.rfind(self.rna_name) != -1)]) == 0 else [ct for ct in ct if (ct.rfind(self.rna_name) != -1)][0]

            with open(self.subdirectory+self.rna_files[self.rna_name]['fasta_file']) as file:
                fasta_lines = file.readlines()
            rna_strand = fasta_lines[1]

            self.rna_files[self.rna_name]['rna_strand'] = rna_strand

            self._get_actual_stems(self.rna_name)

    def get_data(self, data_path, rna_name):
        rna_data = self.load(data_path)
        return rna_data.rna_files[rna_name]
        
    def _get_actual_stems(self, rna_name):
        if (self.rna_files[rna_name]['ct_file'] == None):
            self.rna_files[rna_name]['actual_stems'] = None
        else:
            with open(self.subdirectory+self.rna_files[rna_name]['ct_file']) as file:
                lines = file.readlines()

            rna = self.rna_files[rna_name]['rna_strand']

            stems_actual = []
            sip = False                       # stem in progress?
            sl = 0                            # stem length
            last_line = [0, 0, 0, 0, 0, 0]    # initiate last line

            for i in range(0, len(lines)):
                line = lines[i].strip().split()
                if (int(line[4]) != 0 and sip == False):
                    sip = True
                    temp = [int(line[0]), int(line[4])]
                    if (rna[i] == ('G' or 'g') and rna[int(line[4])-1] == ('C' or 'c')) or (rna[i] == ('C' or 'c') and rna[int(line[4])-1] == ('G' or 'g')):
                        sl += 3
                    if (rna[i] == ('G' or 'g') and rna[int(line[4])-1] == ('U' or 'u')) or (rna[i] == ('U' or 'u') and rna[int(line[4])-1] == ('G' or 'g')) or (rna[i] == ('A' or 'a') and rna[int(line[4])-1] == ('U' or 'u')) or (rna[i] == ('U' or 'u') and rna[int(line[4])-1] == ('A' or 'a')):
                        sl += 2
                if (int(line[4]) != 0 and sip == True and (int(last_line[4])-int(line[4]) == 1)):
                    if (rna[i] == ('G' or 'g') and rna[int(line[4])-1] == ('C' or 'c')) or (rna[i] == ('C' or 'c') and rna[int(line[4])-1] == ('G' or 'g')):
                        sl += 3
                    if (rna[i] == ('G' or 'g') and rna[int(line[4])-1] == ('U' or 'u')) or (rna[i] == ('U' or 'u') and rna[int(line[4])-1] == ('G' or 'g')) or (rna[i] == ('A' or 'a') and rna[int(line[4])-1] == ('U' or 'u')) or (rna[i] == ('U' or 'u') and rna[int(line[4])-1] == ('A' or 'a')):
                        sl += 2
                if (int(line[4]) == 0 and sip == True):
                    sip = False
                    temp.append(sl)
                    if temp[1] > temp[0]:
                        stems_actual.append(temp)
                    sl = 0
                if ((int(last_line[4])-int(line[4]) != 1) and int(last_line[4]) != 0  and sip == True):
                    temp.append(sl)
                    if temp[1] > temp[0]:
                        stems_actual.append(temp)
                    temp = [int(line[0]), int(line[4])]
                    sl = 0
                    if (rna[i] == ('G' or 'g') and rna[int(line[4])-1] == ('C' or 'c')) or (rna[i] == ('C' or 'c') and rna[int(line[4])-1] == ('G' or 'g')):
                        sl = 3
                    if (rna[i] == ('G' or 'g') and rna[int(line[4])-1] == ('U' or 'u')) or (rna[i] == ('U' or 'u') and rna[int(line[4])-1] == ('G' or 'g')) or (rna[i] == ('A' or 'a') and rna[int(line[4])-1] == ('U' or 'u')) or (rna[i] == ('U' or 'u') and rna[int(line[4])-1] == ('A' or 'a')):
                        sl = 2
                
                last_line = line
                
            self.rna_files[rna_name]['actual_stems'] = stems_actual

    def save(self, version, path=None):
        save_path = None
        save_name = f"rna-folding_data_{version}.pickle"

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
