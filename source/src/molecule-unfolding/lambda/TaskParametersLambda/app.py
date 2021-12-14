import boto3
import os
from collections import defaultdict
import json
import datetime
import copy

s3 = boto3.client('s3')
default_s3_prefix = "molecule-unfolding"

default_devices_arns = [
    'arn:aws:braket:::device/qpu/d-wave/DW_2000Q_6',
    'arn:aws:braket:::device/qpu/d-wave/Advantage_system4'
]

default_model_params = {
    "M": [1, 2, 3, 4],
    "D": [4],
    "A": [300],
    "HQ": [200]  # hubo_qubo_val
}
default_hpc_resources = [
    # vcpu, memory_in_GB
    [2, 2],
    [4, 4],
    [8, 8],
    [16, 16]
]

default_opt_params = {
    "qa": {
        "shots": 1000,
        "embed_method": "default"
    },
    "sa": {
        "shots": 100,
        "notes": "benchmarking"
    }
}


def read_as_json(bucket, key):
    print(f"read s3://{bucket}/{key}")
    obj = s3.get_object(Bucket=bucket, Key=key)
    json_ = json.loads(obj['Body'].read())
    print(f"return: {json_}")
    return json_


def read_config(s3_bucket, s3_prefix):
    config_file = f"{s3_prefix}/config/default.json"
    config = None
    global default_hpc_resources
    global default_model_params
    global default_devices_arns
    global default_opt_params
    try:
        config = read_as_json(s3_bucket, config_file)

        if 'hpcResources' in config:
            default_hpc_resources = config['hpcResources']
        if 'modelParams' in config:
            default_model_params = config['modelParams']
        if 'devicesArns' in config:
            default_devices_arns = config['devicesArns']
        if 'optParams' in config:
            default_opt_params = config['optParams']
    except Exception as e:
        print(f"cannot find {config_file}")
        pass


def string_to_s3(content, bucket, key):
    s3.put_object(
        Body=content.encode("utf-8"),
        Bucket=bucket,
        Key=key
    )


def read_user_input(execution_id, bucket, s3_prefix):
    key = f"{s3_prefix}/executions/{execution_id}/user_input.json"
    obj = s3.get_object(Bucket=bucket, Key=key)
    input = json.loads(obj['Body'].read())
    print(f"user_input={input}")
    return input


def get_model_param_items(params_dict: dict):
    param_list = []
    for pname in ["M", "D", "A", "HQ"]:
        pvalues = [f"{pname}={v}" for v in params_dict.get(
            pname, default_model_params[pname])]
        param_list.append(pvalues)

    result = get_all_param_list(copy.deepcopy(param_list))
    print(f"get_param_items: {result}")
    return result


def get_all_param_list(param_list):
    first_l = None
    index_i = 0
    has_more_than_one = False
    for i in range(len(param_list)):
        l = param_list[i]
        if len(l) > 1:
            has_more_than_one = True

        if len(l) > 1 and first_l is None:
            first_l = l[0]
            param_list[i] = l[1:]
            index_i = i
    if not has_more_than_one:
        return ["&".join([ll[0] for ll in param_list])]
    else:
        param_list_copy = copy.deepcopy(param_list)
        param_list_copy[index_i] = [first_l]
        reslut_all = []
        result_list0 = get_all_param_list(param_list_copy)
        result_list1 = get_all_param_list(param_list)
        reslut_all.extend(result_list0)
        reslut_all.extend(result_list1)
        return reslut_all


def validate_input(input_dict: dict):
    print('validate_input')
    valid_keys = ['runMode', 'molFile', 'modelVersion', 'optParams',
                  'experimentName', 'modelParams', 'devicesArns', 'hpcResources', 'Comment']
    valid_keys_str = "|".join(valid_keys)
    errors = []

    if '!' in json.dumps(input_dict):
        errors.append("invalid char '!' in input")

    try:
        for k in input_dict.keys():
            if k not in valid_keys:
                errors.append(
                    f"invalid field: {k}, support fields: {valid_keys_str}")

            if 'devicesArns' == k:
                if not isinstance(input_dict[k], list):
                    errors.append(f"devicesArns must be an array")

                for arn in list(input_dict[k]):
                    if arn not in default_devices_arns:
                        errors.append(f"unknown devices arn: {arn}")

            if 'modelParams' == k:
                if not isinstance(input_dict[k], dict):
                    errors.append(f"devicesArns must be a dict")

                param_names = dict(input_dict[k]).keys()
                for p in param_names:
                    if p not in ["M", "D", "A", "HQ"]:
                        errors.append(f"unknown modelParam: {p}")
                    if not isinstance(input_dict[k][p], list):
                        errors.append(
                            f"values of modelParam: {p} must be an array")
                    list_vals = input_dict[k][p]
                    for e in list_vals:
                        if not isinstance(e, int):
                            errors.append(
                                f"invalid value {e}, value for {p} must be int")

            if 'hpcResources' == k:
                if not isinstance(input_dict[k], list):
                    errors.append(f"hpcResources must be an array")
                for c_m in list(input_dict[k]):
                    if not isinstance(c_m, list) or len(c_m) != 2:
                        errors.append(
                            f"element in hpcResources must be an array with size=2")
                    for e in c_m:
                        if not isinstance(e, int):
                            errors.append(
                                f"invalid value {e}, elements for {k} must be int array, {c_m}")
            if 'optParams' == k:
                if not isinstance(input_dict[k], dict):
                    errors.append(f"optParams must be a dict")
                for p in input_dict[k].keys():
                    if p not in ['sa', 'qa']:
                        errors.append(f"invalid key {p} of optParams, values: sa|qa")
                    elif not isinstance(input_dict[k][p], dict):
                        errors.append(f"optParams[{p}] must be a dict")
                    elif 'shots' in input_dict[k][p] and not isinstance(input_dict[k][p]['shots'], int):
                        errors.append(f"optParams[{p}][shots] must be int, value: {input_dict[k][p]['shots']}")


    except Exception as e:
        errors.append(repr(e))

    print(errors)
    return errors


def handler(event, context):
    print(f"event={event}")
    aws_region = os.environ['AWS_REGION']
    param_type = event['param_type']
    s3_bucket = event['s3_bucket']
    s3_prefix = event.get('s3_prefix', default_s3_prefix)

    read_config(s3_bucket, s3_prefix)

    common_param = f"--aws_region,{aws_region},--s3-bucket,{s3_bucket},--s3_prefix,{s3_prefix}"

    if param_type == 'CHECK_INPUT':

        user_input = event['user_input']
        execution_id = event['execution_id']
        execution_id = execution_id.split(':')[-1]

        errs = validate_input(user_input)
        if len(errs) > 0:
            raise Exception("validate error: {}".format("\n".join(errs)))

        # set default optParams
        if user_input.get('optParams', None) is None:
            user_input['optParams'] = default_opt_params
        elif user_input['optParams'].get('sa', None) is None:
            user_input['optParams']['sa'] = default_opt_params['sa']
        elif user_input['optParams'].get('qa', None) is None:
            user_input['optParams']['qa'] = default_opt_params['qa']

        key = f"{s3_prefix}/executions/{execution_id}/user_input.json"
        string_to_s3(content=json.dumps({
            "user_input": user_input,
            "execution_id": execution_id,
            "aws_region": aws_region,
            "start_time": datetime.datetime.utcnow().isoformat(),

        }), bucket=s3_bucket, key=key)
        return {
            "params": f"{common_param},--execution-id,{execution_id}".split(","),
            "execution_id": execution_id,
            "runMode": user_input.get('runMode', "ALL"),
            "start_time": datetime.datetime.utcnow().isoformat(),
            "s3_prefix": s3_prefix
        }
    else:
        execution_id = event.get('execution_id', None)
        if execution_id:
            common_param = f"{common_param},--execution-id,{execution_id}"
            user_input = read_user_input(
                execution_id, bucket=s3_bucket, s3_prefix=s3_prefix)

            devices_arns = user_input['user_input'].get(
                'devicesArns', default_devices_arns)
            model_params = user_input['user_input'].get(
                'modelParams', default_model_params)
            hpc_resources = user_input['user_input'].get(
                'hpcResources', default_hpc_resources)
        else:
            devices_arns = default_devices_arns
            model_params = default_model_params
            hpc_resources = default_model_params

    print(f"devices_arns={devices_arns}")
    print(f"model_params={model_params}")
    print(f"hpc_resources={hpc_resources}")

    if param_type == 'QC_DEVICE_LIST':
        return {
            "devices_arns": devices_arns,
            "execution_id": execution_id
        }

    model_param_items = get_model_param_items(model_params)

    qc_task_params = defaultdict(list)
    qc_device_names = []
    qc_index = 0
    for device_arn in devices_arns:
        device_name = device_arn.split("/").pop()
        qc_device_names.append(device_name)
        for param_item in model_param_items:
            param_item_name = str(param_item).replace(
                "&", '').replace("=", '')
            qc_task_params[device_arn].append({
                "params": f"--model-param,{param_item},--device-arn,{device_arn},--index,{qc_index},{common_param}".split(","),
                "device_name": device_name,
                "task_name": f"{device_name}_{param_item_name}",
                "model_param": param_item,
                "index": qc_index,
                "device_arn": device_arn})

    hpc_task_params = []
    hpc_index = 0
    for resource in hpc_resources:
        resource_name = f"Vcpu{resource[0]}_Mem{resource[1]}G"
        for param_item in model_param_items:
            hpc_index += 1
            param_item_name = str(param_item).replace(
                "&", '').replace("=", '')
            hpc_task_params.append({
                "params": f"--model-param,{param_item},--resource,{resource_name},--index,{hpc_index},{common_param}".split(","),
                "resource_name": resource_name,
                "task_name": f"{resource_name}_{param_item_name}",
                "model_param": param_item,
                "index": hpc_index,
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
            "qcTaskParams":  qc_task_params[device_arn],
            "execution_id": execution_id,
        }

    if param_type == 'PARAMS_FOR_HPC':
        return {
            "hpcTaskParams": hpc_task_params,
            "execution_id": execution_id
        }
