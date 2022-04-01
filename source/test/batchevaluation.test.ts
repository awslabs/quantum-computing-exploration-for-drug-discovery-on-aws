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
} from 'aws-cdk-lib';

import {
  Template,
  Match,
  Capture,
} from 'aws-cdk-lib/assertions';

import {
  MainStack,
} from '../src/molecular-unfolding/cdk/stack-main';

describe('BatchEvaluation', () => {
  test('has 1 batch ComputeEnvironment', () => {
    const app = new App();
    const stack = new MainStack(app, 'test');
    const template = Template.fromStack(stack);
    template.resourceCountIs('AWS::Batch::ComputeEnvironment', 2);
  });

  test('has 1 batch JobQueue', () => {
    const app = new App();
    const stack = new MainStack(app, 'test');
    const template = Template.fromStack(stack);
    template.resourceCountIs('AWS::Batch::JobQueue', 2);
  });
  test('has 2 batch JobDefinitions', () => {
    const app = new App();
    const stack = new MainStack(app, 'test');
    const template = Template.fromStack(stack);
    template.resourceCountIs('AWS::Batch::JobDefinition', 3);
  });

  test('has 1 SNS', () => {
    const app = new App();
    const stack = new MainStack(app, 'test');
    const template = Template.fromStack(stack);
    template.resourceCountIs('AWS::SNS::Topic', 1);
  });

  test('bechmark StateMachine', () => {
    const app = new App();
    const stack = new MainStack(app, 'test');
    const template = Template.fromStack(stack);
    //const startAtCapture = new Capture();
    //const statesCapture = new Capture();

    template.resourceCountIs('AWS::StepFunctions::StateMachine', 5);
  });


  test('bechmark main StateMachine', () => {
    const app = new App();
    const stack = new MainStack(app, 'test');
    const template = Template.fromStack(stack);
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
            '","s3_prefix":"molecular-unfolding","param_type":"PARAMS_FOR_CC","execution_id.$":"$.execution_id","context.$":"$$"}}},"ParallelCCJobs":{"Type":"Map","ResultPath":"$.parallelCCJobsMap","End":true,"Parameters":{"ItemIndex.$":"$$.Map.Item.Index","ItemValue.$":"$$.Map.Item.Value","execution_id.$":"$.execution_id"},"Iterator":{"StartAt":"Run CC Batch Task","States":{"Run CC Batch Task":{"End":true,"Type":"Task","Resource":"arn:aws:states:::batch:submitJob.sync","Parameters":{"JobDefinition":"',
            {
              Ref: Match.anyValue(),
            },
            "\",\"JobName.$\":\"States.Format('CCTask{}-{}', $.ItemIndex, $.ItemValue.task_name)\",\"JobQueue\":\"",
            {
              Ref: Match.anyValue(),
            },
            "\",\"ContainerOverrides\":{\"Command.$\":\"$.ItemValue.params\",\"ResourceRequirements\":[{\"Type\":\"VCPU\",\"Value.$\":\"States.Format('{}',$.ItemValue.vcpus)\"},{\"Type\":\"MEMORY\",\"Value.$\":\"States.Format('{}', $.ItemValue.memory)\"}]}},\"ResultSelector\":{\"JobId.$\":\"$.JobId\",\"JobName.$\":\"$.JobName\"}}}},\"ItemsPath\":\"$.ccTaskParams\",\"MaxConcurrency\":20}}}",
          ],
        ],
      }),
    });
  });

  test('has lambdas with image package type', () => {
    const app = new App();
    const stack = new MainStack(app, 'test');
    const template = Template.fromStack(stack);
    //const startAtCapture = new Capture();
    //const statesCapture = new Capture();

    template.hasResourceProperties('AWS::Lambda::Function', {
      PackageType: 'Image',
    });
  });

  test('has lambdas in vpc', () => {
    const app = new App();
    const stack = new MainStack(app, 'test');
    const template = Template.fromStack(stack);
    //const startAtCapture = new Capture();
    //const statesCapture = new Capture();

    template.hasResourceProperties('AWS::Lambda::Function', {
      VpcConfig: Match.anyValue(),
    });
  });

  test('BatchEcsInstanceRole has SSM permission', ()=> {
    const app = new App();
    const stack = new MainStack(app, 'test');
    const template = Template.fromStack(stack);
    const findRoles = template.findResources('AWS::IAM::Role', {
      DependsOn: Match.anyValue(),
      Properties: {
        AssumeRolePolicyDocument: Match.anyValue(),
        ManagedPolicyArns: Match.anyValue(),
      },
    });

    let SSMSet = false;
    for (const role in findRoles ) {
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


  test('AWS Events Rule is configed for stepFunctions', ()=> {
    const app = new App();
    const stack = new MainStack(app, 'test');
    const template = Template.fromStack(stack);
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
          stateMachineArn: [
            {
              Ref: nameCapture,
            },
          ],
        },
      },
    });

    expect(nameCapture.asString()).toEqual(expect.stringMatching(/BatchEvaluationStateMachine/));

  });

  test('SNS Key permission is configed correctly', ()=> {
    const app = new App();
    const stack = new MainStack(app, 'test');
    const template = Template.fromStack(stack);
    template.hasResourceProperties('AWS::KMS::Key', {
      KeyPolicy: {
        Statement: [
          {
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
          },
        ],
        Version: '2012-10-17',
      },
    });

  });

});