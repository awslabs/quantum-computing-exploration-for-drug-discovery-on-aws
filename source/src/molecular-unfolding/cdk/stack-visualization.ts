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
  Aspects,
  NestedStack,
  NestedStackProps,
  aws_s3 as s3,
  aws_iam as iam,
  CfnOutput,
  CfnRule,
  Fn,
} from 'aws-cdk-lib';
import {
  Construct,
} from 'constructs';
import {
  Dashboard,
} from './construct-dashboard';
import {
  MainStack,
} from './stack-main';


import {
  ChangePolicyName,
} from './utils/utils';

export interface VisualizationNestStackProps extends NestedStackProps {
  readonly prefix: string;
  readonly stackName: string;
  readonly quicksightUser: string;
  readonly quickSightRoleName: string;
  readonly bucket: s3.Bucket;
}

export class VisualizationNestStack extends NestedStack {
  outputDashboardUrl: CfnOutput;
  constructor(scope: Construct, id: string, props: VisualizationNestStackProps) {

    super(scope, id, props);
    const featureName = 'Visualization';
    this.templateOptions.description = `(${MainStack.SOLUTION_ID}-visualization) ${MainStack.SOLUTION_NAME} - ${featureName} (Version ${MainStack.SOLUTION_VERSION})`;

    new CfnRule(this, 'VisualizationParameterRule', {
      assertions: [{
        assert: Fn.conditionNot(Fn.conditionOr(
          Fn.conditionEquals(props.quicksightUser, ''),
          Fn.conditionEquals(props.quickSightRoleName, ''))),
        assertDescription: 'Parameter quicksightUser or quickSightRoleName is not set',
      }],
    });

    const quicksightRole = iam.Role.fromRoleArn(this, 'QuickSightServiceRole', `arn:aws:iam::${this.account}:role/${props.quickSightRoleName}`);
    props.bucket.grantRead(quicksightRole);
    Aspects.of(this).add(new ChangePolicyName());

    // Dashboard //////////////////////////
    const dashboard = new Dashboard(this, 'Dashboard', {
      account: this.account,
      region: this.region,
      stackName: props.stackName,
      quicksightUser: props.quicksightUser,
    });
    this.outputDashboardUrl = dashboard.outputDashboardUrl;
  }
}