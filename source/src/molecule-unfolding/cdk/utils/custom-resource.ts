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


export default (scope: Construct) => {
  const template_file = 'src/molecule-unfolding/cdk/utils/custom-resource-lambda/create-event-rule/template.json'
  const crossEventRegionCondition = new cdk.CfnCondition(scope, 'CrossEventRegionCondition', {
    expression: cdk.Fn.conditionNot(
      cdk.Fn.conditionEquals(cdk.Stack.of(scope).region, 'us-west-2'),
    ),
  });
  const role = createCustomResourceLambdaRole(scope, 'CreateEventRuleFuncRole')
  const createEventRuleFunc = new NodejsFunction(scope, 'CreateEventRuleFunc', {
    entry: `${__dirname}/custom-resource-lambda/create-event-rule/index.js`,
    handler: 'handler',
    timeout: cdk.Duration.minutes(5),
    memorySize: 256,
    runtime: Runtime.NODEJS_14_X,
    reservedConcurrentExecutions: 5,
    role,
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

  (createEventRuleCustomResource.node.defaultChild as cdk.CfnCustomResource).cfnOptions.condition = crossEventRegionCondition;
  (createEventRuleFunc.node.defaultChild as cdk.CfnCustomResource).cfnOptions.condition = crossEventRegionCondition;
  (role.node.defaultChild as cdk.CfnCustomResource).cfnOptions.condition = crossEventRegionCondition;

}