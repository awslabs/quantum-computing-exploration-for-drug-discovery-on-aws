/*
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/


const AWS = require('aws-sdk')
const util = require('util')

const bucket = process.env.BUCKET

const solution_id = process.env['SOLUTION_ID']
const solution_version = process.env['SOLUTION_VERSION'] || 'v1.0.0'

const options = { customUserAgent: `AwsSolution/${solution_id}/${solution_version}` };
const client = new AWS.Athena(options)

exports.handler = function (event, context, callback) {
    const s3_prefix = event['s3_prefix']
    const stackName = event['stackName']
    const execution_id = event['execution_id']
   
    console.log(`stackName: ${stackName}, s3_prefix: ${s3_prefix}`)

    const ATHENA_OUTPUT_LOCATION = `s3://${bucket}/${s3_prefix}/athena-out/`
    const location = `s3://${bucket}/${s3_prefix}/batch_evaluation_metrics/`
    const tableName = `${stackName}_qc_batch_evaluation_metrics_hist`
    const viewName = `${stackName}_qc_batch_evaluation_metrics`
    const createDBSql = `CREATE DATABASE IF NOT EXISTS qc_db`
    const dropTableSql = `DROP TABLE IF EXISTS qc_db.${tableName}`
    const createTableSql = `
    CREATE EXTERNAL TABLE IF NOT EXISTS qc_db.${tableName} (
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
    ) ROW FORMAT DELIMITED FIELDS TERMINATED BY '\\t' LINES TERMINATED BY '\\n' LOCATION '${location}' 
`

    const createViewSql = `
    CREATE OR REPLACE VIEW qc_db.${viewName} AS 
    SELECT h1.*
    FROM
    qc_db.${tableName} h1
    , (
       SELECT DISTINCT
         Execution_Id
       , Start_Time
       FROM
       qc_db.${tableName}
       ORDER BY Start_Time DESC
       LIMIT 20
    )  h2
    WHERE (h1.Execution_Id = h2.Execution_Id)
`
    const querySql = `SELECT * FROM qc_db.${viewName}`

    const startAhenaQueryExecution = (queryInfo) => {
        return new Promise((resolve, reject) => {
            client.startQueryExecution(queryInfo, (error, results) => {
                if (error) {
                    return reject(error)
                } else {
                    return resolve(results)
                }
            })
        });
    }

    const sqlStmSeq = [createDBSql, dropTableSql, createTableSql, createViewSql, querySql]

    let execPromise = null;
    let timeDelaySeconds = 10000

    for (const sqlStm of sqlStmSeq) {
        if (execPromise == null) {
            console.info("run sql:" + sqlStm)
            execPromise = startAhenaQueryExecution({
                QueryString: sqlStm,
                ResultConfiguration: {
                    OutputLocation: ATHENA_OUTPUT_LOCATION
                },
            });
        } else {
            execPromise = execPromise.then(
                setTimeout(() => {
                    console.info("run sql:" + sqlStm)
                    startAhenaQueryExecution({
                        QueryString: sqlStm,
                        ResultConfiguration: {
                            OutputLocation: ATHENA_OUTPUT_LOCATION
                        },
                    })
                }, timeDelaySeconds)
            );
        }
        timeDelaySeconds += 10000
    }

    execPromise.then(() => {
        callback(null, {
            queryResult: ATHENA_OUTPUT_LOCATION,
            endTime: new Date().toISOString()
        })
    }).catch(error => {
        callback(error)
    })
}
