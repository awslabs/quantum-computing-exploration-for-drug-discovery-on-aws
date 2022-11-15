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
  aws_s3 as s3,
} from 'aws-cdk-lib';

import {
  Construct,
} from 'constructs';

interface Props {
  region: string;
  account: string;
  bucket: s3.Bucket;
  prefix: string;
  stackName: string;
}

export class RoleUtil {

  public static newInstance(scope: Construct, props: Props) {
    return new this(scope, props);
  }

  private props: Props
  private scope: Construct
  private constructor(scope: Construct, props: Props) {
    this.props = props;
    this.scope = scope;
  }


  private addLambdaCommonPolicy(role: iam.Role) {
    role.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      resources: [
        '*',
      ],
      actions: [
        'ec2:CreateNetworkInterface',
        'ec2:DescribeNetworkInterfaces',
        'ec2:DeleteNetworkInterface',
        'ec2:AssignPrivateIpAddresses',
        'ec2:UnassignPrivateIpAddresses',
      ],
    }));
    role.addToPolicy(new iam.PolicyStatement({
      resources: [
        `arn:aws:logs:*:${this.props.account}:log-group:*`,
      ],
      actions: [
        'logs:CreateLogStream',
        'logs:PutLogEvents',
        'logs:CreateLogGroup',
      ],
    }));
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
        'braket:CreateJob',
        'braket:GetDevice',
        'braket:SearchDevices',
        'braket:CreateQuantumTask',
        'braket:SearchJobs',
        'braket:SearchQuantumTasks',
      ],
    }));

    role.addToPolicy(new iam.PolicyStatement({
      resources: [
        `arn:aws:s3:::${this.props.bucket.bucketName}/*`,
        'arn:aws:s3:::braket-*/*',
        'arn:aws:s3:::amazon-braket-*/*',
      ],
      actions: [
        's3:PutObject',
        's3:GetObject',
      ],
    }));

    role.addToPolicy(new iam.PolicyStatement({
      resources: [
        `arn:aws:s3:::${this.props.bucket.bucketName}`,
      ],
      actions: [
        's3:ListBucket',
      ],
    }));

    role.addToPolicy(new iam.PolicyStatement({
      resources: [
        `arn:aws:ecr:${this.props.region}:${this.props.account}:repository/${this.props.prefix}/*`,
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
        'logs:PutLogEvents',
        'logs:CreateLogGroup',
      ],
    }));
    return role;
  }


  public createBatchJobExecutionRole(roleName: string): iam.Role {
    const ecrAccount = process.env.SOLUTION_ECR_ACCOUNT || '';
    const role = new iam.Role(this.scope, `${roleName}`, {
      assumedBy: new iam.ServicePrincipal('ecs-tasks.amazonaws.com'),
    });

    const resources = [
      `arn:aws:ecr:${this.props.region}:${this.props.account}:repository/*`,
    ];

    if (ecrAccount) {
      resources.push(`arn:aws:ecr:${this.props.region}:${ecrAccount}:repository/*`);
    }

    role.addToPolicy(new iam.PolicyStatement({
      resources,
      actions: [
        'ecr:BatchCheckLayerAvailability',
        'ecr:GetDownloadUrlForLayer',
        'ecr:BatchGetImage',
      ],
    }));

    role.addToPolicy(new iam.PolicyStatement({
      resources: [
        '*',
      ],
      actions: [
        'ecr:GetAuthorizationToken',

      ],
    }));

    role.addToPolicy(new iam.PolicyStatement({
      resources: [
        `arn:aws:logs:*:${this.props.account}:log-group:/aws/batch/*`,
      ],
      actions: [
        'logs:CreateLogStream',
        'logs:PutLogEvents',
        'logs:CreateLogGroup',
      ],
    }));
    return role;
  }

  public createCCBatchJobRole(roleName: string): iam.Role {
    const role = new iam.Role(this.scope, `${roleName}`, {
      assumedBy: new iam.ServicePrincipal('ecs-tasks.amazonaws.com'),
    });
    role.addToPolicy(new iam.PolicyStatement({
      resources: [
        `arn:aws:s3:::${this.props.bucket.bucketName}/*`,
      ],
      actions: [
        's3:PutObject',
        's3:GetObject',
      ],
    }));

    role.addToPolicy(new iam.PolicyStatement({
      resources: [
        'arn:aws:s3:::braket-*/*',
        'arn:aws:s3:::amazon-braket-*/*',
      ],
      actions: [
        's3:GetObject',
      ],
    }));

    role.addToPolicy(new iam.PolicyStatement({
      resources: [
        `arn:aws:s3:::${this.props.bucket.bucketName}`,
      ],
      actions: [
        's3:ListBucket',
      ],
    }));
    return role;
  }


  public createQCBatchJobRole(roleName: string): iam.Role {
    const role = new iam.Role(this.scope, `${roleName}`, {
      assumedBy: new iam.ServicePrincipal('ecs-tasks.amazonaws.com'),
    });
    role.addToPolicy(new iam.PolicyStatement({
      resources: [
        `arn:aws:s3:::${this.props.bucket.bucketName}/*`,
      ],
      actions: [
        's3:PutObject',
        's3:GetObject',
      ],
    }));

    role.addToPolicy(new iam.PolicyStatement({
      resources: [
        `arn:aws:braket:*:${this.props.account}:quantum-task/*`,
      ],
      actions: [
        'braket:GetQuantumTask',
      ],
    }));

    role.addToPolicy(new iam.PolicyStatement({
      resources: [
        '*',
      ],
      actions: [
        'braket:GetDevice',
        'braket:CreateQuantumTask',
      ],
    }));

    role.addToPolicy(new iam.PolicyStatement({
      resources: [
        `arn:aws:s3:::${this.props.bucket.bucketName}`,
      ],
      actions: [
        's3:ListBucket',
      ],
    }));
    return role;
  }

  public createCreateModelBatchJobRole(roleName: string): iam.Role {
    const role = new iam.Role(this.scope, `${roleName}`, {
      assumedBy: new iam.ServicePrincipal('ecs-tasks.amazonaws.com'),
    });
    role.addToPolicy(new iam.PolicyStatement({
      resources: [
        `arn:aws:s3:::${this.props.bucket.bucketName}/*`,
      ],
      actions: [
        's3:PutObject',
        's3:GetObject',
      ],
    }));

    role.addToPolicy(new iam.PolicyStatement({
      resources: [
        'arn:aws:s3:::braket-*/*',
        'arn:aws:s3:::amazon-braket-*/*',
      ],
      actions: [
        's3:GetObject',
      ],
    }));

    role.addToPolicy(new iam.PolicyStatement({
      resources: [
        `arn:aws:s3:::${this.props.bucket.bucketName}`,
      ],
      actions: [
        's3:ListBucket',
      ],
    }));
    return role;
  }

  public createAggResultLambdaRole(): iam.Role {
    const role = new iam.Role(this.scope, 'AggResultLambdaRole', {
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
    });
    const table_name1 = `${this.props.stackName}_qc_batch_evaluation_metrics_hist`;
    const table_name2 = `${this.props.stackName}_qc_batch_evaluation_metrics`;
    role.addToPolicy(new iam.PolicyStatement({
      resources: [
        `arn:aws:athena:*:${this.props.account}:workgroup/primary`,
        `arn:aws:athena:*:${this.props.account}:datacatalog/AwsDataCatalog`,
        `arn:aws:glue:*:${this.props.account}:database/qc_db`,
        `arn:aws:glue:*:${this.props.account}:table/qc_db/${table_name1}`,
        `arn:aws:glue:*:${this.props.account}:table/qc_db/${table_name2}`,
        `arn:aws:glue:*:${this.props.account}:catalog`,
      ],
      actions: [
        'athena:StartQueryExecution',
        'athena:GetQueryExecution',
        'athena:GetQueryResults',
        'glue:UpdateDatabase',
        'glue:DeleteDatabase',
        'glue:CreateDatabase',
        'glue:GetTable',
        'glue:DeleteTable',
        'glue:CreateTable',
        'glue:UpdateTable',
      ],
    }));

    role.addToPolicy(new iam.PolicyStatement({
      resources: [
        '*',
      ],
      actions: [
        'athena:ListDataCatalogs',
      ],
    }));

    role.addToPolicy(new iam.PolicyStatement({
      resources: [
        `arn:aws:s3:::${this.props.bucket.bucketName}/*`,
      ],
      actions: [
        's3:GetObject',
        's3:PutObject',
      ],
    }));

    role.addToPolicy(new iam.PolicyStatement({
      resources: [
        `arn:aws:s3:::${this.props.bucket.bucketName}`,
      ],
      actions: [
        's3:ListBucket',
        's3:GetBucketLocation',
      ],
    }));

    this.addLambdaCommonPolicy(role);
    return role;
  }

  public createWaitForTokenLambdaRole(roleName: string): iam.Role {
    const role = new iam.Role(this.scope, `${roleName}`, {
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
    });

    role.addToPolicy(new iam.PolicyStatement({
      resources: [
        `arn:aws:s3:::${this.props.bucket.bucketName}/*`,
      ],
      actions: [
        's3:GetObject',
        's3:PutObject',
      ],
    }));

    this.addLambdaCommonPolicy(role);

    return role;
  }

  public createCheckQCDeviceLambdaRole(roleName: string): iam.Role {
    const role = new iam.Role(this.scope, `${roleName}`, {
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
    });

    role.addToPolicy(new iam.PolicyStatement({
      resources: [
        '*',
      ],
      actions: [
        'braket:GetDevice',
      ],
    }));

    this.addLambdaCommonPolicy(role);

    return role;
  }

  public createTaskParametersLambdaRole(roleName: string): iam.Role {
    const role = new iam.Role(this.scope, `${roleName}`, {
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
    });
    role.addToPolicy(new iam.PolicyStatement({
      resources: [
        `arn:aws:s3:::${this.props.bucket.bucketName}/*`,
      ],
      actions: [
        's3:GetObject',
        's3:PutObject',
      ],
    }));

    this.addLambdaCommonPolicy(role);

    return role;
  }


  public createCallBackLambdaRole(roleName: string): iam.Role {
    const role = new iam.Role(this.scope, `${roleName}`, {
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
    });
    role.addToPolicy(new iam.PolicyStatement({
      resources: [
        `arn:aws:s3:::${this.props.bucket.bucketName}/*`,
      ],
      actions: [
        's3:PutObject',
        's3:GetObject',
      ],
    }));

    role.addToPolicy(new iam.PolicyStatement({
      resources: [
        'arn:aws:s3:::braket-*/*',
        'arn:aws:s3:::amazon-braket-*/*',
      ],
      actions: [
        's3:GetObject',
      ],
    }));

    this.addLambdaCommonPolicy(role);

    role.addToPolicy(new iam.PolicyStatement({
      actions: [
        'states:SendTaskSuccess',
        'states:SendTaskFailure',
        'states:SendTaskHeartbeat',
      ],
      resources: [
        '*',
      ],
    }));

    return role;
  }
}