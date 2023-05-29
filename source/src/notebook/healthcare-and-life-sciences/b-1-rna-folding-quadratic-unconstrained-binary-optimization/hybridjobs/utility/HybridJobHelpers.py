# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from braket.aws import AwsDevice
from braket.aws import AwsSession

import os
import boto3

import copy

c = copy.deepcopy

def obtain_default_bucket(target: str) -> str:
    with open(os.path.abspath('../..') + '/.default-setting') as f:
        lines = f.readlines()
        for line in lines:
            if (line.startswith(target+'=')):
                return line.split('=')[1].strip()

def get_key(single_dict):
    for k in single_dict.keys():
        return k

def parse_params(params_list, hp, hp_list):
    params = params_list[0]
    k = get_key(params)
    ps = params[k]
    for p in ps:
        hp[k] = p
        if len(params_list) == 1:
            hp_list.append(c(hp))
        else:
            parse_params(params_list[1:], hp, hp_list)

def get_quantum_device(device_name):
    device_arn = "arn:aws:braket:::device/quantum-simulator/amazon/sv1"
    try:
        device = AwsDevice.get_devices(names=[device_name])
        device_arn = device[0].arn
    except Exception as e:
        print(f"fail to get {device_name}: {e}, use sv1 instead")
    return device_arn

def upload_data(dir_name, suffix_check, aws_session=AwsSession()):
    stream_s3_uri = aws_session.construct_s3_uri(obtain_default_bucket("bucketName"), dir_name)
    return_path = None
    
    def _check_upload(file_name, check_list):
        file_end = file_name.split('.')[-1]
        if file_end in check_list:
            path = f"{stream_s3_uri}/" + file_name.split('/')[-1]
            aws_session.upload_to_s3(file_name, path)
            
    if os.path.isdir(dir_name):
        dir_list = os.listdir(dir_name)
        for file_name in dir_list:
            _check_upload(os.path.join(dir_name,file_name), suffix_check)
        return_path = stream_s3_uri
    else:
        _check_upload(file_name, suffix_check)
        single_file_name = file_name.split('/')[-1]
        return_path = f"{stream_s3_uri}/{single_file_name}"
        
    return return_path

def queue_check(jobs):
    # check current running or queued jobs
    region = boto3.client('s3').meta.region_name
    braket = boto3.client("braket", region_name=region)
    p = braket.get_paginator("search_jobs")
    paginator = p.paginate(filters=[]).build_full_result()
    
    existing_job_count = 0
    if "jobs" in paginator:
        for job in paginator["jobs"]:
            if job["status"] in ["RUNNING", "QUEUED"]:
                existing_job_count = existing_job_count + 1
    
    check_pass = True
    if existing_job_count >= 4:
        check_pass = False
    
    print(f"There are {existing_job_count} jobs in RUNNING or QUEUED status")
    
    return check_pass

def get_result(result, target, dm):
    return [dm, result["time"], target]

def get_dm(target):
    file_name = './rna-folding-data/' + target + '.fasta.txt'
    str_len = -100
    with open(file_name) as file:
        fasta_lines = file.readlines()
        str_len = len(fasta_lines[1])
    return str_len

def display_results(results, experiments_params):
    sorted_results = {}
    
    for device in experiments_params["params"][4]["device"]:
        sorted_results[str(device)] = []
        # for target in results[0].keys():
        #     sorted_results[str(device)][target] = []
    
    max_offset = 10
    for result in results:
        for target in result.keys():
            device = result[target]["hypermeter"]["device"]
            
            dm = get_dm(target)

            if len(sorted_results[device]) == 0:
                sorted_results[device].append(get_result(result[target],target,dm))
                continue

            last_idx = 0
            for idx, sorted_result in enumerate(sorted_results[device]):
                sorted_dm = float(sorted_result[0])

                last_sorted_dm = float(sorted_results[device][last_idx][0])

                if last_sorted_dm < dm and dm < sorted_dm:
                    sorted_results[device].insert(idx,get_result(result[target],target,dm))
                    break
                elif dm < last_sorted_dm and idx == 0:
                    sorted_results[device].insert(last_idx,get_result(result[target],target,dm))
                    break
                elif dm > sorted_dm and idx == len(sorted_results[device])-1:
                    sorted_results[device].insert(idx+1,get_result(result[target],target,dm))

                last_idx = idx
    # print(f"sorted result {sorted_results}")
    return sorted_results