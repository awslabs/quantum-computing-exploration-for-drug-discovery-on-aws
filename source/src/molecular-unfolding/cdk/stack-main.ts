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
  aws_s3 as s3,
  Aspects,
  StackProps,
  CfnCondition,
  Fn,
  RemovalPolicy,
  CfnOutput,
  CfnRule,
} from 'aws-cdk-lib';

import {
  Construct,
} from 'constructs';

import {
  SolutionStack,
} from '../../stack';


import {
  BatchEvaluation,
} from './construct-batch-evaluation';

import {
  EventListener,
} from './construct-listener';
import {
  Notebook,
} from './construct-notebook';

import create_custom_resources from './utils/custom-resource';
import {
  AddCfnNag,
  AddCondition,
} from './utils/utils';
import setup_vpc_and_sg from './utils/vpc';

export class MainStack extends SolutionStack {
  static SOLUTION_ID = 'SO8027'
  static SOLUTION_VERSION = process.env.SOLUTION_VERSION || 'v1.0.0'

  // constructor
  constructor(scope: Construct, id: string, props: StackProps = {}) {
    const DESCRIPTION = `(${MainStack.SOLUTION_ID}) Quantum Computing Exploration for Drug Discovery on AWS ${MainStack.SOLUTION_VERSION} Main Stack`;
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

    const prefix = 'molecular-unfolding';

    const crossEventRegionCondition = new CfnCondition(this, 'CrossEventRegionCondition', {
      expression: Fn.conditionNot(
        Fn.conditionEquals(this.region, 'us-west-2'),
      ),
    });

    const logS3bucket = new s3.Bucket(this, 'AccessLogS3Bucket', {
      removalPolicy: RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
      enforceSSL: true,
      encryption: s3.BucketEncryption.S3_MANAGED,
    });

    const bucketName = `amazon-braket-${stackName}-${this.account}-${this.region}`;
    const s3bucket = new s3.Bucket(this, 'amazon-braket', {
      removalPolicy: RemovalPolicy.DESTROY,
      bucketName,
      autoDeleteObjects: true,
      enforceSSL: true,
      encryption: s3.BucketEncryption.S3_MANAGED,
      serverAccessLogsBucket: logS3bucket,
      serverAccessLogsPrefix: `accesslogs/${bucketName}/`,
    });
    s3bucket.node.addDependency(logS3bucket);

    new CfnOutput(this, 'bucketName', {
      value: s3bucket.bucketName,
      description: 'S3 bucket name',
    });

    const {
      vpc,
      batchSg,
      lambdaSg,
    } = setup_vpc_and_sg(this);

    create_custom_resources(this, {
      vpc,
      sg: lambdaSg,
      crossEventRegionCondition,
    });
    Aspects.of(this).add(new AddCondition(crossEventRegionCondition));

    // Notebook //////////////////////////
    new Notebook(this, 'MolUnfNotebook', {
      account: this.account,
      region: this.region,
      bucket: s3bucket,
      prefix,
      notebookSg: batchSg,
      vpc,
      stackName,
    });

    // BatchEvaluation StepFuncs //////////////////////////
    new BatchEvaluation(this, 'MolUnfBatchEvaluation', {
      account: this.account,
      region: this.region,
      bucket: s3bucket,
      prefix,
      vpc,
      batchSg,
      lambdaSg,
      stackName,
    });


    // Event Listener Lambda //////////////////////////
    new EventListener(this, 'BraketTaskEventHandler', {
      account: this.account,
      region: this.region,
      bucket: s3bucket,
      prefix,
      vpc,
      lambdaSg,
      stackName,
    });
    Aspects.of(this).add(new AddCfnNag());
  }

}