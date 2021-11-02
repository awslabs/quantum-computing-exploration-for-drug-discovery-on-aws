import argparse
import logging

import boto3
import dimod
import numpy as np
# experiment for biopandas
from biopandas.pdb import PandasPdb
from braket.aws import AwsSession
from braket.ocean_plugin import BraketDWaveSampler
from dwave.system.composites import EmbeddingComposite
import time

logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                    datefmt='%Y-%m-%d:%H:%M:%S',
                    level=logging.INFO)

timestamp=int(time.time())

sum_log = []

DEFAULT_DEVICE_ARN = 'arn:aws:braket:::device/qpu/d-wave/Advantage_system1'
DEFAULT_M = 4
DEFAULT_D = 4
DEFAULT_AWS_REGION = 'us-east-1'

parser = argparse.ArgumentParser()
parser.add_argument('--s3-bucket', type=str)
parser.add_argument('--M', type=int, default=DEFAULT_M)
parser.add_argument('--D', type=int, default=DEFAULT_D)
parser.add_argument('--device-arn', type=str, default=DEFAULT_DEVICE_ARN)
parser.add_argument('--aws-region', type=str, default=DEFAULT_AWS_REGION)
parser.add_argument('--instance-type', type=str, default="EC2")

args, _ = parser.parse_known_args()

M = args.M
D = args.D
device_arn = args.device_arn
aws_region = args.aws_region
instance_type = args.instance_type
my_bucket = args.s3_bucket

logging.info("s3_bucket: {}, aws_region: {}, M: {}, D: {}, device_arn: {}, instance_type: {}".format(my_bucket, aws_region, M, D, device_arn, instance_type))

device_name = device_arn.split("/")[-1]

content_prefix = "{},{},{},{}".format(M, D, device_name, instance_type)


my_prefix = "annealer-experiment"  # the name of the folder in the bucket

boto3.setup_default_session(region_name=aws_region)
boto_sess = boto3.Session(region_name=aws_region)
aws_session = AwsSession(boto_session=boto_sess)
s3_client = boto3.client('s3')

# response = s3_client.list_buckets()
# logging.info("response list_buckets: {}".format(response))

logging.info("s3_folder: s3://{}/{}".format(my_bucket, my_prefix))

def residue_func(row):
    return row['residue_name'] + '_' + str(row['residue_number'])


ligand = PandasPdb().read_pdb('./peptide.pdb')
ligand_pddf = ligand.df['ATOM']
ligand_pddf['residue_name'] = ligand_pddf.apply(lambda row: residue_func(row), axis=1)
ligand_pddf.head()

# parameters for experiments
# num shots for classic
n_c = 1000
# num shots for quantum
n_q = 1000


# M = len(sort_torsion_group)
# M = 4
# resolution = 360/8
# D = 8


def sub_list(l1, l2):
    result = []
    for n in range(len(l1)):
        result.append(l1[n] - l2[n])
    return result


def add_list(l1, l2):
    result = []
    for n in range(len(l1)):
        result.append(l1[n] + l2[n])
    return result


def rount_list(l):
    result = []
    for n in l:
        result.append(round(n, 4))
    return result


def string_to_s3(content):
    file_name = "T{}_M{}_D{}_{}_{}.csv".format(timestamp, M, D, device_name, instance_type)
    key = "{}/metric/{}".format(my_prefix, file_name)
    s3 = boto3.client('s3')
    s3.put_object(
        Body=content.encode("utf-8"),
        Bucket=my_bucket,
        Key=key
    )
    logging.info("put file s3://{}/{}".format(my_bucket, key))



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
    Nm = sqrt(N[0] ** 2 + N[1] ** 2 + N[2] ** 2)

    # Rotation axis unit vector
    n = [N[0] / Nm, N[1] / Nm, N[2] / Nm]

    # Matrix common factors     
    c = cos(theta)
    t = (1 - cos(theta))
    s = sin(theta)
    X = n[0]
    Y = n[1]
    Z = n[2]

    # Matrix 'M'
    d11 = t * X ** 2 + c
    d12 = t * X * Y - s * Z
    d13 = t * X * Z + s * Y
    d21 = t * X * Y + s * Z
    d22 = t * Y ** 2 + c
    d23 = t * Y * Z - s * X
    d31 = t * X * Z - s * Y
    d32 = t * Y * Z + s * X
    d33 = t * Z ** 2 + c

    #            |p.x|
    # Matrix 'M'*|p.y|
    #            |p.z|
    q[0] = d11 * p[0] + d12 * p[1] + d13 * p[2]
    q[1] = d21 * p[0] + d22 * p[1] + d23 * p[2]
    q[2] = d31 * p[0] + d32 * p[1] + d33 * p[2]

    # Translate axis and rotated point back to original location
    sum_p = add_list(q, p1)
    final_p = rount_list(sum_p)
    return final_p


# stats about num for each atom group
# https://stackoverflow.com/questions/46498118/pandas-use-one-column-for-groupby-and-get-stats-for-multiple-other-columns
ligand_number_pddf = ligand_pddf[['atom_number', 'residue_name']].groupby('residue_name').agg(['min', 'max'])
ligand_number_pddf.columns = ligand_number_pddf.columns.map('{0[0]}_{0[1]}'.format)
ligand_number_pddf = ligand_number_pddf.reset_index()
atom_list = ligand_number_pddf['residue_name'].values
ligand_number_pddf.head()

# get torsion group
atom_number_min = {}
atom_number_max = {}
torsion_group = {}

for index, row in ligand_number_pddf.iterrows():
    # update data dict
    atom_number_min[row['atom_number_min']] = row['residue_name']
    atom_number_max[row['atom_number_max']] = row['residue_name']

for k, v in atom_number_min.items():
    max_candidate = k - 1
    if max_candidate in atom_number_max.keys():
        torsion_name = [atom_number_max[max_candidate], v]
        torsion_group[max_candidate] = torsion_name

sort_torsion_group = sorted(torsion_group.items())

logging.info("sort_torsion_group={}".format(len(sort_torsion_group)))

# construct fragment group
fragment_group = {}


def get_pts(name, ligand):
    atom_pddf = ligand.loc[(ligand['residue_name'] == name)]

    max_idx = max(atom_pddf['atom_number'])
    pts_len = len(atom_pddf)
    min_idx = max_idx - pts_len + 1

    max_pts = []
    max_pts.append(float(atom_pddf[atom_pddf['atom_number'] == max_idx]['x_coord'].values[0]))
    max_pts.append(float(atom_pddf[atom_pddf['atom_number'] == max_idx]['y_coord'].values[0]))
    max_pts.append(float(atom_pddf[atom_pddf['atom_number'] == max_idx]['z_coord'].values[0]))

    min_pts = []
    min_pts.append(float(atom_pddf[atom_pddf['atom_number'] == min_idx]['x_coord'].values[0]))
    min_pts.append(float(atom_pddf[atom_pddf['atom_number'] == min_idx]['y_coord'].values[0]))
    min_pts.append(float(atom_pddf[atom_pddf['atom_number'] == min_idx]['z_coord'].values[0]))

    mid_pts = []

    for idx in range(min_idx + 1, max_idx):
        current_pts = []
        current_pts.append(float(atom_pddf[atom_pddf['atom_number'] == idx]['x_coord'].values[0]))
        current_pts.append(float(atom_pddf[atom_pddf['atom_number'] == idx]['y_coord'].values[0]))
        current_pts.append(float(atom_pddf[atom_pddf['atom_number'] == idx]['z_coord'].values[0]))
        mid_pts.append(current_pts)

    return min_idx, max_idx, range(min_idx + 1, max_idx), min_pts, max_pts, mid_pts


for tor in sort_torsion_group:
    first_red_idx = tor[0]
    first_red_name = tor[1][0]
    second_red_name = tor[1][1]
    if first_red_name not in fragment_group.keys():
        min_idx, max_idx, mid_idx, min_pts, max_pts, mid_pts = get_pts(first_red_name, ligand_pddf)
        initial_value = {}
        initial_value['min_pts'] = [min_pts]
        initial_value['mid_pts'] = mid_pts
        initial_value['max_pts'] = [max_pts]
        initial_value['min_idx'] = [min_idx]
        initial_value['mid_idx'] = mid_idx
        initial_value['max_idx'] = [max_idx]
        fragment_group[first_red_name] = initial_value

    if second_red_name not in fragment_group.keys():
        min_idx, max_idx, mid_idx, min_pts, max_pts, mid_pts = get_pts(second_red_name, ligand_pddf)
        initial_value = {}
        initial_value['min_pts'] = [min_pts]
        initial_value['mid_pts'] = mid_pts
        initial_value['max_pts'] = [max_pts]
        initial_value['min_idx'] = [min_idx]
        initial_value['mid_idx'] = mid_idx
        initial_value['max_idx'] = [max_idx]
        fragment_group[second_red_name] = initial_value


def get_idx(var):
    return int(var.split('_')[1]) - 1


def get_theta(var, theta_option):
    return theta_option[int(var.split('_')[-1]) - 1]


def get_current_pts(fragment_name, fragment_group, pts_name, pts_dict):
    target_pts = []
    if fragment_name not in pts_dict.keys():
        target_pts = fragment_group[fragment_name][pts_name]
    else:
        if pts_name not in pts_dict[fragment_name].keys():
            target_pts = fragment_group[fragment_name][pts_name]
        else:
            target_pts = pts_dict[fragment_name][pts_name]
    return target_pts


def update_pts(start_pts, end_pts, pts_list, rotate_theta):
    rotate_list = []
    logging.debug("start_pts {}".format(start_pts))
    logging.debug("end_pts {}".format(end_pts))
    logging.debug("pts_list {}".format(pts_list))
    pi = 3.1415926
    for pt in pts_list:
        rotate_list.append(PointRotate3D(start_pts[0], end_pts[0], pt, rotate_theta / 180 * pi))
    return rotate_list


def update_pts_dict(target_name, pts_name, pts_dict, rotate_pts):
    if target_name not in pts_dict.keys():
        pts_dict[target_name] = {}
    pts_dict[target_name][pts_name] = rotate_pts


def calc_distance_between_pts(pts1, pts2):
    pts1_middle = np.array(tuple(list(np.mean(np.array(pts1), axis=0))))
    pts2_middle = np.array(tuple(list(np.mean(np.array(pts2), axis=0))))
    return np.linalg.norm(pts1_middle - pts2_middle)


def calc_distance_func(rotate_values, sort_torsion_group, fragment_group, theta_option):
    # save temp results for pts
    temp_pts_dict = {}

    tor_base_idx = get_idx(rotate_values[0])
    tor_len = len(rotate_values)
    tor_target_idx = get_idx(rotate_values[tor_len - 1])

    current_start_idx = []

    for left_idx in range(tor_len):
        # get rotate theta
        tor_start_value = rotate_values[left_idx]
        tor_start_idx = get_idx(tor_start_value)
        tor_start = sort_torsion_group[tor_start_idx]
        rotate_theta = get_theta(tor_start_value, theta_option)
        # rotate points
        start_name = tor_start[1][0]
        start_pts = get_current_pts(start_name, fragment_group, 'max_pts', temp_pts_dict)

        end_name = tor_start[1][1]
        end_pts = get_current_pts(end_name, fragment_group, 'min_pts', temp_pts_dict)
        logging.debug(
            "current tor {} with base_idx {} rotate_theta {}".format(tor_start_value, tor_start_idx, rotate_theta))

        for right_idx in range(left_idx, tor_len):
            tor_end_value = rotate_values[right_idx]
            tor_end_idx = get_idx(tor_end_value)
            tor_end = sort_torsion_group[tor_end_idx]
            logging.debug(
                "update tor  {}, tor_end_id is {}, tor_target_idx is {}".format(tor_end, tor_end_idx, tor_end_idx))
            #             only update min/max pts

            # rotate target min/max pts
            end_name = tor_end[1][1]

            end_min_pts = get_current_pts(end_name, fragment_group, 'min_pts', temp_pts_dict)
            end_max_pts = get_current_pts(end_name, fragment_group, 'max_pts', temp_pts_dict)

            end_min_rotate_pts = update_pts(start_pts, end_pts, end_min_pts, rotate_theta)
            end_max_rotate_pts = update_pts(start_pts, end_pts, end_max_pts, rotate_theta)

            update_pts_dict(end_name, 'min_pts', temp_pts_dict, end_min_rotate_pts)
            update_pts_dict(end_name, 'max_pts', temp_pts_dict, end_max_rotate_pts)

            if int(tor_end_idx) == int(tor_target_idx):
                # update all the pts
                logging.debug("update all pts!!!!!!!!")
                mid_pts = get_current_pts(end_name, fragment_group, 'mid_pts', temp_pts_dict)
                end_mid_rotate_pts = update_pts(start_pts, end_pts, mid_pts, rotate_theta)

                #                 fragment_group[target_pts_name]['mid_pts'] = target_mid_rotate_pts
                update_pts_dict(end_name, 'mid_pts', temp_pts_dict, end_mid_rotate_pts)

            logging.debug("#########pts_dict {}".format(temp_pts_dict))

    base_name = sort_torsion_group[tor_base_idx][1][0]
    target_name = sort_torsion_group[tor_target_idx][1][1]
    base_pts = fragment_group[base_name]['mid_pts'] + fragment_group[base_name]['min_pts'] + fragment_group[base_name][
        'max_pts']
    target_pts = temp_pts_dict[target_name]['mid_pts'] + temp_pts_dict[target_name]['min_pts'] + \
                 temp_pts_dict[target_name]['max_pts']
    logging.debug("base pts {}".format(base_pts))
    logging.debug("target pts {} ".format(target_pts))
    distance = calc_distance_between_pts(base_pts, target_pts)

    return distance


# Torsion（m）；Options for score（d）
# Variables （v = m * d）
# initial variable string
theta_option = [x * 360 / D for x in range(D)]
var = {}

for m in range(M):
    x_d = {}
    for d in range(D):
        x_d[d + 1] = 'x_{}_{}'.format(m + 1, d + 1)
    var[m + 1] = x_d

# initial constraint 
A = 10000
hubo = {}
for m in range(M):
    for d1 in range(D):
        var_1 = var[m + 1][d1 + 1]
        for d2 in range(D):
            var_2 = var[m + 1][d2 + 1]
            if (var_2, var_1) in hubo.keys():
                hubo[(var_2, var_1)] = hubo[(var_2, var_1)] + A
            elif var_1 == var_2:
                hubo[(var_1,)] = -A
            else:
                hubo[(var_1, var_2)] = A

# initial distance function: D_a_b
hubo_distances = {}
# fragment num
F = M + 1


def update_hubo(tor_group, up_list):
    if len(tor_group) == 1:
        #         logging.info(tor_group)
        for d in range(D):
            final_list = up_list + [var[tor_group[0]][d + 1]]
            # distance
            hubo_distances[tuple(final_list)] = -calc_distance_func(tuple(final_list), sort_torsion_group,
                                                                    fragment_group, theta_option)
    else:
        for d in range(D):
            final_list = up_list + [var[tor_group[0]][d + 1]]
            update_hubo(tor_group[1:], final_list)


for a in range(F):
    for b in range(a + 1, F):
        logging.info("fragment {}-{}".format(a, b))
        start_pos = a
        end_pos = b - a
        torsion_group = []
        while (end_pos > 0):
            torsion_pos = start_pos + 1
            #             logging.info("torsion {}".format(torsion_pos))
            start_pos = start_pos + 1
            end_pos = end_pos - 1
            torsion_group.append(torsion_pos)
        logging.info("torsion group {}".format(torsion_group))
        # update hubo
        update_hubo(torsion_group, [])

hubo.update(hubo_distances)

qubo = dimod.make_quadratic(hubo, 5, dimod.BINARY)

import time

start = time.time()
# set parameters
num_shots = n_c
# vartype = dimod.SPIN

# # run classical simulated annealing
# model = dimod.BinaryQuadraticModel(linear, quadratic, offset, vartype)
sampler = dimod.SimulatedAnnealingSampler()
response = sampler.sample(qubo, num_reads=num_shots)

# print results
logging.info(response)

end = time.time()

t_sum_classic = (end - start) / 60

logging.info("elapsed time for sa of {} shots: {} min".format(num_shots, t_sum_classic))

response_aggregate = response.aggregate()

# Please enter the S3 bucket you created during onboarding
# (or any other S3 bucket starting with 'amazon-braket-' in your account) in the code below

s3_folder = (my_bucket, my_prefix)
# set parameters
num_reads = n_q

start = time.time()
# run BQM: solve with the D-Wave 2000Q device
# sampler = BraketDWaveSampler(s3_folder,'arn:aws:braket:::device/qpu/d-wave/DW_2000Q_6')

logging.info("the sum time for sa {}".format(t_sum_classic))
sum_log.append("{},sa,{}".format(content_prefix, t_sum_classic))

logging.info("BraketDWaveSampler start - {}".format(content_prefix))

t_sum_quantum = -1
try:
   sampler = BraketDWaveSampler(s3_folder, device_arn, aws_session=aws_session)
   #sampler = BraketDWaveSampler(s3_folder, device_arn)
   end = time.time()
   t1 = (end - start) / 60
   logging.info("elapsed time for init sampler {} min".format(t1))
   
   start = time.time()
   sampler = EmbeddingComposite(sampler)
   end = time.time()
   t2 = (end - start) / 60
   logging.info("elapsed time for embedding generation {} min".format(t2))
   
   start = time.time()
   sampleset = sampler.sample(qubo, num_reads=num_reads)
   end = time.time()
   t3 = (end - start) / 60
   logging.info("elapsed time for d wave of {} shots: {} min".format(num_shots, t3))
   
   t_sum_quantum = t1 + t2 + t3

   logging.info("the sum time for qa {}".format(t_sum_quantum))
   sum_log.append("{},qa,{}".format(content_prefix, t_sum_quantum))

except Exception as err:
    logging.error(repr(err)) 
    pass 

string_to_s3("\n".join(sum_log))
