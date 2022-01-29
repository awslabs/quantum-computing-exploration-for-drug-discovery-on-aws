import * as cdk from 'aws-cdk-lib';
import {
  Stack
} from 'aws-cdk-lib';
import {
  Construct
} from 'constructs'

import {
  aws_iam as iam
} from 'aws-cdk-lib'

import {
  aws_ec2 as ec2
} from 'aws-cdk-lib'

import {
  NodejsFunction
} from 'aws-cdk-lib/aws-lambda-nodejs';

import {
  Runtime
} from 'aws-cdk-lib/aws-lambda';

import {
  Provider
} from 'aws-cdk-lib/custom-resources';


function createCustomResourceLambdaRole(scope: Construct, roleName: string): iam.Role {
  const account_id = Stack.of(scope).account

  const role = new iam.Role(scope, `${roleName}`, {
    assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
  });

  role.addToPolicy(new iam.PolicyStatement({
    effect: iam.Effect.ALLOW,
    resources: [
      '*'
    ],
    actions: [
      "ec2:CreateNetworkInterface",
      "ec2:DescribeNetworkInterfaces",
      "ec2:DeleteNetworkInterface",
      "ec2:AssignPrivateIpAddresses",
      "ec2:UnassignPrivateIpAddresses"
    ]
  }));

  role.addToPolicy(new iam.PolicyStatement({
    resources: [
      `arn:aws:logs:*:${account_id}:log-group:*`
    ],
    actions: [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:CreateLogGroup"
    ]
  }));

  role.addToPolicy(new iam.PolicyStatement({
    resources: [
      `arn:aws:iam::${account_id}:role/*`,
      `arn:aws:iam::${account_id}:policy/*`
    ],
    actions: [
      "iam:DetachRolePolicy",
      "iam:DeleteRolePolicy",
      "iam:CreateRole",
      "iam:DeleteRole",
      "iam:AttachRolePolicy",
      "iam:UpdateRole",
      "iam:PutRolePolicy",
      "iam:CreatePolicy",
      "iam:DeletePolicy",
      "iam:GetRole",
      "iam:GetPolicy",
      "iam:PassRole",
    ]
  }));

  role.addToPolicy(new iam.PolicyStatement({
    resources: [
      `arn:aws:events:*:${account_id}:rule/*`
    ],
    actions: [
      "events:DescribeRule",
      "events:DeleteRule",
      "events:PutTargets",
      "events:EnableRule",
      "events:PutRule",
      "events:RemoveTargets",
      "events:DisableRule"
    ]
  }));

  role.addToPolicy(new iam.PolicyStatement({
    resources: [
      `arn:aws:cloudformation:*:${account_id}:stack/*/*`
    ],
    actions: [
      "cloudformation:CreateChangeSet",
      "cloudformation:DeleteChangeSet",
      "cloudformation:UpdateStack",
      "cloudformation:DescribeChangeSet",
      "cloudformation:ExecuteChangeSet",
      "cloudformation:CreateStack",
      "cloudformation:DeleteStack",
      "cloudformation:DescribeStacks"
    ]
  }));

  return role;
}

interface Props {
  crossEventRegionCondition: cdk.CfnCondition;
  vpc: ec2.Vpc;
  sg: ec2.SecurityGroup
}

export default (scope: Construct, props: Props) => {

  const template_file = 'src/molecule-unfolding/cdk/utils/custom-resource-lambda/create-event-rule/template.json'

  const role = createCustomResourceLambdaRole(scope, 'CreateEventRuleFuncRole')

  const createEventRuleFunc = new NodejsFunction(scope, 'CreateEventRuleFunc', {
    entry: `${__dirname}/custom-resource-lambda/create-event-rule/index.js`,
    handler: 'handler',
    timeout: cdk.Duration.minutes(5),
    memorySize: 256,
    runtime: Runtime.NODEJS_12_X,
    reservedConcurrentExecutions: 5,
    role,
    vpc: props.vpc,
    securityGroups: [props.sg],
    vpcSubnets: props.vpc.selectSubnets({
      subnetType: ec2.SubnetType.PRIVATE_WITH_NAT
    }),

    bundling: {
      commandHooks: {
        beforeBundling(inputDir: string, outputDir: string): string[] {
          return [
            `cp ${inputDir}/${template_file} ${outputDir}`,
          ];
        },
        afterBundling(_inputDir: string, _outputDir: string): string[] {
          return [];
        },
        beforeInstall() {
          return [];
        },
      },
    }

  });

  const provider = new Provider(
    scope,
    'EventRuleCustomResourceProvider', {
      onEventHandler: createEventRuleFunc
    },
  );

  const createEventRuleCustomResource = new cdk.CustomResource(scope, 'CreateEventRuleCustomResource', {
    serviceToken: provider.serviceToken
  });

  (createEventRuleCustomResource.node.defaultChild as cdk.CfnCustomResource).cfnOptions.condition = props.crossEventRegionCondition;
  (createEventRuleFunc.node.defaultChild as cdk.CfnCustomResource).cfnOptions.condition = props.crossEventRegionCondition;
  (role.node.defaultChild as cdk.CfnCustomResource).cfnOptions.condition = props.crossEventRegionCondition;
}