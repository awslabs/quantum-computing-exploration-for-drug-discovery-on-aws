import {
  readFileSync,
} from 'fs';

import {
  CloudFormationClient,
  CreateStackCommand,
  UpdateStackCommand,
  DeleteStackCommand,
  DescribeStacksCommand,
} from '@aws-sdk/client-cloudformation';

import {
  Context,
  CloudFormationCustomResourceEvent,
} from 'aws-lambda'; // eslint-disable-line import/no-unresolved


exports.handler = async function (event: CloudFormationCustomResourceEvent, context: Context) {
  try {
    await _handler(event, context);
    console.log('=== complete ===');
  } catch (e: any) {
    console.error(e.message);
    throw e;
  }
};

function sleep(millis: number) {
  return new Promise(resolve => setTimeout(resolve, millis));
}

async function _handler(event: CloudFormationCustomResourceEvent, context: Context) {
  const currentRegion = process.env.AWS_REGION;
  let RequestType = event.RequestType;

  console.log('functionName: ' + context.functionName);
  console.log('currentRegion: ' + currentRegion);
  console.log('RequestType: ' + RequestType);

  if (currentRegion == 'us-west-2') {
    console.log('ignore creating event rule');
    return;
  }
  const config = {
    region: 'us-west-2',
  };

  const cf_client = new CloudFormationClient(config);
  let templateBody = readFileSync(`${__dirname}/template.json`, 'utf-8');
  const stackName = `QRSFDD-BraketEventTo${currentRegion}`;
  const eventBridgeRoleArn = process.env.EVENT_BRIDGE_ROLE_ARN;
  const createStackInput = {
    StackName: stackName,
    Capabilities: ['CAPABILITY_NAMED_IAM'],
    Parameters: [{
      ParameterKey: 'TargetRegion',
      ParameterValue: currentRegion,
    },
    {
      ParameterKey: 'EventBridgeRoleArn',
      ParameterValue: eventBridgeRoleArn,
    }],
    TemplateBody: templateBody,
  };

  const describeCommand = new DescribeStacksCommand({
    StackName: stackName,
  });

  let stackExists = true;
  try {
    await cf_client.send(describeCommand);
  } catch (e: any) {
    if (e.message.indexOf('does not exist') > 0) {
      stackExists = false;
    } else {
      console.error(e.message);
      throw e;
    }
  }

  console.log('stackExists: ' + stackExists);

  if (!stackExists && RequestType == 'Delete') {
    console.log('stack already deleted');
    return;
  }

  let command = undefined;

  if (RequestType != 'Delete') {
    if (stackExists) {
      console.log('UpdateStackCommand ... ');
      command = new UpdateStackCommand(createStackInput);
    } else {
      console.log('CreateStackCommand ... ');
      command = new CreateStackCommand(createStackInput);
    }
  } else {
    console.log('DeleteStackCommand ... ');
    command = new DeleteStackCommand({
      StackName: stackName,
    });
  }

  await cf_client.send(command);

  // Wait for complete
  let response = undefined;
  let stackStatus = '';
  do {
    response = undefined;
    try {
      response = await cf_client.send(describeCommand);
    } catch (e: any) {
      if (RequestType == 'Delete' && e.message.indexOf('does not exist') > 0) {
        stackStatus = 'complete';
      } else {
        console.error(e.message);
      }
    }

    if (response && response.Stacks && response.Stacks[0] && stackStatus != 'complete') {
      stackStatus = response.Stacks[0].StackStatus?? '';
      console.log(`${stackStatus}`);
      await sleep(5000);
    }

  } while (stackStatus.indexOf('IN_PROGRESS') > 0);

  return response;

}