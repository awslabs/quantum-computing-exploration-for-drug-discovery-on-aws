# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

########################################################################################################################
#   The following functions are used to calculate molecules's geometries
########################################################################################################################

import numpy as np
import logging

log = logging.getLogger()
log.setLevel('INFO')


def sub_list(l1, l2):
    result = []
    for n in range(len(l1)):
        result.append(l1[n]-l2[n])
    return result


def add_list(l1, l2):
    result = []
    for n in range(len(l1)):
        result.append(l1[n]+l2[n])
    return result


def rount_list(l):
    result = []
    for n in l:
        result.append(round(n, 4))
    return result


"""
    Return a point rotated about an arbitrary axis in 3D.
    Positive angles are counter-clockwise looking down the axis toward the origin.
    The coordinate system is assumed to be right-hand.
    Arguments: 'axis point 1', 'axis point 2', 'point to be rotated', 'angle of rotation (in radians)' >> 'new point' 
"""


def PointRotate3D(p1, p2, p0, theta):
    #     from point import Point
    from math import cos, sin, sqrt

    # Translate so axis is at origin
    p = sub_list(p0, p1)
    # Initialize point q
    q = [0.0, 0.0, 0.0]
    N = sub_list(p2, p1)
#     Nm = sqrt(N.x**2 + N.y**2 + N.z**2)
    Nm = sqrt(N[0]**2 + N[1]**2 + N[2]**2)

    # Rotation axis unit vector
    n = [N[0]/Nm, N[1]/Nm, N[2]/Nm]

    # Matrix common factors
    c = cos(theta)
    t = (1 - cos(theta))
    s = sin(theta)
    X = n[0]
    Y = n[1]
    Z = n[2]

    # Matrix 'M'
    d11 = t*X**2 + c
    d12 = t*X*Y - s*Z
    d13 = t*X*Z + s*Y
    d21 = t*X*Y + s*Z
    d22 = t*Y**2 + c
    d23 = t*Y*Z - s*X
    d31 = t*X*Z - s*Y
    d32 = t*Y*Z + s*X
    d33 = t*Z**2 + c

    #            |p.x|
    # Matrix 'M'*|p.y|
    #            |p.z|
    q[0] = d11*p[0] + d12*p[1] + d13*p[2]
    q[1] = d21*p[0] + d22*p[1] + d23*p[2]
    q[2] = d31*p[0] + d32*p[1] + d33*p[2]

    # Translate axis and rotated point back to original location
    sum_p = add_list(q, p1)
    final_p = rount_list(sum_p)
    return final_p


def get_idx(var, var_rb_map):
    # 'x_3_2' -> '3' -> '4+5' -> ['4','5']
    return var_rb_map[str(var.split('_')[1])].split('+')


def get_theta(var, theta_option):
    return theta_option[int(var.split('_')[-1])-1]


def get_current_pts(pts_name, pts_dict, mol_data):
    target_pts = []
    for pt in pts_name:
        if pt not in pts_dict.keys():
            atom = mol_data.atom_data[pt]
            pts_info = {}
            pts_info['pts'] = [atom['x'], atom['y'], atom['z']]
            pts_info['idx'] = ([0, 0, 0], [0, 0, 0])
            target_pts.append(pts_info)
        else:
            target_pts.append(pts_dict[pt])
#         if pts_name not in pts_dict[fragment_name].keys():
#             target_pts = fragment_group[fragment_name][pts_name]
#         else:
#             target_pts = pts_dict[fragment_name][pts_name]
    return target_pts


def update_pts(start_pts, end_pts, pts_list, rotate_theta):
    rotate_list = []
    logging.debug("start_pts {}".format(start_pts))
    logging.debug("end_pts {}".format(end_pts))
    logging.debug("pts_list {}".format(pts_list))
    pi = 3.1415926
    for pt in pts_list:
        if pt['idx'] != (start_pts[0]['pts'], end_pts[0]['pts']):
            rotate_list.append(PointRotate3D(
                start_pts[0]['pts'], end_pts[0]['pts'], pt['pts'], rotate_theta/180*pi))
        else:
            logging.debug("avoid same rotate *******")
            rotate_list.append(pt['pts'])
    return rotate_list


def update_pts_dict(target_name, pts_dict, rotate_pts, rotate_bd):
    for cn, target in enumerate(target_name):
        if target not in pts_dict.keys():
            pts_dict[target] = {}
        pts_dict[target] = {}
        pts_dict[target]['pts'] = rotate_pts[cn]
        pts_dict[target]['idx'] = rotate_bd


def calc_distance_between_pts(pts1, pts2):
    pts1_middle = np.array(tuple(list(np.mean(np.array(pts1), axis=0))))
    pts2_middle = np.array(tuple(list(np.mean(np.array(pts2), axis=0))))

#     sum_distance = []
#     for pt_a in pts1:
#         for pt_b in pts2:
#             sum_distance.append(np.linalg.norm(np.array(pt_a)-np.array(pt_b)))

#     return min(sum_distance)

    return np.linalg.norm(pts1_middle-pts2_middle)


def calc_mid_pts(pts, mol_data):
    pts_pos = []
    for pt in pts:
        atom = mol_data.atom_data[pt]
        pts_pos.append([atom['x'], atom['y'], atom['z']])
    return list(np.mean(np.array(pts_pos), axis=0))


def transfer_pts_name(pts):
    return ','.join(list(pts))


def rot_pts_name(pts, var_rb_map):
    rb = []
    for pt in pts:
        rb.append(var_rb_map[str(pt.split('_')[1])])
    return ','.join(rb)


def pts_pos_list(pts_dict_list):
    pts_list = []
    for pt_dict in pts_dict_list:
        pts_list.append(pt_dict['pts'])
    return pts_list


def update_pts_distance(atom_pos_data, rb_set, tor_map, var_rb_map, theta_option, update_local_pts=False, update_distance=False):
    def _gen_pts_pos_list(pt_set, atom_pos_data):
        return [atom_pos_data[pt]['pts'] for pt in pt_set]

    def _gen_pts_list(pt_set, atom_pos_data):
        return [atom_pos_data[pt] for pt in pt_set]
    # rb_set
    if update_local_pts:

        for var_name, affect_tor_pts_set in tor_map.items():
            d = var_name.split('_')[2]
            rb_name = var_rb_map[var_name.split('_')[1]]
            # update points
            start_pts = atom_pos_data[rb_name.split('+')[0]]
            end_pts = atom_pos_data[rb_name.split('+')[1]]
            whole_set = set.union(rb_set['f_1_set'], affect_tor_pts_set)
            gen_pts = _gen_pts_list(whole_set, atom_pos_data)
            theta = theta_option[int(d)-1]
            rotate_list = update_pts([start_pts], [end_pts], gen_pts, theta)
            for pt_name, pt_value in zip(whole_set, rotate_list):
                atom_pos_data[pt_name]['pts'] = pt_value

    distance = None
    if update_distance:
        # calculate distance
        distance = calc_distance_between_pts(_gen_pts_pos_list(
            rb_set['f_0_set'], atom_pos_data), _gen_pts_pos_list(rb_set['f_1_set'], atom_pos_data))

    return distance


def atom_distance_func(rotate_values, mol_data, var_rb_map, theta_option, M):
    # save temp results for pts
    temp_pts_dict = {}

    tor_len = len(rotate_values)
    tor_last_idx = get_idx(rotate_values[tor_len-1], var_rb_map)

    # initial points for distance calculation
    tor_name = rot_pts_name(rotate_values, var_rb_map)
    f_0 = mol_data.bond_graph.sort_ris_data[str(M)][tor_name]['f_0_set']
    f_0_mid = calc_mid_pts(f_0, mol_data)
    f_1 = mol_data.bond_graph.sort_ris_data[str(M)][tor_name]['f_1_set']
    f_1_mid = calc_mid_pts(f_1, mol_data)
    f_1_name = transfer_pts_name(f_1)
    temp_pts_dict[f_1_name] = {}
    temp_pts_dict[f_1_name]['pts'] = f_1_mid
    temp_pts_dict[f_1_name]['idx'] = ([0, 0, 0], [0, 0, 0])

    for left_idx in range(tor_len):
        # get rotate theta
        # e.g. ['x_3_2', 'x_4_7'] -> 'x_3_2'
        tor_start_value = rotate_values[left_idx]
        # e.g. 'x_3_2' -> ['4','5']
        tor_start_idx = get_idx(tor_start_value, var_rb_map)
#         # ??
#         tor_start = sort_torsion_group[tor_start_idx]
        # e.g. 'x_3_2' -> 2*pi/D * (2-1)
        rotate_theta = get_theta(tor_start_value, theta_option)
        # rotate points
        # e.g. '4' -> [x,y,z]
        start_name = tor_start_idx[0]
        start_pts = get_current_pts([start_name], temp_pts_dict, mol_data)

        end_name = tor_start_idx[1]
        end_pts = get_current_pts([end_name], temp_pts_dict, mol_data)
        logging.debug("current tor {} with base_idx {} rotate_theta {}".format(
            tor_start_value, tor_start_idx, rotate_theta))

        rot_bond = (start_pts[0]['pts'], end_pts[0]['pts'])

        for right_idx in range(left_idx, tor_len):
            tor_end_value = rotate_values[right_idx]
            tor_end_idx = get_idx(tor_end_value, var_rb_map)
#             tor_end = sort_torsion_group[tor_end_idx]
            logging.debug("update tor {}".format(tor_end_idx))
#             only update min/max pts

            # rotate target min/max pts
            if right_idx != left_idx:
                target_start_name = tor_end_idx[0]
                target_start_pts = get_current_pts(
                    [target_start_name], temp_pts_dict, mol_data)

                target_end_name = tor_end_idx[1]
                target_end_pts = get_current_pts(
                    [target_end_name], temp_pts_dict, mol_data)

                rotate_start_pts = update_pts(
                    start_pts, end_pts, target_start_pts, rotate_theta)
                update_pts_dict([target_start_name],
                                temp_pts_dict, rotate_start_pts, rot_bond)

                rotate_end_pts = update_pts(
                    start_pts, end_pts, target_end_pts, rotate_theta)
                update_pts_dict([target_end_name], temp_pts_dict,
                                rotate_end_pts, rot_bond)

            if int(tor_end_idx[1]) == int(tor_last_idx[1]):
                # update all the pts
                logging.debug("update all pts!!!!!!!!")
                f_1_rotate_pts = get_current_pts(f_1, temp_pts_dict, mol_data)

                end_mid_rotate_pts = update_pts(
                    start_pts, end_pts, f_1_rotate_pts, rotate_theta)
                update_pts_dict(f_1, temp_pts_dict,
                                end_mid_rotate_pts, rot_bond)

#                 fragment_group[target_pts_name]['mid_pts'] = target_mid_rotate_pts

            logging.debug("#########pts_dict {}".format(temp_pts_dict))

    base_pts = []
    base_pts = get_current_pts(f_0, temp_pts_dict, mol_data)

    target_pts = []
    for pt in f_1:
        target_pts.append(temp_pts_dict[pt])
    logging.debug("base pts {}".format(base_pts))
    logging.debug("target pts {} ".format(target_pts))
    distance = calc_distance_between_pts(
        pts_pos_list(base_pts), pts_pos_list(target_pts))

    return distance


def get_same_direction_set(candidate_set, rb_data, rb_name):

    # judge direction
    f_0_set = rb_data[rb_name]['f_0_set']
    f_1_set = rb_data[rb_name]['f_1_set']

    direction_set = 'initial'
    if candidate_set.issubset(f_0_set):
        direction_set = f_0_set
    elif candidate_set.issubset(f_1_set):
        direction_set = f_1_set

    return direction_set


def mol_distance_func(atom_pos_data, check, set):
    max_idx = max([int(num) for num in atom_pos_data.keys()])

    sum_distance = 0

    record_distance = []

    map_set = set

    for left_idx in range(max_idx-1):
        for right_idx in range(left_idx+1, max_idx):
            left_key = str(left_idx+1)
            right_key = str(right_idx+1)

            distance = calc_distance_between_pts([atom_pos_data[left_key]['pts']], [
                                                 atom_pos_data[right_key]['pts']])

            if check == 'initial':
                check_radius_distance = atom_pos_data[left_key]['vdw-radius'] + \
                    atom_pos_data[right_key]['vdw-radius']
                if check_radius_distance > distance:
                    map_set.add((left_key, right_key))
                    logging.debug(
                        f"!!!!!!!!!!!! initial van der waals check fail at {left_key} and {right_key} with check: {check_radius_distance} v.s. real {distance}")
            if check == 'test':
                check_radius_distance = atom_pos_data[left_key]['vdw-radius'] + \
                    atom_pos_data[right_key]['vdw-radius']
                if check_radius_distance > distance and (left_key, right_key) not in map_set:
                    logging.debug(
                        f"!!!!!!!!!!!! found van der waals check fail at {left_key} and {right_key} with check: {check_radius_distance} v.s. real {distance}")

            sum_distance = sum_distance + distance

            record_distance.append(distance)

    return sum_distance, record_distance, map_set
