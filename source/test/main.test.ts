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
} from 'aws-cdk-lib/assertions';

import {
  MainStack,
} from '../src/molecular-unfolding/cdk/stack-main';
import {
  SolutionStack,
} from '../src/stack';


test('can create base stack', () => {
  const app = new App();
  const stack = new SolutionStack(app, 'test');
  Template.fromStack(stack);
});

test('can create MainStack', () => {
  const app = new App();
  const stack = new MainStack(app, 'test');
  expect(stack).not.toBeNull();
});

test('synthesizes the way we expect', () => {
  const app = new App();
  const stack = new MainStack(app, 'test');
  const template = Template.fromStack(stack);
  expect(template).toBeTruthy();
});

test('has 1 s3 bucket', () => {
  const app = new App();
  const stack = new MainStack(app, 'test');
  const template = Template.fromStack(stack);
  template.hasResource('AWS::S3::Bucket', 1);
});

test('s3 bucket can be deleted', () => {
  const app = new App();
  const stack = new MainStack(app, 'test');
  const template = Template.fromStack(stack);
  template.hasResource('Custom::S3AutoDeleteObjects', 1);
});

test('has 1 vpc', () => {
  const app = new App();
  const stack = new MainStack(app, 'test');
  const template = Template.fromStack(stack);
  template.hasResource('AWS::EC2::VPC', 1);
});

test('has 4 subnets', () => {
  const app = new App();
  const stack = new MainStack(app, 'test');
  const template = Template.fromStack(stack);
  template.hasResource('AWS::EC2::Subnet', 4);
});

test('has 1 flowLog', () => {
  const app = new App();
  const stack = new MainStack(app, 'test');
  const template = Template.fromStack(stack);
  template.hasResource('AWS::EC2::FlowLog', 1);
});

test('has output - BucketName', () => {
  const app = new App();
  const stack = new MainStack(app, 'test');
  const template = Template.fromStack(stack);
  template.hasOutput('BucketName', {});
});

test('has output - NotebookUrl', () => {
  const app = new App();
  const stack = new MainStack(app, 'test');
  const template = Template.fromStack(stack);
  template.hasOutput('NotebookUrl', {});
});

test('has output - SNSTopic', () => {
  const app = new App();
  const stack = new MainStack(app, 'test');
  const template = Template.fromStack(stack);
  template.hasOutput('SNSTopic', {});
});


test('has output - StateMachineURL', () => {
  const app = new App();
  const stack = new MainStack(app, 'test');
  const template = Template.fromStack(stack);
  template.hasOutput('StateMachineURL', {});
});

test('has 2 nest CloudFormation stacks ', () => {
  const app = new App();
  const stack = new MainStack(app, 'test');
  const template = Template.fromStack(stack);
  template.hasResource('AWS::CloudFormation::Stack', 2);
});

test('has Condition ConditionDeployBatchEvaluation', () => {
  const app = new App();
  const stack = new MainStack(app, 'test');
  const template = Template.fromStack(stack);
  const conditionDeployBatchEvaluation = template.toJSON().Conditions.ConditionDeployBatchEvaluation;
  expect(conditionDeployBatchEvaluation).toEqual({
    'Fn::Equals': [
      {
        Ref: 'DeployBatchEvaluation',
      },
      'yes',
    ],
  });
});

test('has Condition ConditionDeployVisualization', () => {
  const app = new App();
  const stack = new MainStack(app, 'test');
  const template = Template.fromStack(stack);
  const conditionDeployVisualization = template.toJSON().Conditions.ConditionDeployVisualization;
  expect(conditionDeployVisualization).toEqual({
    'Fn::Equals': [
      {
        Ref: 'DeployVisualization',
      },
      'yes',
    ],
  });
});

test('SupportedRegionsRule config correctly', () => {
  const app = new App();
  const stack = new MainStack(app, 'test');
  const template = Template.fromStack(stack);

  const supportedRegions = template.toJSON().Rules.SupportedRegionsRule.Assertions;
  expect(supportedRegions).toEqual(
    [
      {
        Assert: { 'Fn::Contains': [['us-west-2', 'us-east-1', 'eu-west-2'], { Ref: 'AWS::Region' }] },
        AssertDescription: 'supported regions are us-west-2, us-east-1, eu-west-2',
      },
    ],
  );
});
