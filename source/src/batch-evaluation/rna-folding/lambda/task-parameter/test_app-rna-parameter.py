# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import boto3
import pytest
from moto import mock_s3
import json
import datetime

@mock_s3
def test_handler_QC_DEVICE_LIST(monkeypatch):
    from . import app
    monkeypatch.setenv('AWS_REGION', 'us-east-1')
    event = {
        'param_type': 'QC_DEVICE_LIST',
        's3_bucket': 'test_s3_bucket',
        's3_prefix': 'test_s3_prefix',
        'execution_id': None
    }
    devices = app.handler(event, None)
    assert devices == {'devices_arns': ['arn:aws:braket:::device/qpu/d-wave/DW_2000Q_6',
                                        'arn:aws:braket:::device/qpu/d-wave/Advantage_system4',
                                        'arn:aws:braket:us-west-2::device/qpu/d-wave/Advantage_system6'
                                        ],
                       'execution_id': None}


@mock_s3
def test_handler_CHECK_INPUT_default(monkeypatch):
    boto3.setup_default_session()
    from . import app
    s3 = boto3.client('s3')
    s3.create_bucket(Bucket='test_s3_bucket')
    s3.put_object(
        Body='test'.encode("utf-8"),
        Bucket='test_s3_bucket',
        Key='test-key.json'
    )

    monkeypatch.setenv('AWS_REGION', 'us-east-1')
    monkeypatch.setenv('AWS_ACCESS_KEY_ID', 'fake')
    monkeypatch.setenv('AWS_SECRET_ACCESS_KEY', 'fake')

    event = {
        'param_type': 'CHECK_INPUT',
        's3_bucket': 'test_s3_bucket',
        's3_prefix': 'test_s3_prefix',
        'execution_id': 'arn:aws:states:us-west-2:123456789000:execution:MolUnfBatchEvaluationBatchEvaluationStateMachine759181D6-smNpiWdkgrOI:test_execution_id',
        'user_input': {}
    }

    app.handler(event, None)
    assert True


@mock_s3
def test_handler_CHECK_INPUT_full_input(monkeypatch):
    boto3.setup_default_session()
    from . import app
    monkeypatch.setenv('AWS_REGION', 'us-east-1')
    s3 = boto3.client('s3', region_name='us-east-1')
    s3.create_bucket(Bucket='test_s3_bucket')

    event = {
        'param_type': 'CHECK_INPUT',
        's3_bucket': 'test_s3_bucket',
        's3_prefix': 'test_s3_prefix',
        'execution_id': 'arn:aws:states:us-west-2:123456789000:execution:MolUnfBatchEvaluationBatchEvaluationStateMachine759181D6-smNpiWdkgrOI:test_execution_id',
        'user_input': {
            "version": "1",
            "runMode": "ALL",
            "molFile": "s3://test_bucket/qc/raw_model/117_ideal.mol2",
            "modelVersion": "v1",
            "experimentName": "test",
            "optParams": {
                "qa": {
                    "shots": 1000,
                    "embed_method": "default"
                },
                "sa": {
                    "shots": 100,
                    "notes": "batch evaluation"
                }
            },

            "modelParams": {
                "M": [1, 2, 3, 4],
                "D": [4],
                "A": [300],
                "HQ": [200]
            },
            "devicesArns": [
                "arn:aws:braket:::device/qpu/d-wave/DW_2000Q_6",
                "arn:aws:braket:::device/qpu/d-wave/Advantage_system4",
                "arn:aws:braket:us-west-2::device/qpu/d-wave/Advantage_system6",
            ],
            "ccResources": [
                [2, 2],
                [4, 4],
                [8, 8],
                [16, 16]
            ]
        }
    }

    app.handler(event, None)
    assert True


@mock_s3
def test_handler_CHECK_INPUT_M4_D8(monkeypatch):
    boto3.setup_default_session()
    from . import app
    monkeypatch.setenv('AWS_REGION', 'us-east-1')
    s3 = boto3.client('s3', region_name='us-east-1')
    s3.create_bucket(Bucket='test_s3_bucket')

    event = {
        'param_type': 'CHECK_INPUT',
        's3_bucket': 'test_s3_bucket',
        's3_prefix': 'test_s3_prefix',
        'execution_id': 'arn:aws:states:us-west-2:123456789000:execution:MolUnfBatchEvaluationBatchEvaluationStateMachine759181D6-smNpiWdkgrOI:test_execution_id',
        'user_input': {
            "modelParams": {
                "M": [1, 2, 3, 4],
                "D": [8],
            }
        }
    }
    app.handler(event, None)
    assert True


@mock_s3
def test_handler_CHECK_INPUT_M4_D4(monkeypatch):
    boto3.setup_default_session()
    from . import app
    monkeypatch.setenv('AWS_REGION', 'us-east-1')
    s3 = boto3.client('s3', region_name='us-east-1')
    s3.create_bucket(Bucket='test_s3_bucket')

    event = {
        'param_type': 'CHECK_INPUT',
        's3_bucket': 'test_s3_bucket',
        's3_prefix': 'test_s3_prefix',
        'execution_id': 'arn:aws:states:us-west-2:123456789000:execution:MolUnfBatchEvaluationBatchEvaluationStateMachine759181D6-smNpiWdkgrOI:test_execution_id',
        'user_input': {
            "modelParams": {
                "M": [1, 2, 3, 4],
                "D": [4],
            }
        }
    }
    app.handler(event, None)
    assert True


@mock_s3
def test_handler_CHECK_INPUT_runMode_err(monkeypatch):
    boto3.setup_default_session()
    from . import app
    monkeypatch.setenv('AWS_REGION', 'us-east-1')
    s3 = boto3.client('s3', region_name='us-east-1')
    s3.create_bucket(Bucket='test_s3_bucket')

    event = {
        'param_type': 'CHECK_INPUT',
        's3_bucket': 'test_s3_bucket',
        's3_prefix': 'test_s3_prefix',
        'execution_id': 'arn:aws:states:us-west-2:123456789000:execution:MolUnfBatchEvaluationBatchEvaluationStateMachine759181D6-smNpiWdkgrOI:test_execution_id',
        'user_input': {
            "runModex": "QC",
        }
    }
    with pytest.raises(Exception) as excinfo:
        app.handler(event, None)

    assert 'validate error' in str(excinfo.value)


@mock_s3
def test_handler_CHECK_INPUT_modelParams_M(monkeypatch):
    boto3.setup_default_session()
    from . import app
    monkeypatch.setenv('AWS_REGION', 'us-east-1')
    s3 = boto3.client('s3', region_name='us-east-1')
    s3.create_bucket(Bucket='test_s3_bucket')

    event = {
        'param_type': 'CHECK_INPUT',
        's3_bucket': 'test_s3_bucket',
        's3_prefix': 'test_s3_prefix',
        'execution_id': 'arn:aws:states:us-west-2:123456789000:execution:MolUnfBatchEvaluationBatchEvaluationStateMachine759181D6-smNpiWdkgrOI:test_execution_id',
        'user_input': {
            "modelParams": {
                "M": [101],
                "D": [4],
                "A": [300],
                "HQ": [200]
            },
        }
    }

    app.handler(event, None)
    assert True



@mock_s3
def test_handler_CHECK_INPUT_modelParams_M_Error_empty(monkeypatch):
    boto3.setup_default_session()
    from . import app
    monkeypatch.setenv('AWS_REGION', 'us-east-1')
    s3 = boto3.client('s3', region_name='us-east-1')
    s3.create_bucket(Bucket='test_s3_bucket')

    event = {
        'param_type': 'CHECK_INPUT',
        's3_bucket': 'test_s3_bucket',
        's3_prefix': 'test_s3_prefix',
        'execution_id': 'arn:aws:states:us-west-2:123456789000:execution:MolUnfBatchEvaluationBatchEvaluationStateMachine759181D6-smNpiWdkgrOI:test_execution_id',
        'user_input': {
            "modelParams": {
                "M": [],
            },
        }
    }
    with pytest.raises(Exception) as excinfo:
        app.handler(event, None)

    assert 'value for M is empty' in str(excinfo.value)
    

@mock_s3
def test_handler_CHECK_INPUT_modelParams_D16(monkeypatch):
    boto3.setup_default_session()
    from . import app
    monkeypatch.setenv('AWS_REGION', 'us-east-1')
    s3 = boto3.client('s3', region_name='us-east-1')
    s3.create_bucket(Bucket='test_s3_bucket')

    event = {
        'param_type': 'CHECK_INPUT',
        's3_bucket': 'test_s3_bucket',
        's3_prefix': 'test_s3_prefix',
        'execution_id': 'arn:aws:states:us-west-2:123456789000:execution:MolUnfBatchEvaluationBatchEvaluationStateMachine759181D6-smNpiWdkgrOI:test_execution_id',
        'user_input': {
            "modelParams": {
                "D": [16]
            },
        }
    }

    app.handler(event, None)
    assert True
  

@mock_s3
def test_handler_CHECK_INPUT_modelParams_D_empty_error(monkeypatch):
    boto3.setup_default_session()
    from . import app
    monkeypatch.setenv('AWS_REGION', 'us-east-1')
    s3 = boto3.client('s3', region_name='us-east-1')
    s3.create_bucket(Bucket='test_s3_bucket')

    event = {
        'param_type': 'CHECK_INPUT',
        's3_bucket': 'test_s3_bucket',
        's3_prefix': 'test_s3_prefix',
        'execution_id': 'arn:aws:states:us-west-2:123456789000:execution:MolUnfBatchEvaluationBatchEvaluationStateMachine759181D6-smNpiWdkgrOI:test_execution_id',
        'user_input': {
            "modelParams": {
                "D": []
            },
        }
    }

    with pytest.raises(Exception) as excinfo:
        app.handler(event, None)

    assert 'validate error' in str(excinfo.value)



@mock_s3
def test_handler_CHECK_INPUT_modelParams_D_4_8_error(monkeypatch):
    boto3.setup_default_session()
    from . import app
    monkeypatch.setenv('AWS_REGION', 'us-east-1')
    s3 = boto3.client('s3', region_name='us-east-1')
    s3.create_bucket(Bucket='test_s3_bucket')

    event = {
        'param_type': 'CHECK_INPUT',
        's3_bucket': 'test_s3_bucket',
        's3_prefix': 'test_s3_prefix',
        'execution_id': 'arn:aws:states:us-west-2:123456789000:execution:MolUnfBatchEvaluationBatchEvaluationStateMachine759181D6-smNpiWdkgrOI:test_execution_id',
        'user_input': {
            "modelParams": {
                "D": [4, 8]
            },
        }
    }

    with pytest.raises(Exception) as excinfo:
        app.handler(event, None)

    assert 'validate error' in str(excinfo.value)


@mock_s3
def test_handler_CHECK_INPUT_modelParams_devicesArns_error(monkeypatch):
    boto3.setup_default_session()
    from . import app
    monkeypatch.setenv('AWS_REGION', 'us-east-1')
    s3 = boto3.client('s3', region_name='us-east-1')
    s3.create_bucket(Bucket='test_s3_bucket')

    event = {
        'param_type': 'CHECK_INPUT',
        's3_bucket': 'test_s3_bucket',
        's3_prefix': 'test_s3_prefix',
        'execution_id': 'arn:aws:states:us-west-2:123456789000:execution:MolUnfBatchEvaluationBatchEvaluationStateMachine759181D6-smNpiWdkgrOI:test_execution_id',
        'user_input': {
             "devicesArns": [
                "DW_2000Q_6",
                "Advantage_system4"
                ],
        }
    }

    with pytest.raises(Exception) as excinfo:
        app.handler(event, None)

    assert 'validate error' in str(excinfo.value)


@mock_s3
def test_handler_CHECK_INPUT_ccResources_max_err(monkeypatch):
    boto3.setup_default_session()
    from . import app
    monkeypatch.setenv('AWS_REGION', 'us-east-1')
    s3 = boto3.client('s3', region_name='us-east-1')
    s3.create_bucket(Bucket='test_s3_bucket')

    event = {
        'param_type': 'CHECK_INPUT',
        's3_bucket': 'test_s3_bucket',
        's3_prefix': 'test_s3_prefix',
        'execution_id': 'arn:aws:states:us-west-2:123456789000:execution:MolUnfBatchEvaluationBatchEvaluationStateMachine759181D6-smNpiWdkgrOI:test_execution_id',
        'user_input': {
            "ccResources": [
                [1, 2],
                [2, 2],
                [2, 4],
                [4, 4],
                [4, 8],
                [4, 16],
                [8, 8],
                [8, 16],
                [8, 32],
                [16, 16],
                [16, 32]
            ]
        }
    }
    with pytest.raises(Exception) as excinfo:
        app.handler(event, None)

    assert 'validate error: max ccResources length is' in str(excinfo.value)


@mock_s3
def test_handler_PARAMS_FOR_QC_DEVICE(monkeypatch):
    boto3.setup_default_session()
    from . import app
    s3 = boto3.client('s3', region_name='us-east-1')
    s3.create_bucket(Bucket='test_s3_bucket')

    monkeypatch.setenv('AWS_REGION', 'us-east-1')

    event = {
        'param_type': 'CHECK_INPUT',
        's3_bucket': 'test_s3_bucket',
        's3_prefix': 'test_s3_prefix',
        'execution_id': 'arn:aws:states:us-west-2:123456789000:execution:MolUnfBatchEvaluationBatchEvaluationStateMachine759181D6-smNpiWdkgrOI:test_execution_id',
        'user_input': {}
    }

    app.handler(event, None)

    event = {
        'param_type': 'PARAMS_FOR_QC_DEVICE',
        's3_bucket': 'test_s3_bucket',
        's3_prefix': 'test_s3_prefix',
        'execution_id': 'test_execution_id',
        'device_arn': "arn:aws:braket:::device/qpu/d-wave/DW_2000Q_6"
    }

    s3.put_object(
        Body=json.dumps({
            "user_input": {
                "modelParams": {
                    "M": [1, 2, 3, 4],
                    "D": [4]
                },
                "devicesArns": [
                    "arn:aws:braket:::device/qpu/d-wave/DW_2000Q_6",
                    "arn:aws:braket:::device/qpu/d-wave/Advantage_system4",
                    "arn:aws:braket:us-west-2::device/qpu/d-wave/Advantage_system6"
                ],
                "ccResources": [
                    [2, 2],
                    [4, 4],
                    [8, 8],
                    [16, 16]
                ]
            },
            "execution_id": 'test_execution_id',
            "aws_region": 'us-east-1',
            "start_time": datetime.datetime.utcnow().isoformat()
        }).encode("utf-8"),

        Bucket='test_s3_bucket',
        Key='test_s3_prefix/executions/test_execution_id/user_input.json'
    )

    params = app.handler(event, None)
    assert len(params['qcTaskParams']) == 4


@mock_s3
def test_handler_PARAMS_FOR_CC(monkeypatch):
    boto3.setup_default_session()
    from . import app
    s3 = boto3.client('s3', region_name='us-east-1')
    s3.create_bucket(Bucket='test_s3_bucket')

    monkeypatch.setenv('AWS_REGION', 'us-east-1')

    event = {
        'param_type': 'CHECK_INPUT',
        's3_bucket': 'test_s3_bucket',
        's3_prefix': 'test_s3_prefix',
        'execution_id': 'arn:aws:states:us-west-2:123456789000:execution:MolUnfBatchEvaluationBatchEvaluationStateMachine759181D6-smNpiWdkgrOI:test_execution_id',
        'user_input': {}
    }

    app.handler(event, None)

    event = {
        'param_type': 'PARAMS_FOR_CC',
        's3_bucket': 'test_s3_bucket',
        's3_prefix': 'test_s3_prefix',
        'execution_id': 'test_execution_id',
        'device_arn': "arn:aws:braket:::device/qpu/d-wave/DW_2000Q_6"
    }

    s3.put_object(
        Body=json.dumps({
            "user_input": {
                "modelParams": {
                    "M": [1, 2, 3, 4],
                    "D": [4]
                },
                "devicesArns": [
                    "arn:aws:braket:::device/qpu/d-wave/DW_2000Q_6",
                    "arn:aws:braket:::device/qpu/d-wave/Advantage_system4"
                ],
                "ccResources": [
                    [2, 2],
                    [4, 4],
                    [8, 8],
                    [16, 16]
                ]
            },
            "execution_id": 'test_execution_id',
            "aws_region": 'us-east-1',
            "start_time": datetime.datetime.utcnow().isoformat()
        }).encode("utf-8"),

        Bucket='test_s3_bucket',
        Key='test_s3_prefix/executions/test_execution_id/user_input.json'
    )

    params = app.handler(event, None)
    assert len(params['ccTaskParams']) == 16
