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
  StackProps,
  Fn,
  CfnRule,
  CfnParameter,
} from 'aws-cdk-lib';

import {
  Construct,
} from 'constructs';

import {
  SolutionStack,
} from '../../stack';

import {
  Dashboard,
} from './construct-dashboard';


export class DashboardStack extends SolutionStack {
  static SOLUTION_ID = 'SO8027'
  static SOLUTION_VERSION = process.env.SOLUTION_VERSION || 'v1.0.0'

  // constructor
  constructor(scope: Construct, id: string, props: StackProps = {}) {
    const DESCRIPTION = `(${DashboardStack.SOLUTION_ID}) Quantum Computing Exploration for Drug Discovery on AWS ${DashboardStack.SOLUTION_VERSION} Dashboard Stack`;
    super(scope, id, props);
    this.setDescription(DESCRIPTION);
    const stackName = this.stackName.replace(/[^a-zA-Z0-9_]+/, '').toLocaleLowerCase();

    const supportRegions = ['us-west-2', 'us-east-1', 'eu-west-2'];
    new CfnRule(this, 'SupportedRegionsRule', {
      assertions: [{
        assert: Fn.conditionContains(supportRegions, this.region),
        assertDescription: 'supported regions are ' + supportRegions.join(', '),
      }],
    });

    const quickSightUserParam = new CfnParameter(this, 'QuickSightUser', {
      type: 'String',
      description: 'QuickSight User, find user name from https://us-east-1.quicksight.aws.amazon.com/sn/admin',
      minLength: 1,
      allowedPattern: '[\u0020-\u00FF]+',
      constraintDescription: 'Any printable ASCII character ranging from the space character (\u0020) through the end of the ASCII character range',
    });

    // Dashboard //////////////////////////
    new Dashboard(this, 'MolUnfDashboard', {
      account: this.account,
      region: this.region,
      stackName,
      quicksightUser: quickSightUserParam.valueAsString,
    });
  }
}