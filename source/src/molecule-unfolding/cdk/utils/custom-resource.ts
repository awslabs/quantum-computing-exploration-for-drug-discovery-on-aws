import * as cdk from 'aws-cdk-lib';
import { Stack } from 'aws-cdk-lib';
import {
    Construct
  } from 'constructs'

export default (scope: Construct) => {
    const account_id = Stack.of(scope).account
    const region = Stack.of(scope).region

    if (region == 'us-west-2') {
        return
    }
    
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
              "events:DeleteRule",
              "events:PutTargets",
              "events:EnableRule",
              "events:PutRule",
              "events:RemoveTargets",
              "events:DisableRule"
            ]
          }
        ]
      });
      new cdk.CustomResource(scope, 'CreateEventRuleCustomResource', {
        serviceToken: provider.serviceToken
      });
    }