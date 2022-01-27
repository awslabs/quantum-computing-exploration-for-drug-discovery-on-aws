const {
    EventBridgeClient,
    PutRuleCommand,
    DeleteRuleCommand,
    PutTargetsCommand,
    RemoveTargetsCommand
} = require("@aws-sdk/client-eventbridge");

const {
    IAMClient,
    CreateRoleCommand,
    CreatePolicyCommand,
    AttachRolePolicyCommand,
    GetRoleCommand,
    GetPolicyCommand,
    DeleteRoleCommand,
    DeletePolicyCommand,
    DetachRolePolicyCommand
} = require("@aws-sdk/client-iam");

exports.handler = async function (event, context) {
    await _handler(event, context).then(() => {
        console.log("=== complete ===")
    }).catch((e) => console.log(e))
}

async function _handler(event, context) {
    //console.log("EVENT: \n" + JSON.stringify(event, null, 2))
    const awsAccountId = context.invokedFunctionArn.split(':')[4]
    const currentRegion = process.env.AWS_REGION
    const RequestType = event['RequestType']

    console.log("awsAccountId:" + awsAccountId)
    console.log("currentRegion: " + currentRegion)
    console.log("RequestType: " + RequestType)

    const currentRegionShort = currentRegion.replace(/-/g, '')

    if (currentRegion == "us-west-2") {
        console.log('ignore creating event rule')
        return
    }

    const iam_client = new IAMClient({
        region: "us-west-2"
    });

    const event_client = new EventBridgeClient({
        region: "us-west-2"
    });

    const roleName = 'QCBraketEventCrossRegion-' + currentRegion;
    const policyName = "QCBraketEventCrossRegion-" + currentRegion;
    const policyArn = `arn:aws:iam::${awsAccountId}:policy/${policyName}`;
    const ruleName = 'QCBraketRule' + currentRegionShort;
    const targetId = 'CrossRegionDestinationBusId';
    const detachAttachPolicyInput = {
        PolicyArn: policyArn,
        RoleName: roleName
    }

    console.log("GetRoleCommand ...")
    await iam_client.send(new GetRoleCommand({
        RoleName: roleName
    })).catch((e) => console.log(e))

    console.log("DetachRolePolicyCommand ...")
    await iam_client.send(new DetachRolePolicyCommand(detachAttachPolicyInput))
        .catch((e) => console.log(e));

    console.log("DeleteRoleCommand ...")
    await iam_client.send(new DeleteRoleCommand({
        RoleName: roleName
    })).catch((e) => console.log(e));

    console.log("GetPolicyCommand ...")
    await iam_client.send(new GetPolicyCommand({
        PolicyArn: policyArn
    })).then(() => {
        console.log("DeletePolicyCommand ..." + ruleName)
        iam_client.send(new DeletePolicyCommand({
            PolicyArn: policyArn
        }))
    }).catch((e) => console.log(e));

    console.log("RemoveTargetsCommand ..." + ruleName)
    await event_client.send(new RemoveTargetsCommand({
        Ids: [targetId],
        Rule: ruleName
    })).catch((e) => console.log(e));

    console.log("DeleteRuleCommand ..." + ruleName)
    await event_client.send(new DeleteRuleCommand({
        Name: ruleName
    })).catch((e) => console.log(e));

    if (RequestType == "Delete") {
        return
    }

    ////////////////////////////////////////////////////////////

    const createRoleInput = {
        AssumeRolePolicyDocument: JSON.stringify({
            Version: "2012-10-17",
            Statement: [{
                Effect: "Allow",
                Principal: {
                    Service: "events.amazonaws.com"
                },
                Action: "sts:AssumeRole"
            }]
        }),
        Path: "/",
        RoleName: roleName
    }

    const createPolicyInput = {
        PolicyName: policyName,
        PolicyDocument: JSON.stringify({
            Version: "2012-10-17",
            Statement: [{
                Effect: "Allow",
                Action: ['events:PutEvents'],
                Resource: [`arn:aws:events:${currentRegion}:${awsAccountId}:event-bus/default`]
            }]
        })
    }

    console.log("CreateRoleCommand ..." + JSON.stringify(createRoleInput))
    const createRoleOutput = await iam_client.send(new CreateRoleCommand(createRoleInput))
    const roleArn = createRoleOutput.Role.Arn;

    console.log("CreatePolicyCommand ..." + JSON.stringify(createPolicyInput))
    await iam_client.send(new CreatePolicyCommand(createPolicyInput))

    console.log("AttachRolePolicyCommand ..." + JSON.stringify(detachAttachPolicyInput))
    await iam_client.send(new AttachRolePolicyCommand(detachAttachPolicyInput))


    const eventPattern = {
        "source": ["aws.braket"],
        "detail-type": ['Braket Task State Change']
    }

    const ruleInput = {
        Name: ruleName,
        Description: 'Routes to targetRegion event bus',
        EventBusName: 'default',
        EventPattern: JSON.stringify(eventPattern),
        State: 'ENABLED'
    }
    const ruleCommand = new PutRuleCommand(ruleInput);

    console.log("PutRuleCommand ... " + JSON.stringify(ruleInput))
    const ruleOutput = await event_client.send(ruleCommand);
    console.log(`ruleOutput.RuleArn: ${ruleOutput.RuleArn}`)

    const targetInput = {
        EventBusName: 'default',
        Rule: ruleName,
        Targets: [{
            Arn: `arn:aws:events:${currentRegion}:${awsAccountId}:event-bus/default`,
            Id: targetId,
            RoleArn: roleArn
        }]
    }
    const targetCommand = new PutTargetsCommand(targetInput);
    console.log("PutTargetsCommand ..." + JSON.stringify(targetInput))
    const targetOutput = await event_client.send(targetCommand);

    return targetOutput
}