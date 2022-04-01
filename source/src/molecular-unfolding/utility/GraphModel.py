# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

########################################################################################################################
#   The following class is the graph model for molecules
########################################################################################################################

import networkx as nx
import math

import logging

log = logging.getLogger()
log.setLevel('INFO')


class BuildMolGraph():

    def __init__(self, df_bonds, atom_num):

        self.df_bonds = df_bonds
        self.atom_num = atom_num

        self.mol_g = nx.Graph()

        self.build_graph()

        self.mol_ug = self.mol_g.to_undirected()

        # use betweenness_centrality to generate rotatabole bonds: self.mol_ug -> rb_list
        self.rb_list = self.build_rb()
        self.rb_data, self.rb_data_list = self.build_rb_data()
        # test only N rb for graph model
        self.sort_ris_data = {}
        for M_cnt, rb_data in enumerate(self.rb_data_list):
            self.sort_ris_data[str(M_cnt+1)] = self.build_ris_data(rb_data)

    def build_graph(self):
        def add_node(nodes_list, node):
            if node not in nodes_list:
                nodes_list.append(node)

        def add_edge(edges_list, edge, rotatable_list, filter_by_type, bond_type):
            if filter_by_type:
                if bond_type != 'ar':
                    rotatable_list.append(edge)
            if edge not in edges_list:
                edges_list.append(edge)

        nodes_list = []
        edges_list = []
        # l_frag
        # r_frag
        # side_atom
        # bc_score
        self.non_ar_bonds = []

        for index, row in self.df_bonds.iterrows():
            logging.debug("atom 1 {} atom 2 {}".format(
                row['atom1'], row['atom2']))
            add_node(nodes_list, row['atom1'])
            add_node(nodes_list, row['atom2'])
            add_edge(edges_list, (row['atom1'], row['atom2']),
                     self.non_ar_bonds, True, row['bond_type'])

        self.mol_g.add_nodes_from(nodes_list)
        self.mol_g.add_edges_from(edges_list)

    def build_rb(self):
        self.bc = nx.betweenness_centrality(self.mol_ug)
        rb_list = []
        for rot in self.non_ar_bonds:
            if math.isclose(self.bc[rot[0]], 0) or math.isclose(self.bc[rot[1]], 0):
                continue
            rb_list.append(rot)
        self.rb_num = len(rb_list)
        return rb_list

    def build_rb_data(self):
        # find L/R fragments
        rb_data = {}
        self.rb_name = []

        def clear_set(src, value):
            for i in range(2):
                if value[i] in src:
                    src.remove(value[i])

        def update_pts_pair(rb_data):
            rb_data['pair_set'] = set()
            for f_0_pt in rb_data['f_0_set']:
                for f_1_pt in rb_data['f_1_set']:
                    pair_pts = (f_0_pt, f_1_pt)
                    if pair_pts not in rb_data['pair_set']:
                        rb_data['pair_set'].add(pair_pts)

        # add list to save invalid rb
        invalid_rb_list = []
        invalid_rb_name_list = []
        for rb in self.rb_list:
            self.mol_ug.remove_edge(rb[0], rb[1])
            current_rb_name = "{}+{}".format(rb[0], rb[1])
            self.rb_name.append(current_rb_name)
        #     print(rb_name)
            if current_rb_name not in rb_data.keys():
                rb_data[current_rb_name] = {}
                i = 0
                for pts in nx.connected_components(self.mol_ug):
                    #             print(pts)
                    update_pts = pts.copy()
                    clear_set(update_pts, rb)
                    rb_data[current_rb_name]['f_{}_set'.format(i)] = update_pts
                    i = i + 1
                if "f_1_set" not in rb_data[current_rb_name].keys():
                    invalid_rb_list.append(rb)
                    invalid_rb_name_list.append(current_rb_name)
                    # print(f"rb_name {current_rb_name} f_0_set {rb_data[current_rb_name]['f_0_set']} with length {len(rb_data[current_rb_name]['f_0_set'])}")
                # update bc score
                rb_data[current_rb_name]['bc_num'] = (
                    self.bc[rb[0]] + self.bc[rb[1]])/2
                # update make pts pair set
        #         update_pts_pair(rb_data[rb_name])
            self.mol_ug.add_edge(rb[0], rb[1])

        for invalid_rb, invalid_rb_name in zip(invalid_rb_list, invalid_rb_name_list):
            self.rb_list.remove(invalid_rb)
            del rb_data[invalid_rb_name]

        sort_rb_data = {k: v for k, v in sorted(
            rb_data.items(), key=lambda rb: -rb[1]['bc_num'])}

        rb_data_list = []
        for rb, data in sort_rb_data.items():
            if len(rb_data_list) == 0:
                current_rb_data = {}
            else:
                current_rb_data = rb_data_list[-1].copy()
            current_rb_data[rb] = data
            rb_data_list.append(current_rb_data)
            logging.debug(rb_data_list)

        return rb_data, rb_data_list

    def build_ris_data(self, rb_data):
        ris_data = {}

        def judge_side_by_metrics(rb_data, candidate_pt):
            if candidate_pt in rb_data['f_0_set']:
                return 0
            if candidate_pt in rb_data['f_1_set']:
                return 1

        def update_bc_info(ris_data_bond, rb_data, bond_group):
            bc_num = []
            for rb in bond_group:
                bc_num.append(rb_data[rb]['bc_num'])
            ris_data_bond['avg_bc_num'] = sum(bc_num)/len(bc_num)
            ris_data_bond['rb_count_num'] = len(bc_num)

        def update_ris_data(ris_data, rb_data, candidate_pair):
            atom_l = candidate_pair[0]
            atom_r = candidate_pair[1]
            bond_group = []
            for rb, pts_data in rb_data.items():
                if (atom_l in pts_data['f_0_set'] and atom_r in pts_data['f_1_set']) or (atom_l in pts_data['f_1_set'] and atom_r in pts_data['f_0_set']):
                    bond_group.append(rb)

            if len(bond_group) == 0:
                return

            bond_name = ','.join(bond_group)

            if bond_name not in ris_data.keys():
                ris_data[bond_name] = {}
                ris_data[bond_name]['metrics'] = bond_group[0]
                ris_data[bond_name]['f_0_set'] = set()
                ris_data[bond_name]['f_1_set'] = set()
                # update bc score
                update_bc_info(ris_data[bond_name], rb_data, bond_group)

            for atom in candidate_pair:
                side = judge_side_by_metrics(
                    rb_data[ris_data[bond_name]['metrics']], atom)
                ris_data[bond_name]['f_{}_set'.format(side)].add(atom)

        for atom_l in range(1, self.atom_num+1):
            for atom_r in range(atom_l+1, self.atom_num+1):
                candidate_pair = (str(atom_l), str(atom_r))
                update_ris_data(ris_data, rb_data, candidate_pair)
        #         print("{}-{}".format(atom_l, atom_r))

        # sorted(ris_data, key=lambda ris: (ris['rb_count_num']))
        # sort by num of bond at first (from small to large)
        # sort by bc_num at second ( from large to small)
        sor_ris_data = {k: v for k, v in sorted(ris_data.items(), key=lambda ris: (
            ris[1]['rb_count_num'], -ris[1]['avg_bc_num']))}
        return sor_ris_data
