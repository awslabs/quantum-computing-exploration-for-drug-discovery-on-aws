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

            self.rna_files[self.rna_name]['potential_stems']= self._potential_stems(rna_strand)

            self._get_actual_stems(self.rna_name)

    def get_data(self, rna_name):
        rna_data = self.load(self.save_path)
        return rna_data.rna_files[rna_name]

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
                        # stem = [row+1,col+1,0]
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
        self.save_path = None
        save_name = f"rna-folding_data_{version}.pickle"

        if path != None:
            self.save_path = os.path.join(path, save_name)
        else:
            self.save_path = os.path.join(".", save_name)

        with open(self.save_path, "wb") as f:
            pickle.dump(self, f)
        logging.info(f"finish save {save_name}")

        return self.save_path

    @classmethod
    def load(cls, filename):
        with open(filename, "rb") as f:
            return pickle.load(f)  # nosec
