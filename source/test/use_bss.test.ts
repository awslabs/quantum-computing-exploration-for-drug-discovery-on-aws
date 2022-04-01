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
  Aspects,
} from 'aws-cdk-lib';

import {
  Template,
  Match,
  Capture,
} from 'aws-cdk-lib/assertions';

import {
  BootstraplessStackSynthesizer,
  BatchJobDefinition,
} from 'cdk-bootstrapless-synthesizer';
import {
  MainStack,
} from '../src/molecular-unfolding/cdk/stack-main';


function newSynthesizer() {
  return process.env.USE_BSS ? new BootstraplessStackSynthesizer() : undefined;
}

beforeAll(() => {
  const env = process.env;
  env.USE_BSS = 'true';
  env.BSS_TEMPLATE_BUCKET_NAME = 'cfn-template-bucket';
  env.BSS_FILE_ASSET_BUCKET_NAME = 'file-asset-bucket-us-west-2';
  env.BSS_FILE_ASSET_REGION_SET = 'us-west-1,us-west-2';
  env.BSS_FILE_ASSET_PREFIX = 'file-asset-prefix/latest/';
  env.BSS_IMAGE_ASSET_REPOSITORY_NAME = 'testRepo';
  env.BSS_IMAGE_ASSET_ACCOUNT_ID = '123456789012';
  env.BSS_IMAGE_ASSET_TAG_PREFIX = 'latest-';
  env.BSS_IMAGE_ASSET_REGION_SET = 'us-west-1,us-west-2';
});

afterAll(() => {
  const env = process.env;
  delete env.USE_BSS;
});


test('Policy of batch execution role is generated correctly when USE_BSS = true', () => {

  const app = new App();
  const stack = new MainStack(app, 'test', {
    synthesizer: newSynthesizer(),
  });

  if (process.env.USE_BSS) {
    Aspects.of(app).add(new BatchJobDefinition());
  }

  const template = Template.fromStack(stack);
  const nameCapture = new Capture();

  template.hasResourceProperties('AWS::IAM::Policy', {
    PolicyDocument: {
      Statement: [{
        Action: [
          'ecr:BatchCheckLayerAvailability',
          'ecr:GetDownloadUrlForLayer',
          'ecr:BatchGetImage',
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
              ':ecr:',
              {
                Ref: 'AWS::Region',
              },
              ':123456789012:repository/testRepo',
            ],
          ],
        },
      }],
      Version: '2012-10-17',
    },
    PolicyName: Match.anyValue(),
    Roles: [{
      Ref: nameCapture,
    }],
  });
  expect(nameCapture.asString()).toEqual(expect.stringMatching(/^batchExecutionRole/));

});