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
  aws_iam as iam,
} from 'aws-cdk-lib';

import { ManagedPolicy } from 'aws-cdk-lib/aws-iam';

import {
  Construct,
} from 'constructs';

interface Props {
  region: string;
  account: string;
  prefix: string;
  stackName: string;
}

export class RoleUtil {

  public static newInstance(scope: Construct, props: Props) {
    return new this(scope, props);
  }

  private props: Props;
  private scope: Construct;
  private constructor(scope: Construct, props: Props) {
    this.props = props;
    this.scope = scope;
  }

  public createNotebookIamRole(): iam.Role {
    const role = new iam.Role(this.scope, 'NotebookRole', {
      assumedBy: new iam.ServicePrincipal('sagemaker.amazonaws.com'),
    });

    role.addToPolicy(new iam.PolicyStatement({
      resources: [
        `arn:aws:braket:*:${this.props.account}:quantum-task/*`,
        `arn:aws:braket:*:${this.props.account}:job/*`,
      ],
      actions: [
        'braket:GetJob',
        'braket:GetQuantumTask',
        'braket:CancelQuantumTask',
        'braket:CancelJob',
        'braket:ListTagsForResource',
      ],
    }));

    role.addToPolicy(new iam.PolicyStatement({
      resources: [
        '*',
      ],
      actions: [
        'braket:CancelJob',
        'braket:CancelQuantumTask',
        'braket:CreateJob',
        'braket:CreateQuantumTask',
        'braket:GetDevice',
        'braket:GetJob',
        'braket:GetQuantumTask',
        'braket:SearchDevices',
        'braket:SearchJobs',
        'braket:SearchQuantumTasks',
        'braket:ListTagsForResource',
        'braket:TagResource',
        'braket:UntagResource',
      ],
    }));

    role.addToPolicy(new iam.PolicyStatement({
      resources: [
        'arn:aws:s3:::braket-*/*',
        'arn:aws:s3:::cdk-*/*',
        'arn:aws:s3:::amazon-braket-*/*',
        'arn:aws:s3:::braketnotebookcdk-**',
      ],
      actions: [
        's3:PutObject',
        's3:GetObject',
        's3:ListBucket',
        's3:CreateBucket',
        's3:PutBucketPublicAccessBlock',
        's3:PutBucketPolicy',
      ],
    }));

    role.addToPolicy(new iam.PolicyStatement({
      resources: [
        'arn:aws:iam::*:role/*',
      ],
      actions: [
        'iam:ListRoles',
      ],
    }));

    role.addToPolicy(new iam.PolicyStatement({
      resources: [
        'arn:aws:iam::*:role/service-role/AmazonBraketJobsExecutionRole*',
      ],
      actions: [
        'iam:PassRole',
      ],
    }));


    role.addToPolicy(new iam.PolicyStatement({
      resources: [
        `arn:aws:ecr:${this.props.region}:${this.props.account}:repository/*`,
      ],
      actions: [
        'ecr:UploadLayerPart',
        'ecr:BatchDeleteImage',
        'ecr:DeleteRepository',
        'ecr:CompleteLayerUpload',
        'ecr:DescribeRepositories',
        'ecr:BatchCheckLayerAvailability',
        'ecr:CreateRepository',
        'ecr:GetDownloadUrlForLayer',
        'ecr:PutImage',
        'ecr:BatchGetImage',
        'ecr:InitiateLayerUpload',
      ],
    }));

    role.addToPolicy(new iam.PolicyStatement({
      resources: [
        `arn:aws:logs:*:${this.props.account}:log-group:/aws/sagemaker/*`,
      ],
      actions: [
        'logs:CreateLogStream',
        'logs:DescribeLogStreams',
        'logs:PutLogEvents',
        'logs:CreateLogGroup',
      ],
    }));

    role.addManagedPolicy(ManagedPolicy.fromAwsManagedPolicyName('AmazonBraketFullAccess'));

    return role;
  }
}
