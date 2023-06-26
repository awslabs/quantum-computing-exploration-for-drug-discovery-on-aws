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
} from '../src/cdk/stack-main';

test('can create MainStack', () => {
  const app = new App();
  const stack = new MainStack(app, 'test', {});
  expect(stack).not.toBeNull();
});

test('synthesizes the way we expect', () => {
  const app = new App();
  const stack = new MainStack(app, 'test');
  const template = Template.fromStack(stack);
  expect(template).toBeTruthy();
});


test('has 1 parameter', () => {
  const app = new App();
  const stack = new MainStack(app, 'test');
  const template = Template.fromStack(stack);
  template.hasParameter('snsEmail', 1);
});

test('has 1 eventBridge', () => {
  const app = new App();
  const stack = new MainStack(app, 'test');
  const template = Template.fromStack(stack);
  template.hasResource('AWS::Events::Rule', 1);
});

test('has output - NotebookURL', () => {
  const app = new App();
  const stack = new MainStack(app, 'test');
  const template = Template.fromStack(stack);
  template.hasOutput('NotebookURL', {});
});

test('has output - SNSTopic', () => {
  const app = new App();
  const stack = new MainStack(app, 'test');
  const template = Template.fromStack(stack);
  template.hasOutput('SNSTopic', {});
});

test('subscription success - email', () => {
  const app = new App();
  const stack = new MainStack(app, 'test');
  const template = Template.fromStack(stack);
  template.hasResource('AWS::SNS::Topic', 1);
});


test('SupportedRegionsRule config correctly', () => {
  const app = new App();
  const stack = new MainStack(app, 'test');
  const template = Template.fromStack(stack);

  const supportedRegions = template.toJSON().Rules.SupportedRegionsRule.Assertions;
  expect(supportedRegions).toEqual(
    [
      {
        Assert: { 'Fn::Contains': [['us-west-1', 'us-west-2', 'us-east-1', 'eu-west-2'], { Ref: 'AWS::Region' }] },
        AssertDescription: 'supported regions are us-west-1, us-west-2, us-east-1, eu-west-2',
      },
    ],
  );
});
