const AWS = require('aws-sdk')
const util = require('util')
const client = new AWS.Athena({})
const bucket = process.env.BUCKET

exports.handler = function (event, context, callback) {
    //console.log("REQUEST RECEIVED:\n" + JSON.stringify(event))
    const s3_prefix = event['s3_prefix']
    const stackName = event['stackName']
    const execution_id = event['execution_id']

    console.log(`stackName: ${stackName}, s3_prefix: ${s3_prefix}`)

    const ATHENA_OUTPUT_LOCATION = `s3://${bucket}/${s3_prefix}/athena-out/`
    const location = `s3://${bucket}/${s3_prefix}/benchmark_metrics/`
    const tableName = `${stackName}_qc_benchmark_metrics_hist`
    const viewName = `${stackName}_qc_benchmark_metrics`

    const dropTableSql = `DROP TABLE IF EXISTS ${tableName}`

    const createTableSql = "CREATE EXTERNAL TABLE IF NOT EXISTS " + tableName + "(\n" +
        "\tExecution_Id string,\n" +
        "\tCompute_Type string,\n" +
        "\tResource string,\n" +
        "\tParams string,\n" + 
        "\tOpt_Params string,\n" +
        "\tTask_Duration float,\n" +
        "\tTime_Info string,\n" +
        "\tStart_Time string,\n" +
        "\tExperiment_Name string,\n" +
        "\tTask_Id string,\n" +
        "\tModel_Name string,\n" +  
        "\tModel_FileName string,\n" + 
        "\tScenario string,\n" +
        "\tCreate_Time string,\n" +
        "\tResult_Detail string,\n" +
        "\tResult_Location string\n" +
        ") ROW FORMAT DELIMITED FIELDS TERMINATED BY '!' LINES TERMINATED BY '\\n' LOCATION '" + location + "'"

    const createViewSql = `
        CREATE OR REPLACE VIEW ${viewName} as 
        select * from  ${tableName} h1
        where Start_Time = (select Max(Start_Time) from ${tableName} h2)
         `
    const querySql = `SELECT * FROM ${viewName}`

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

    console.info("run sql:" + createTableSql)
    startAhenaQueryExecution({
        QueryString: dropTableSql,
        ResultConfiguration: {
            OutputLocation: ATHENA_OUTPUT_LOCATION
        },
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