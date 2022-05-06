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
  aws_s3 as s3,
  Stack,
} from 'aws-cdk-lib';

import { Template, Match } from 'aws-cdk-lib/assertions';

import {
  BatchEvaluationNestStack,
} from '../src/molecular-unfolding/cdk/statck-batch-evaluation';

import setup_vpc_and_sg from '../src/molecular-unfolding/cdk/utils/vpc';


describe('Listener', () => {
  test('Events Rule is configed correctly', () => {
    const app = new App();
    const stack = new Stack(app, 'test');
    const {
      vpc,
      batchSg,
      lambdaSg,
    } = setup_vpc_and_sg(stack);
    const s3bucket = new s3.Bucket(stack, 'amazon-braket-test');

    const nestStack = new BatchEvaluationNestStack(stack, 'BatchEvaluation', {
      account: '123456789012',
      region: 'us-east-1',
      bucket: s3bucket,
      prefix: 'test_s3_prefix',
      vpc,
      batchSg,
      lambdaSg,
      stackName: 'nestStack',
    });
    const template = Template.fromStack(nestStack);
    template.hasResourceProperties('AWS::Events::Rule', {
      EventPattern: Match.objectLike({
        'source': [
          'aws.braket',
        ],
        'detail-type': [
          'Braket Task State Change',
        ],
      }),
    });
  });
});