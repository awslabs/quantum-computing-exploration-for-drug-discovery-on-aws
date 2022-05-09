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
} from 'aws-cdk-lib/assertions';

import {
  NotebookNestStack,
} from '../src/molecular-unfolding/cdk/stack-notebook';

import setup_vpc_and_sg from '../src/molecular-unfolding/cdk/utils/vpc';


function initializeNestStackTemplate() {
  const app = new App();
  const stack = new Stack(app, 'test');

  const {
    vpc,
    batchSg,
  } = setup_vpc_and_sg(stack);

  const s3bucket = new s3.Bucket(stack, 'amazon-braket-test');
  const prefix = 'test_s3_prefix';
  const nestStack = new NotebookNestStack(stack, 'notebook', {
    prefix,
    bucket: s3bucket,
    batchSg,
    vpc,
    stackName: 'nestStack',
  });
  return Template.fromStack(nestStack);
}

describe('Notebook', () => {
  test('has 1 notebook', () => {
    const template = initializeNestStackTemplate();
    template.resourceCountIs('AWS::SageMaker::NotebookInstance', 1);
  });

  test('the notebook has a lifecycle', () => {
    const template = initializeNestStackTemplate();
    template.resourceCountIs('AWS::SageMaker::NotebookInstanceLifecycleConfig', 1);
  });

});