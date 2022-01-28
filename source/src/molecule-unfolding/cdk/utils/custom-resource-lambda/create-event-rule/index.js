const {
    CloudFormationClient,
    CreateStackCommand,
    UpdateStackCommand,
    DeleteStackCommand,
    DescribeStacksCommand
} = require("@aws-sdk/client-cloudformation");
const {
    readFileSync
} = require('fs');

exports.handler = async function (event, context) {
    await _handler(event, context).then(() => {
        console.log("=== complete ===")
    }).catch((e) => {
        console.log(e);
        throw e
    })
}

function sleep(millis) {
    return new Promise(resolve => setTimeout(resolve, millis));
}

async function _handler(event, context) {
    const currentRegion = process.env.AWS_REGION
    const RequestType = event['RequestType']

    console.log("currentRegion: " + currentRegion)
    console.log("RequestType: " + RequestType)

    if (currentRegion == "us-west-2") {
        console.log('ignore creating event rule')
        return
    }
    const config = {
        region: "us-west-2"
    }
    const cf_client = new CloudFormationClient(config);
    let templateBody = readFileSync(`${__dirname}/template.json`, 'utf-8')
    const stackName = `QRSFDD-BraketEventTo${currentRegion}`
    const createStackInput = {
        StackName: stackName,
        Capabilities: ['CAPABILITY_NAMED_IAM'],
        Parameters: [{
            ParameterKey: 'TargetRegion',
            ParameterValue: currentRegion
        }],
        TemplateBody: templateBody
    }

    const describeCommand = new DescribeStacksCommand({
        StackName: stackName
    });

    let stackExists = true
    await cf_client.send(describeCommand).catch(e => {
        if (e.message.indexOf('does not exist') > 0) {
            stackExists = false
        } else {
            console.log(e.message);
            throw e;
        }
    });

    console.log("stackExists: " + stackExists)

    if (!stackExists && RequestType == "Delete") {
        console.log("stack already deleted")
        return
    }

    let command = undefined;

    if (RequestType != "Delete") {
        if (stackExists) {
            console.log("UpdateStackCommand ... ")
            command = new UpdateStackCommand(createStackInput);
        } else {
            console.log("CreateStackCommand ... ")
            command = new CreateStackCommand(createStackInput);
        }
    } else {
        console.log("DeleteStackCommand ... ")
        command = new DeleteStackCommand({
            StackName: stackName
        })
    }

    await cf_client.send(command);

    // Wait for complete
    let response = undefined;
    let stackStatus = ''
    do {
        response = undefined;
        response = await cf_client.send(describeCommand).catch(e => {
            console.log(e.message);
            if (RequestType == "Delete" && e.message.indexOf('does not exist') > 0) {
                stackStatus = 'complete'
            }
        });
        if (response && stackStatus != 'complete') {
            stackStatus = response['Stacks'][0]['StackStatus']
            console.log(`${stackStatus}`)
            await sleep(5000);
        }

    } while (stackStatus.indexOf('IN_PROGRESS') > 0)

    return response

}