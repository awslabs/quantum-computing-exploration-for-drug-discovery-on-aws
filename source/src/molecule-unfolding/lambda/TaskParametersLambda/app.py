import boto3
import os 

def handler(event, context):
    print(f"event={event}")
    aws_region = os.environ['AWS_REGION']
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

    common_param = f"--aws_region,{aws_region},--s3-bucket,{s3_bucket}"

    qc_task_params = []
    for device_arn in devices_arns:
        device_name = device_arn.split("/").pop()
        for (param_name, param_values) in model_params.items():
            for param_value in param_values:
                qc_task_params.append({
                    "params": f"--{param_name},{param_value},--device-arn,{device_arn},{common_param}".split(","),
                    "device_name": device_name
                })
    hpc_task_params = []
    for resource in hpc_resources:
        resource_name = f"Vcpu{resource[0]}_Mem{resource[1]}G"
        for (param_name, param_values) in model_params.items():
            for param_value in param_values:
                hpc_task_params.append({
                    "params": f"--{param_name},{param_value},--resource,{resource_name},{common_param}".split(","),
                    "resource_name": resource_name,
                    "vcpus": resource[0],
                    "memory": resource[1] * 1024
                })
    
    return {
        "qcTaskParams": qc_task_params,
        "hpcTaskParams": hpc_task_params
    }

