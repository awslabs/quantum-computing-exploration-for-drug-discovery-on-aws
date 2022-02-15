import {
    App
} from 'aws-cdk-lib';

import {
    Template,
    Match
} from "aws-cdk-lib/assertions";

import {
    SolutionStack
} from '../src/stack';

import {
    MainStack
} from '../src/molecule-unfolding/cdk/stack-main';

test('can create base stack', () => {
    const app = new App();
    const stack = new SolutionStack(app, 'test');
    Template.fromStack(stack);
});

test('can create MainStack', () => {
    const app = new App();
    const stack = new MainStack(app, 'test');
    expect(stack).not.toBeNull()
});

test("synthesizes the way we expect", () => {
    const app = new App();
    const stack = new MainStack(app, 'test');
    const template = Template.fromStack(stack);
    expect(template).toBeTruthy()
})

test("has 1 s3 bucket", () => {
    const app = new App();
    const stack = new MainStack(app, 'test');
    const template = Template.fromStack(stack);
    template.hasResource('AWS::S3::Bucket', 1)
})

test("s3 bucket can be deleted", () => {
    const app = new App();
    const stack = new MainStack(app, 'test');
    const template = Template.fromStack(stack);
    template.hasResource('Custom::S3AutoDeleteObjects', 1)
})

test("has 1 vpc", () => {
    const app = new App();
    const stack = new MainStack(app, 'test');
    const template = Template.fromStack(stack);
    template.hasResource('AWS::EC2::VPC', 1)
})

test("has 4 subnets", () => {
    const app = new App();
    const stack = new MainStack(app, 'test');
    const template = Template.fromStack(stack);
    template.hasResource("AWS::EC2::Subnet", 4)
})

test("has 1 flowLog", () => {
    const app = new App();
    const stack = new MainStack(app, 'test');
    const template = Template.fromStack(stack);
    template.hasResource("AWS::EC2::FlowLog", 1)
})

test("has output - bucketName", () => {
    const app = new App();
    const stack = new MainStack(app, 'test');
    const template = Template.fromStack(stack);
    template.hasOutput('bucketName', {})
})

test("has 1 CustomResource", () => {
    const app = new App();
    const stack = new MainStack(app, 'test');
    const template = Template.fromStack(stack);
    template.hasResource('AWS::CloudFormation::CustomResource', 1)
})

test("The CustomResource has Condition", () => {
    const app = new App();
    const stack = new MainStack(app, 'test');
    const template = Template.fromStack(stack);

    template.hasResource('AWS::CloudFormation::CustomResource', {
        "Condition": "CrossEventRegionCondition"
    })
})

test("CrossEventRegionCondition is for us-west-2", () => {
    const app = new App();
    const stack = new MainStack(app, 'test');
    const template = Template.fromStack(stack);
    const conditionRegion = template.toJSON()['Conditions']['CrossEventRegionCondition']["Fn::Not"]
    expect(conditionRegion).toEqual([{
        "Fn::Equals": [{
            "Ref": "AWS::Region"
        }, "us-west-2"]
    }])
})

test('EventBridgeRole has the right policy', () => {
    const app = new App();
    const stack = new MainStack(app, 'test');
    const template = Template.fromStack(stack);
    template.hasResourceProperties('AWS::IAM::Policy', {
        'PolicyDocument': {
            "Statement": [{
                "Action": "events:PutEvents",
                "Effect": "Allow",
                "Resource": {
                    "Fn::Join": [
                        "",
                        [
                            "arn:aws:events:",
                            {
                                "Ref": "AWS::Region"
                            },
                            ":",
                            {
                                "Ref": "AWS::AccountId"
                            },
                            ":event-bus/default"
                        ]
                    ]
                }
            }],
            "Version": "2012-10-17"
        }
    })
})

test('CreateEventRuleFunc has Environment Variables', () => {
    const app = new App();
    const stack = new MainStack(app, 'test');
    const template = Template.fromStack(stack);
    template.hasResourceProperties('AWS::Lambda::Function', {
        "Environment": {
            "Variables": {
                "EVENT_BRIDGE_ROLE_ARN": Match.anyValue(),
                "AWS_NODEJS_CONNECTION_REUSE_ENABLED": "1"
            }
        }
    })
})


test('CreateEventRuleFunc has the right policy', () => {
    const app = new App();
    const stack = new MainStack(app, 'test');
    const template = Template.fromStack(stack);
    template.hasResourceProperties('AWS::IAM::Policy', {
        "PolicyDocument": {
            "Statement": [{
                    "Action": [
                        "ec2:CreateNetworkInterface",
                        "ec2:DescribeNetworkInterfaces",
                        "ec2:DeleteNetworkInterface",
                        "ec2:AssignPrivateIpAddresses",
                        "ec2:UnassignPrivateIpAddresses"
                    ],
                    "Effect": "Allow",
                    "Resource": "*"
                },
                {
                    "Action": [
                        "logs:CreateLogStream",
                        "logs:PutLogEvents",
                        "logs:CreateLogGroup"
                    ],
                    "Effect": "Allow",
                    "Resource": {
                        "Fn::Join": [
                            "",
                            [
                                "arn:",
                                {
                                    "Ref": "AWS::Partition"
                                },
                                ":logs:",
                                {
                                    "Ref": "AWS::Region"
                                },
                                ":",
                                {
                                    "Ref": "AWS::AccountId"
                                },
                                ":log-group:*"
                            ]
                        ]
                    }
                },
                {
                    "Action": [
                        "events:DescribeRule",
                        "events:DeleteRule",
                        "events:PutTargets",
                        "events:EnableRule",
                        "events:PutRule",
                        "events:RemoveTargets",
                        "events:DisableRule"
                    ],
                    "Effect": "Allow",
                    "Resource": {
                        "Fn::Join": [
                            "",
                            [
                                "arn:",
                                {
                                    "Ref": "AWS::Partition"
                                },
                                ":events:us-west-2:",
                                {
                                    "Ref": "AWS::AccountId"
                                },
                                ":rule:*"
                            ]
                        ]
                    }
                },
                {
                    "Action": [
                        "cloudformation:CreateChangeSet",
                        "cloudformation:DeleteChangeSet",
                        "cloudformation:UpdateStack",
                        "cloudformation:DescribeChangeSet",
                        "cloudformation:ExecuteChangeSet",
                        "cloudformation:CreateStack",
                        "cloudformation:DeleteStack",
                        "cloudformation:DescribeStacks"
                    ],
                    "Effect": "Allow",
                    "Resource": {
                        "Fn::Join": [
                            "",
                            [
                                "arn:",
                                {
                                    "Ref": "AWS::Partition"
                                },
                                ":cloudformation:us-west-2:",
                                {
                                    "Ref": "AWS::AccountId"
                                },
                                ":stack:/QRSFDD-BraketEventTo",
                                {
                                    "Ref": "AWS::Region"
                                },
                                "/*"
                            ]
                        ]
                    }
                }
            ],
            "Version": "2012-10-17"
        }
    })
})