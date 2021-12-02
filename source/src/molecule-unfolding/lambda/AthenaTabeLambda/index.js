const AWS = require('aws-sdk')
const util = require('util')
const client = new AWS.Athena({})
const bucket = process.env.BUCKET

exports.handler = function (event, context, callback) {
    console.log("REQUEST RECEIVED:\n" + JSON.stringify(event))
    const s3_prefix = "molecule-unfolding"
    const ATHENA_OUTPUT_LOCATION = `s3://${bucket}/${s3_prefix}/athena-out/`
    const location = `s3://${bucket}/${s3_prefix}/benchmark_metrics/`
    const dropTableSql = "DROP TABLE IF EXISTS qc_benchmark_metrics_hist"

    const createTableSql = "CREATE EXTERNAL TABLE IF NOT EXISTS qc_benchmark_metrics_hist(\n" +
        "\tExecution_Id string,\n" +
        "\tCompute_Type string,\n" +
        "\tResource string,\n" +
        "\tParams string,\n" +
        "\tTask_Duration1 float,\n" +
        "\tTask_Duration2 float,\n" +
        "\tTask_Duration3 float,\n" +
        "\tStart_Time string,\n" +
        "\tExperiment_Name string,\n" +
        "\tTask_Id string,\n" +
        "\tModel_Name string,\n" +  
        "\tModel_FileName string,\n" + 
        "\tScenario string,\n" +
        "\tCreate_Time string\n" +
        ") ROW FORMAT DELIMITED FIELDS TERMINATED BY ',' LINES TERMINATED BY '\\n' LOCATION '" + location + "'"

    const createViewSql = `
        CREATE OR REPLACE VIEW qc_benchmark_metrics as 
        select * from qc_benchmark_metrics_hist h1
        where Start_Time = (select Max(Start_Time) from qc_benchmark_metrics_hist h2)
         `
    const querySql = "SELECT * FROM qc_benchmark_metrics"

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