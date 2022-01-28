import * as cdk from 'aws-cdk-lib';
import {
  Stack
} from 'aws-cdk-lib';
import {
  Construct
} from 'constructs'

export default (scope: Construct) => {
  const account_id = Stack.of(scope).account

  const crossEventRegionCondition = new cdk.CfnCondition(scope, 'CrossEventRegionCondition', {
    expression: cdk.Fn.conditionNot(
      cdk.Fn.conditionEquals(cdk.Stack.of(scope).region, 'us-west-2'),
    ),
  });

  const provider = cdk.CustomResourceProvider.getOrCreateProvider(scope, 'Custom::CreateEventRule', {
    codeDirectory: `${__dirname}/custom-resource-lambda/create-event-rule`,
    runtime: cdk.CustomResourceProviderRuntime.NODEJS_14_X,
    timeout: cdk.Duration.minutes(5),
    policyStatements: [{
        Effect: 'Allow',
        Resource: [
          `arn:aws:iam::${account_id}:role/*`,
          `arn:aws:iam::${account_id}:policy/*`
        ],
        Action: [
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
      },
      {
        Effect: 'Allow',
        Resource: [
          `arn:aws:events:*:${account_id}:rule/*`
        ],
        Action: [
          "events:DescribeRule",
          "events:DeleteRule",
          "events:PutTargets",
          "events:EnableRule",
          "events:PutRule",
          "events:RemoveTargets",
          "events:DisableRule"
        ]
      },
      {
        Effect: 'Allow',
        Resource: [
          `arn:aws:cloudformation:*:${account_id}:stack/*/*`
        ],
        Action: [
          "cloudformation:CreateChangeSet",
          "cloudformation:DeleteChangeSet",
          "cloudformation:UpdateStack",
          "cloudformation:DescribeChangeSet",
          "cloudformation:ExecuteChangeSet",
          "cloudformation:CreateStack",
          "cloudformation:DeleteStack",
          "cloudformation:DescribeStacks"
        ]
      }
    ]
  });

  const createEventRuleCustomResource = new cdk.CustomResource(scope, 'CreateEventRuleCustomResource', {
    serviceToken: provider.serviceToken
  });

  (createEventRuleCustomResource.node.defaultChild as cdk.CfnCustomResource).cfnOptions.condition = crossEventRegionCondition;
  (provider.node.children[1] as cdk.CfnResource).cfnOptions.condition = crossEventRegionCondition;
  (provider.node.children[2] as cdk.CfnResource).cfnOptions.condition = crossEventRegionCondition;

}