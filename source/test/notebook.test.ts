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