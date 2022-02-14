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

import { Logger } from '@aws-lambda-powertools/logger';

const logger = new Logger();

exports.handler = async function (event, context) {
    await _handler(event, context).then(() => {
        logger.info("=== complete ===")
    }).catch((e) => {
        logger.error(e);
        throw e
    })
}

function sleep(millis) {
    return new Promise(resolve => setTimeout(resolve, millis));
}

async function _handler(event, context) {
    const currentRegion = process.env.AWS_REGION

    const RequestType = event['RequestType']
    logger.addContext(context);
    
    logger.info("currentRegion: " + currentRegion)
    logger.info("RequestType: " + RequestType)

    if (currentRegion == "us-west-2") {
        logger.info('ignore creating event rule')
        return
    }
    const config = {
        region: "us-west-2"
    }

    const cf_client = new CloudFormationClient(config);
    let templateBody = readFileSync(`${__dirname}/template.json`, 'utf-8')
    const stackName = `QRSFDD-BraketEventTo${currentRegion}`
    const eventBridgeRoleArn = process.env.EVENT_BRIDGE_ROLE_ARN
    const createStackInput = {
        StackName: stackName,
        Capabilities: ['CAPABILITY_NAMED_IAM'],
        Parameters: [{
            ParameterKey: 'TargetRegion',
            ParameterValue: currentRegion
        },
        {
            ParameterKey: 'EventBridgeRoleArn',
            ParameterValue: eventBridgeRoleArn
        }
        ],
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
            logger.info(e.message);
            throw e;
        }
    });

    logger.info("stackExists: " + stackExists)

    if (!stackExists && RequestType == "Delete") {
        logger.info("stack already deleted")
        return
    }

    let command = undefined;

    if (RequestType != "Delete") {
        if (stackExists) {
            logger.info("UpdateStackCommand ... ")
            command = new UpdateStackCommand(createStackInput);
        } else {
            logger.info("CreateStackCommand ... ")
            command = new CreateStackCommand(createStackInput);
        }
    } else {
        logger.info("DeleteStackCommand ... ")
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
            logger.info(e.message);
            if (RequestType == "Delete" && e.message.indexOf('does not exist') > 0) {
                stackStatus = 'complete'
            }
        });
        if (response && stackStatus != 'complete') {
            stackStatus = response['Stacks'][0]['StackStatus']
            logger.info(`${stackStatus}`)
            await sleep(5000);
        }

    } while (stackStatus.indexOf('IN_PROGRESS') > 0)

    return response

}