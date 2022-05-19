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
  CfnOutput,
} from 'aws-cdk-lib';
import {
  Construct,
} from 'constructs';
import {
  Notebook,
} from './construct-notebook';
import {
  MainStack,
} from './stack-main';

export interface NotebookNestStackProps extends NestedStackProps {
  readonly prefix: string;
  readonly stackName: string;
  readonly bucket: s3.Bucket;
  readonly batchSg: ec2.SecurityGroup;
  readonly vpc: ec2.Vpc;
}

export class NotebookNestStack extends NestedStack {
  notebookUrlOutput: CfnOutput;
  constructor(scope: Construct, id: string, props: NotebookNestStackProps) {

    super(scope, id, props);
    const featureName = 'Notebook';
    this.templateOptions.description = `(${MainStack.SOLUTION_ID}-notebook) ${MainStack.SOLUTION_NAME} - ${featureName} (Version ${MainStack.SOLUTION_VERSION})`;

    // Notebook //////////////////////////
    const notebook = new Notebook(this, 'Notebook', {
      account: this.account,
      region: this.region,
      bucket: props. bucket,
      prefix: props.prefix,
      notebookSg: props.batchSg,
      vpc: props.vpc,
      stackName: props.stackName,
    });

    this.notebookUrlOutput = new CfnOutput(this, 'NotebookUrl', {
      value: notebook.notebookUrl,
      description: 'Notebook URL',
    });
  }
}