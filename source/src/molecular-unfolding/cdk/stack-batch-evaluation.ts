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
  NestedStack,
  NestedStackProps,
  aws_s3 as s3,
  aws_ec2 as ec2,
  CfnCondition,
  Aspects,
  Fn,
  CfnOutput,
} from 'aws-cdk-lib';
import {
  Construct,
} from 'constructs';
import {
  BatchEvaluation,
} from './construct-batch-evaluation';

import {
  EventListener,
} from './construct-listener';
import {
  MainStack,
} from './stack-main';


import create_custom_resources from './utils/custom-resource';
import {
  AddCfnNag,
  AddCondition,
} from './utils/utils';

export interface BatchEvaluationNestStackProps extends NestedStackProps {
  readonly bucket: s3.Bucket;
  readonly prefix: string;
  readonly vpc: ec2.Vpc;
  readonly batchSg: ec2.SecurityGroup;
  readonly lambdaSg: ec2.SecurityGroup;
  readonly stackName: string;
}

export class BatchEvaluationNestStack extends NestedStack {
  stateMachineURLOutput: CfnOutput;
  snsOutput?: CfnOutput;

  constructor(scope: Construct, id: string, props: BatchEvaluationNestStackProps) {

    super(scope, id, props);
    const featureName = 'Batch Evaluation';
    this.templateOptions.description = `(${MainStack.SOLUTION_ID}-batch-eval) ${MainStack.SOLUTION_NAME} - ${featureName} (Version ${MainStack.SOLUTION_VERSION})`;

    const crossEventRegionCondition = new CfnCondition(this, 'CrossEventRegionCondition', {
      expression: Fn.conditionNot(
        Fn.conditionEquals(this.region, 'us-west-2'),
      ),
    });

    props.vpc.addInterfaceEndpoint('EcrDockerEndpoint', {
      service: ec2.InterfaceVpcEndpointAwsService.ECR_DOCKER,
    });

    props.vpc.addInterfaceEndpoint('AthenaEndpoint', {
      service: ec2.InterfaceVpcEndpointAwsService.ATHENA,
    });

    create_custom_resources(this, {
      vpc: props.vpc,
      sg: props.lambdaSg,
      crossEventRegionCondition,
    });

    Aspects.of(this).add(new AddCondition(crossEventRegionCondition));

    // BatchEvaluation StepFuncs //////////////////////////
    const batchEvaluation = new BatchEvaluation(this, 'BatchEvaluation', {
      account: this.account,
      region: this.region,
      bucket: props.bucket,
      prefix: props.prefix,
      vpc: props.vpc,
      batchSg: props.batchSg,
      lambdaSg: props.lambdaSg,
      stackName: props.stackName,
    });

    this.stateMachineURLOutput = batchEvaluation.stateMachineURLOutput;
    this.snsOutput = batchEvaluation.snsOutput;

    // Event Listener Lambda //////////////////////////
    new EventListener(this, 'BraketTaskEventHandler', {
      account: this.account,
      region: this.region,
      bucket: props.bucket,
      prefix: props.prefix,
      vpc: props.vpc,

      lambdaSg: props.lambdaSg,
      stackName: props.stackName,
    });
    Aspects.of(this).add(new AddCfnNag());
  }


}