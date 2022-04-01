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

import { Template } from 'aws-cdk-lib/assertions';

import {
  MainStack,
} from '../src/molecular-unfolding/cdk/stack-main';

describe('Notebook', () => {
  test('has 1 notebook', () => {
    const app = new App();
    const stack = new MainStack(app, 'test');
    const template = Template.fromStack(stack);
    template.resourceCountIs('AWS::SageMaker::NotebookInstance', 1);
  });

  test('the notebook has a lifecycle', () => {
    const app = new App();
    const stack = new MainStack(app, 'test');
    const template = Template.fromStack(stack);
    template.resourceCountIs('AWS::SageMaker::NotebookInstanceLifecycleConfig', 1);
  });

});