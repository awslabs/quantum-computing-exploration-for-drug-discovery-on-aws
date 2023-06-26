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
  App, Aspects,
} from 'aws-cdk-lib';


import {
  BootstraplessStackSynthesizer, CompositeECRRepositoryAspect,
} from 'cdk-bootstrapless-synthesizer';

import {
  AwsSolutionsChecks, NagSuppressions,
} from 'cdk-nag';

import {
  MainStack,
} from './cdk/stack-main';


const app = new App();

NagSuppressions.addStackSuppressions(new MainStack(app, 'QCEDDStack', {
  synthesizer: newSynthesizer(),
}), [
  { id: 'AwsSolutions-IAM4', reason: 'these policies is used by CDK Customer Resource lambda' },
  { id: 'AwsSolutions-IAM5', reason: 'Some roles and policies need to get dynamic resources' },
  { id: 'AwsSolutions-L1', reason: 'The custom resource runtime version is not latest' },
  { id: 'AwsSolutions-SM1', reason: 'The latest version is no need to use VPC' },
  { id: 'AwsSolutions-SM3', reason: 'The custom resource need to access directly' },
], true);

Aspects.of(app).add(new AwsSolutionsChecks());

if (process.env.USE_BSS) {
  Aspects.of(app).add(new CompositeECRRepositoryAspect());
}

app.synth();

function newSynthesizer() {
  return process.env.USE_BSS ? new BootstraplessStackSynthesizer() : undefined;
}