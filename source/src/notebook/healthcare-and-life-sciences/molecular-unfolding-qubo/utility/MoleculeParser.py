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

from .GraphModel import BuildMolGraph

log = logging.getLogger()
log.setLevel('INFO')


class MoleculeData():

    def __init__(self, mol_file, function, name=None):
        # parse file
        self.mol = None
        self.name = None
        file_type = mol_file.split('.')[-1]

        if name == None:
            self.name = mol_file.split('/')[-1].split('.')[0]
        else:
            self.name = name

        if file_type == 'mol2':
            logging.info("parse mol2 file!")
            self.mol = PandasMol2().read_mol2(mol_file)
            self.bond = self.bond_parset(mol_file)

            self.atom_num = self.mol.df['atom_id'].max()
            self.atom_data = self.atom_parset()
            self._add_van_der_waals()
            self.bond_graph = BuildMolGraph(self.bond, self.atom_num)
        else:
            logging.error(
                "file type {} not supported! only support mol2,pdb".format(file_type))
            raise Exception("file type not supported!")

    def _add_van_der_waals(self):
        # https://en.wikipedia.org/wiki/Van_der_Waals_radius
        van_der_waals_dict = {'H': 1.2, 'C': 1.7, 'N': 1.55,
                              'O': 1.52, 'F': 1.47, 'S': 1.8, 'Ch': 1.75, 'Co': 1.4, 'Cl': 1.75}

        def _parse_atom(atom_type):
            return atom_type.split('.')[0]

        for pt, info in self.atom_data.items():
            self.atom_data[pt]['vdw-radius'] = van_der_waals_dict[_parse_atom(
                self.atom_data[pt]['atom_type'])]

    def bond_parset(self, filename):
        with open(filename, 'r') as f:
            f_text = f.read()
    #     print(f_text)
        search_result = re.search(r'@<TRIPOS>BOND([a-z0-9\s]*)', f_text)
    #     print("research result {}".format(search_result))
        group_result = search_result.group(1)
    #     print("group result {}".format(group_result))
        bonds = np.array(re.sub(
            r'\s+', ' ', re.search(r'@<TRIPOS>BOND([a-z0-9\s]*)', f_text).group(1)).split()).reshape((-1, 4))

        df_bonds = pd.DataFrame(
            bonds, columns=['bond_id', 'atom1', 'atom2', 'bond_type'])
        df_bonds.set_index(['bond_id'], inplace=True)
        return df_bonds

    def atom_parset(self):
        self.mol.df['atom_id'] = self.mol.df.atom_id.astype('str')
        return self.mol.df.set_index('atom_id').T.to_dict('dict')

    def save(self, version, path=None):
        save_path = None
        save_name = f"qmu_{self.name}_data_{version}.pickle"

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
