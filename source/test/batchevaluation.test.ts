/*
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/

import {
  App,
  Stack,
  aws_s3 as s3,
} from 'aws-cdk-lib';

import {
  Template,
  Match,
  Capture,
} from 'aws-cdk-lib/assertions';

import {
  BatchEvaluationNestStack,
} from '../src/molecular-unfolding/cdk/statck-batch-evaluation';

import setup_vpc_and_sg from '../src/molecular-unfolding/cdk/utils/vpc';

function initializeNestStackTemplate() {
  const app = new App();
  const stack = new Stack(app, 'test');

  const {
    vpc,
    batchSg,
    lambdaSg,
  } = setup_vpc_and_sg(stack);

  const s3bucket = new s3.Bucket(stack, 'amazon-braket-test');
  const prefix = 'test_s3_prefix';
  const nestStack = new BatchEvaluationNestStack(stack, 'BatchEvaluation', {
    account: '123456789012',
    region: 'us-east-1',
    prefix,
    bucket: s3bucket,
    vpc,
    batchSg,
    lambdaSg,
    stackName: 'nestStack',
  });
  return Template.fromStack(nestStack);
}


describe('BatchEvaluation', () => {
  test('has 1 batch ComputeEnvironment', () => {
    const template = initializeNestStackTemplate();
    template.resourceCountIs('AWS::Batch::ComputeEnvironment', 2);
  });

  test('has 1 batch JobQueue', () => {
    const template = initializeNestStackTemplate();
    template.resourceCountIs('AWS::Batch::JobQueue', 2);
  });
  test('has 2 batch JobDefinitions', () => {
    const template = initializeNestStackTemplate();
    template.resourceCountIs('AWS::Batch::JobDefinition', 3);
  });

  test('has 1 SNS', () => {
    const template = initializeNestStackTemplate();
    template.resourceCountIs('AWS::SNS::Topic', 1);
  });

  test('StateMachine count is 5', () => {
    const template = initializeNestStackTemplate();
    //const startAtCapture = new Capture();
    //const statesCapture = new Capture();

    template.resourceCountIs('AWS::StepFunctions::StateMachine', 5);
  });

  test('CreateEventRuleFuncServiceRole has CrossEventRegionCondition', () => {
    const template = initializeNestStackTemplate();
    const findRoles = template.findResources('AWS::IAM::Role', {
      Condition: 'CrossEventRegionCondition',
    });
    let conditionSet = false;
    for (const p in findRoles) {
      if (p.startsWith('CreateEventRuleFuncServiceRole')) {
        conditionSet = true;
        break;
      }
    }
    expect(conditionSet).toBeTruthy();
  });

  test('has 1 CustomResource', () => {
    const template = initializeNestStackTemplate();
    template.hasResource('AWS::CloudFormation::CustomResource', 1);
  });

  test('The CustomResource has Condition', () => {
    const template = initializeNestStackTemplate();

    template.hasResource('AWS::CloudFormation::CustomResource', {
      Condition: 'CrossEventRegionCondition',
    });
  });


  test('CreateEventRuleFunc has Environment Variables', () => {
    const template = initializeNestStackTemplate();
    template.hasResourceProperties('AWS::Lambda::Function', {
      Environment: {
        Variables: {
          EVENT_BRIDGE_ROLE_ARN: Match.anyValue(),
          AWS_NODEJS_CONNECTION_REUSE_ENABLED: '1',
        },
      },
    });
  });

  test('CrossEventRegionCondition is for us-west-2', () => {
    const template = initializeNestStackTemplate();
    const conditionRegion = template.toJSON().Conditions.CrossEventRegionCondition['Fn::Not'];
    expect(conditionRegion).toEqual([{
      'Fn::Equals': [{
        Ref: 'AWS::Region',
      }, 'us-west-2'],
    }]);
  });


  test('EventBridgeRole has the right policy', () => {
    const template = initializeNestStackTemplate();
    template.hasResourceProperties('AWS::IAM::Policy', {
      PolicyDocument: {
        Statement: [{
          Action: 'events:PutEvents',
          Effect: 'Allow',
          Resource: {
            'Fn::Join': [
              '',
              [
                'arn:',
                {
                  Ref: 'AWS::Partition',
                },
                ':events:',
                {
                  Ref: 'AWS::Region',
                },
                ':',
                {
                  Ref: 'AWS::AccountId',
                },
                ':event-bus/default',
              ],
            ],
          },
        }],
        Version: '2012-10-17',
      },
    });
  });

  test('CreateEventRuleFunc has the right policy', () => {
    const roleCapture = new Capture();
    const template = initializeNestStackTemplate();
    template.hasResourceProperties('AWS::IAM::Policy', {
      PolicyDocument: {
        Statement: [{
          Action: [
            'events:DescribeRule',
            'events:DeleteRule',
            'events:PutTargets',
            'events:EnableRule',
            'events:PutRule',
            'events:RemoveTargets',
            'events:DisableRule',
          ],
          Effect: 'Allow',
          Resource: {
            'Fn::Join': [
              '',
              [
                'arn:',
                {
                  Ref: 'AWS::Partition',
                },
                ':events:us-west-2:',
                {
                  Ref: 'AWS::AccountId',
                },
                ':rule/QCEDD-BraketEventTo',
                {
                  Ref: 'AWS::Region',
                },
                '*',
              ],
            ],
          },
        },
        {
          Action: [
            'cloudformation:CreateChangeSet',
            'cloudformation:DeleteChangeSet',
            'cloudformation:DescribeChangeSet',
            'cloudformation:ExecuteChangeSet',
            'cloudformation:UpdateStack',
            'cloudformation:DeleteStack',
            'cloudformation:CreateStack',
            'cloudformation:DescribeStacks',
          ],
          Effect: 'Allow',
          Resource: {
            'Fn::Join': [
              '',
              [
                'arn:',
                {
                  Ref: 'AWS::Partition',
                },
                ':cloudformation:us-west-2:',
                {
                  Ref: 'AWS::AccountId',
                },
                ':stack/QCEDD-BraketEventTo',
                {
                  Ref: 'AWS::Region',
                },
                '/*',
              ],
            ],
          },
        },
        {
          Action: 'iam:PassRole',
          Effect: 'Allow',
          Resource: {
            'Fn::GetAtt': [
              roleCapture,
              'Arn',
            ],
          },
        }],
        Version: '2012-10-17',
      },

    });
    expect(roleCapture.asString()).toEqual(expect.stringMatching(/^EventBridgeRole/));

  });

  test('CC StateMachine', () => {
    const template = initializeNestStackTemplate();
    //const startAtCapture = new Capture();
    //const statesCapture = new Capture();

    template.hasResourceProperties('AWS::StepFunctions::StateMachine', {
      DefinitionString: Match.objectLike({
        'Fn::Join': [
          '',
          [
            '{"StartAt":"Get Task Parameters","States":{"Get Task Parameters":{"Next":"ParallelCCJobs","Retry":[{"ErrorEquals":["Lambda.ServiceException","Lambda.AWSLambdaException","Lambda.SdkClientException"],"IntervalSeconds":2,"MaxAttempts":6,"BackoffRate":2}],"Type":"Task","OutputPath":"$.Payload","Resource":"arn:',
            {
              Ref: 'AWS::Partition',
            },
            ':states:::lambda:invoke","Parameters":{"FunctionName":"',
            {
              'Fn::GetAtt': [
                Match.anyValue(),
                'Arn',
              ],
            },
            '","Payload":{"s3_bucket":"',
            {
              Ref: Match.anyValue(),
            },
            '","s3_prefix":"test_s3_prefix","param_type":"PARAMS_FOR_CC","execution_id.$":"$.execution_id","context.$":"$$"}}},"ParallelCCJobs":{"Type":"Map","ResultPath":"$.parallelCCJobsMap","End":true,"Parameters":{"ItemIndex.$":"$$.Map.Item.Index","ItemValue.$":"$$.Map.Item.Value","execution_id.$":"$.execution_id"},"Iterator":{"StartAt":"Run CC Batch Job","States":{"Run CC Batch Job":{"Next":"Batch Job Complete","Type":"Task","Resource":"arn:aws:states:::batch:submitJob.sync","Parameters":{"JobDefinition":"',
            {
              Ref: Match.anyValue(),
            },
            "\",\"JobName.$\":\"States.Format('CCTask{}-{}', $.ItemIndex, $.ItemValue.task_name)\",\"JobQueue\":\"",
            {
              Ref: Match.anyValue(),
            },
            "\",\"ContainerOverrides\":{\"Command.$\":\"$.ItemValue.params\",\"ResourceRequirements\":[{\"Type\":\"VCPU\",\"Value.$\":\"States.Format('{}',$.ItemValue.vcpus)\"},{\"Type\":\"MEMORY\",\"Value.$\":\"States.Format('{}', $.ItemValue.memory)\"}]}},\"Catch\":[{\"ErrorEquals\":[\"States.TaskFailed\"],\"Next\":\"Batch Job Complete\"}],\"ResultSelector\":{\"JobId.$\":\"$.JobId\",\"JobName.$\":\"$.JobName\"}},\"Batch Job Complete\":{\"Type\":\"Pass\",\"End\":true}}},\"ItemsPath\":\"$.ccTaskParams\",\"MaxConcurrency\":20}}}",
          ],
        ],
      }),
    });
  });

  test('has lambdas with image package type', () => {
    const template = initializeNestStackTemplate();
    //const startAtCapture = new Capture();
    //const statesCapture = new Capture();

    template.hasResourceProperties('AWS::Lambda::Function', {
      PackageType: 'Image',
    });
  });

  test('has lambdas in vpc', () => {
    const template = initializeNestStackTemplate();
    //const startAtCapture = new Capture();
    //const statesCapture = new Capture();

    template.hasResourceProperties('AWS::Lambda::Function', {
      VpcConfig: Match.anyValue(),
    });
  });

  test('BatchEcsInstanceRole has SSM permission', () => {
    const template = initializeNestStackTemplate();
    const findRoles = template.findResources('AWS::IAM::Role', {
      Properties: {
        AssumeRolePolicyDocument: Match.anyValue(),
        ManagedPolicyArns: Match.anyValue(),
      },
    });

    let SSMSet = false;
    for (const role in findRoles) {
      if (role.startsWith('BatchCCComputeEnvEcsInstanceRole')) {
        for (const arn of findRoles[role].Properties.ManagedPolicyArns) {
          if ('Fn::Join' in arn) {
            const policyName = arn['Fn::Join'][1][2];
            if (policyName.indexOf(':iam::aws:policy/AmazonSSMManagedInstanceCore') > -1) {
              SSMSet = true;
            }
          }
        }
      }
    }
    expect(SSMSet).toBeTruthy();
  });


  test('AWS Events Rule is configed for stepFunctions', () => {
    const template = initializeNestStackTemplate();
    const nameCapture = new Capture();
    template.hasResourceProperties('AWS::Events::Rule', {
      EventPattern: {
        'source': [
          'aws.states',
        ],
        'detail-type': [
          'Step Functions Execution Status Change',
        ],
        'detail': {
          status: [
            'FAILED',
            'TIMED_OUT',
            'ABORTED',
          ],
          stateMachineArn: [{
            Ref: nameCapture,
          }],
        },
      },
    });

    expect(nameCapture.asString()).toEqual(expect.stringMatching(/BatchEvaluationStateMachine/));

  });

  test('SNS Key permission is configed correctly', () => {
    const template = initializeNestStackTemplate();
    template.hasResourceProperties('AWS::KMS::Key', {
      KeyPolicy: {
        Statement: [{
          Action: 'kms:*',
          Effect: 'Allow',
          Principal: {
            AWS: {
              'Fn::Join': [
                '',
                [
                  'arn:',
                  {
                    Ref: 'AWS::Partition',
                  },
                  ':iam::',
                  {
                    Ref: 'AWS::AccountId',
                  },
                  ':root',
                ],
              ],
            },
          },
          Resource: '*',
        },
        {
          Action: [
            'kms:Decrypt',
            'kms:GenerateDataKey',
          ],
          Effect: 'Allow',
          Principal: {
            Service: 'events.amazonaws.com',
          },
          Resource: '*',
        },
        {
          Action: [
            'kms:Decrypt',
            'kms:GenerateDataKey*',
            'kms:CreateGrant',
            'kms:ListGrants',
            'kms:DescribeKey',
          ],
          Condition: {
            StringEquals: {
              'kms:ViaService': {
                'Fn::Join': [
                  '',
                  [
                    'sns.',
                    {
                      Ref: 'AWS::Region',
                    },
                    '.amazonaws.com',
                  ],
                ],
              },
              'kms:CallerAccount': {
                Ref: 'AWS::AccountId',
              },
            },
          },
          Effect: 'Allow',
          Principal: {
            AWS: '*',
          },
          Resource: '*',
        }],
        Version: '2012-10-17',
      },
    });
  });
});


