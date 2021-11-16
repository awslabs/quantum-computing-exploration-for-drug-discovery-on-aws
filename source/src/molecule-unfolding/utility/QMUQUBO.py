########################################################################################################################
#   The following class is the construction of QUBO model
########################################################################################################################
import dimod
from .MolGeoCalc import atom_distance_func

import time
import logging


class QMUQUBO():
    
    def __init__(self, mol_data, method, **param):
        
        # prepare parameters
        self.param = param
        M = self.param['M']
        D = self.param['D']
        A = self.param['A']
        hubo_qubo_val = self.param['hubo_qubo_val']
        # prepare variables
        self.var, self.var_rb_map, self.rb_var_map = self.prepare_var(mol_data, D)
        
        self.hubo = {}
        theta_option = [x * 360/D for x in range(D)]
        
        if method == 'pre-calc':
            logging.info("pre-calculate for constructing molecule QUBO")
            hubo_constraints, hubo_distances = self.build_qubo_pre_calc(mol_data, M, D, A, self.var, self.rb_var_map, self.var_rb_map, theta_option)
            self.hubo.update(hubo_constraints)
            self.hubo.update(hubo_distances)
        elif method == 'after-calc':
            logging.info("after calculate for constructing molecule QUBO not implemented !!")
        else:
            logging.info("only pre-calculate(method='pre-calc') and after-calculate(method='after-calc') are supported, \
            method {} not support !!".format(method))
            
        self.qubo = dimod.make_quadratic(self.hubo, hubo_qubo_val, dimod.BINARY)
        
    def prepare_var(self, mol_data, D):
        
        var = {}
        var_rb_map = {}
        rb_var_map = {}
                    
        for m, name in enumerate(mol_data.bond_graph.rb_name):
            x_d = {}
            var_rb_map[str(m+1)] = name
            rb_var_map[str(name)] = str(m+1) 
            for d in range(D):
                x_d[str(d+1)] = 'x_{}_{}'.format(m+1, d+1)
            var[str(m+1)] = x_d
            
        return var, var_rb_map, rb_var_map
        
    def build_qubo_pre_calc(self, mol_data, M, D, A, var, rb_var_map, var_rb_map, theta_option):
        # initial constraint 
        hubo_constraints = {}
        for m in range(M):
            for d1 in range(D):
                var_1 = var[str(m+1)][str(d1+1)]
                for d2 in range(D):
                    var_2 = var[str(m+1)][str(d2+1)]
                    if (var_2, var_1) in hubo_constraints.keys():
                        hubo_constraints[(var_2,var_1)] = hubo_constraints[(var_2, var_1)] + A
                    elif var_1 == var_2:
                        hubo_constraints[(var_1,var_1)] = -A
                    else:
                        hubo_constraints[(var_1,var_2)] = A
        # update distance term
        hubo_distances = {}
        
        def update_hubo(torsion_group, up_list):
            if len(torsion_group) == 1:
        #         print(tor_group)
                for d in range(D):
                    final_list = up_list + [var[rb_var_map[torsion_group[0]]][str(d+1)]]
                    logging.debug("final list {}".format(final_list))
                    # distance
                    final_list_name = []
                    if len(final_list) == 1:
                        final_list_name = final_list + final_list
                    else:
                        final_list_name = final_list
#                     hubo_distances[tuple(final_list_name)] = -1
                    hubo_distances[tuple(final_list_name)] = -atom_distance_func(tuple(final_list), mol_data, var_rb_map, theta_option)
            else:
                for d in range(D):
                    final_list = up_list + [var[rb_var_map[torsion_group[0]]][str(d+1)]]
                    update_hubo(torsion_group[1:], final_list)
        
        torsion_cnt = 1
        
        for ris, ris_data in mol_data.bond_graph.sort_ris_data.items():
            start = time.time()
            logging.debug("ris group {} ".format(ris))
            end = time.time()
            torsion_group = ris.split(',')
            logging.info(torsion_group)
            update_hubo(torsion_group, [])
            logging.info("elasped time for torsion group {} : {} min".format(ris,(end-start)/60))
            if torsion_cnt == M:
                logging.info("finish construct model for {} torsions".format(M))
                break
         
        return hubo_constraints, hubo_distances
            
 


    

    
    
    
    
    
    
    
    
    