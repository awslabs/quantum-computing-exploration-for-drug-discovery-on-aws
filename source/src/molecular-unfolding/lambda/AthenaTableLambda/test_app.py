# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from moto import mock_athena
import pytest 

@mock_athena
def test_handler(monkeypatch):
    monkeypatch.setenv('BUCKET', 'test-bucket')
    monkeypatch.setenv('AWS_REGION', 'us-west-2')
    from . import app 
    monkeypatch.setattr(app.athena_client, 'get_query_execution', lambda **kwargs: {
        'QueryExecution': {
            'Status': {
                'State': "SUCCEEDED"
            }
        }
    })
    event = {
        's3_prefix': 's3_prefix_test',
        'stackName': 'qcstack'
    }
    res = app.handler(event, None)
    assert res['endTime'] is not None


@mock_athena
def test_handler_with_error(monkeypatch):
    monkeypatch.setenv('BUCKET', 'test-bucket')
    monkeypatch.setenv('AWS_REGION', 'us-west-2')
    from . import app 
    monkeypatch.setattr(app.athena_client, 'get_query_execution', lambda **kwargs: {
        'QueryExecution': {
            'Status': {
                'State': "FAILED"
            }
        }
    })
    event = {
        's3_prefix': 's3_prefix_test',
        'stackName': 'qcstack'
    }

    with pytest.raises(Exception) as excinfo:
        app.handler(event, None)
