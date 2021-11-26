import boto3
import os
from collections import defaultdict

def handler(event, context):
    print(f"event={event}")
    aws_region = os.environ['AWS_REGION']
    param_type = event['param_type']
    s3_bucket = event['s3_bucket']
    devices_arns = [
        'arn:aws:braket:::device/qpu/d-wave/DW_2000Q_6',
        'arn:aws:braket:::device/qpu/d-wave/Advantage_system4'
    ]
    model_params = {
        "M": [1, 2, 3, 4]
    }
    hpc_resources = [
        # vcpu, memory
        (2, 2),
        (4, 4),
        (8, 8),
        (16, 16)
    ]

    if param_type == 'QC_DEVICE_LIST':
        return {
            "devices_arns": devices_arns
        }

    common_param = f"--aws_region,{aws_region},--s3-bucket,{s3_bucket}"

    qc_task_params =defaultdict(list)
    qc_device_names = []
    for device_arn in devices_arns:
        device_name = device_arn.split("/").pop()
        qc_device_names.append(device_name)
        for (param_name, param_values) in model_params.items():
            for param_value in param_values:
                qc_task_params[device_arn].append({
                    "params": f"--{param_name},{param_value},--device-arn,{device_arn},{common_param}".split(","),
                    "device_name": device_name,
                    "device_arn": device_arn
                })
    hpc_task_params = []
    for resource in hpc_resources:
        resource_name = f"Vcpu{resource[0]}_Mem{resource[1]}G"
        for (param_name, param_values) in model_params.items():
            for param_value in param_values:
                hpc_task_params.append({
                    "params": f"--{param_name},{param_value},--resource,{resource_name},{common_param}".split(","),
                    "resource_name": resource_name,
                    "task_name": f"{resource_name}_{param_value}{param_value}",
                    "vcpus": resource[0],
                    "memory": resource[1] * 1024
                })

    if param_type == 'PARAMS_FOR_QC_DEVICE':
        device_arn = event['device_arn']
        print(f"device_arn={device_arn}")
        if device_arn not in devices_arns:
            raise ValueError(f"unknown device_arn: {device_arn}")

        print(qc_task_params)
        return {
            "qcTaskParams":  qc_task_params[device_arn]
        }

    if param_type == 'PARAMS_FOR_HPC':
        return {
            "hpcTaskParams": hpc_task_params
        }
