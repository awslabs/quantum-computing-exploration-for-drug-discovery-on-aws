# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import boto3
import botocore
import os
import logging
import time
import json
import datetime

log = logging.getLogger()
log.setLevel('INFO')

bucket = os.environ['BUCKET']
region = os.environ['AWS_REGION']

solution_version = os.environ.get('SOLUTION_VERSION', 'v1.0.0')
solution_id = os.environ.get('SOLUTION_ID')
user_agent_config = {
    'user_agent_extra': f'AwsSolution/{solution_id}/{solution_version}',
    'region_name': region 
}
default_config = botocore.config.Config(**user_agent_config)

athena_client = boto3.client('athena', config=default_config)

def handler(event, context):

    s3_prefix = event['s3_prefix']
    table_prefix = event["stackName"]

    log.info(f"table_prefix: {table_prefix}, s3_prefix: {s3_prefix}")
    table_name = f"{table_prefix}_qc_batch_evaluation_metrics_hist"
    view_name = f"{table_prefix}_qc_batch_evaluation_metrics"
    ATHENA_OUTPUT_LOCATION = f"s3://{bucket}/{s3_prefix}/athena-out/"
    location = f"s3://{bucket}/{s3_prefix}/batch_evaluation_metrics/"
    createDBSql = "CREATE DATABASE IF NOT EXISTS qc_db"
    dropTableSql = f"DROP TABLE IF EXISTS qc_db.{table_name}"
    createTableSql = f'''
    CREATE EXTERNAL TABLE IF NOT EXISTS qc_db.{table_name} (
        Execution_Id string,
        Compute_Type string,
        Resolver string,
        Complexity integer,
        End_To_End_Time float,
        Running_Time float,
        Time_Info string,
        Start_Time string,
        Experiment_Name string,
        Task_Id string,
        Model_Name string,
        Model_FileName string,
        Scenario string,
        Resource string,
        Model_Param string,
        Opt_Param string,
        Create_Time string,
        Result_Detail string,
        Result_Location string
    ) ROW FORMAT DELIMITED FIELDS TERMINATED BY '\\t' LINES TERMINATED BY '\\n' LOCATION '{location}'
'''
    createViewSql = f"CREATE OR REPLACE VIEW qc_db.{view_name} AS SELECT h1.* FROM qc_db.{table_name} h1, (SELECT DISTINCT Execution_Id, Start_Time FROM qc_db.{table_name} ORDER BY Start_Time DESC LIMIT 20)  h2 WHERE (h1.Execution_Id = h2.Execution_Id)" #nosec B608
    querySql = f"SELECT * FROM qc_db.{view_name}" #nosec B608

    sqlStmSeq = [createDBSql, dropTableSql, createTableSql, createViewSql, querySql]

    for sqlStm in sqlStmSeq:
        log.info(sqlStm)
        response = athena_client.start_query_execution(
            QueryString=sqlStm,
            ResultConfiguration={
                'OutputLocation': ATHENA_OUTPUT_LOCATION
            }
        )
        execution_id = response['QueryExecutionId']
        wait_for_complete(execution_id)

    log.info("all done")
    return {
        'queryResult': ATHENA_OUTPUT_LOCATION,
        'endTime': datetime.datetime.utcnow().isoformat()
    }


def wait_for_complete(execution_id):
    log.info("execution_id:{}".format(execution_id))
    response = athena_client.get_query_execution(
        QueryExecutionId=execution_id
    )
    while True:
        status = response['QueryExecution']['Status']
        log.info("State: {}".format(status['State']))
        if status['State'] == 'SUCCEEDED':
            return status
        elif status['State'] in ['QUEUED', 'RUNNING']:
            time.sleep(3)
            response = athena_client.get_query_execution(
                QueryExecutionId=execution_id
            )
        else:
            log.error(json.dumps(response, default=str))
            raise Exception(json.dumps(response, default=str))
