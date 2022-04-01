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
        Resource string,
        Params string,
        Opt_Params string,
        Task_Duration float,
        Time_Info string,
        Start_Time string,
        Experiment_Name string,
        Task_Id string,
        Model_Name string,
        Model_FileName string, 
        Scenario string,
        Create_Time string,
        Result_Detail string,
        Result_Location string
    ) ROW FORMAT DELIMITED FIELDS TERMINATED BY '!' LINES TERMINATED BY '\\n' LOCATION '${location}' 
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

    console.info("run sql:" + createDBSql)
    startAhenaQueryExecution({
        QueryString: createDBSql,
        ResultConfiguration: {
            OutputLocation: ATHENA_OUTPUT_LOCATION
        },
    }).then(result => {
        setTimeout(() => {
            console.info("run sql:" + dropTableSql)
            startAhenaQueryExecution({
                QueryString: dropTableSql,
                ResultConfiguration: {
                    OutputLocation: ATHENA_OUTPUT_LOCATION
                },
            })
        }, 5000)
    }).then(result => {
        setTimeout(() => {
            console.info("run sql:" + createTableSql)
            startAhenaQueryExecution({
                QueryString: createTableSql,
                ResultConfiguration: {
                    OutputLocation: ATHENA_OUTPUT_LOCATION
                },
            })
        }, 10000)

    }).then(result => {
        setTimeout(() => {
            console.info("run sql:" + createViewSql)
            startAhenaQueryExecution({
                QueryString: createViewSql,
                ResultConfiguration: {
                    OutputLocation: ATHENA_OUTPUT_LOCATION
                },
            })
        }, 20000)

    }).then(result => {
        setTimeout(() => {
            console.info("run sql:" + querySql)
            startAhenaQueryExecution({
                QueryString: querySql,
                ResultConfiguration: {
                    OutputLocation: ATHENA_OUTPUT_LOCATION
                },
            })
        }, 30000)
    }).then(result => {
        callback(null, {
            queryResult: ATHENA_OUTPUT_LOCATION,
            endTime: new Date().toISOString()
        })
    }).catch(error => {
        callback(error)
    })
}