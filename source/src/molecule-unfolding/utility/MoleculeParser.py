########################################################################################################################
#   The following class is the parser for different types of molecule files
########################################################################################################################


from biopandas.mol2 import PandasMol2
import pandas as pd
import numpy as np
import re

import logging

from .GraphModel import BuildMolGraph


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
            self.bond_graph = BuildMolGraph(self.bond,self.atom_num)
        else:
            logging.error("file type {} not supported! only support mol2,pdb".format(file_type))
            raise Exception("file type not supported!")
    
    def bond_parset(self, filename):
        with open(filename, 'r') as f:
            f_text = f.read()
    #     print(f_text)
        search_result = re.search(r'@<TRIPOS>BOND([a-z0-9\s]*)', f_text)
    #     print("research result {}".format(search_result))
        group_result = search_result.group(1)
    #     print("group result {}".format(group_result))
        bonds =  np.array(re.sub(r'\s+', ' ', re.search(r'@<TRIPOS>BOND([a-z0-9\s]*)', f_text).group(1)).split()).reshape((-1, 4))

        df_bonds = pd.DataFrame(bonds, columns=['bond_id', 'atom1', 'atom2', 'bond_type'])
        df_bonds.set_index(['bond_id'], inplace=True)
        return df_bonds
    
    def atom_parset(self):
        self.mol.df['atom_id'] = self.mol.df.atom_id.astype('str')
        return self.mol.df.set_index('atom_id').T.to_dict('dict')