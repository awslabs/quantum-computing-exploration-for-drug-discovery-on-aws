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


import * as batch from '@aws-cdk/aws-batch-alpha';

import {
  aws_ec2 as ec2,
  aws_iam as iam,
  aws_ecs as ecs,
  aws_s3 as s3,
  Duration,
  Aspects,
} from 'aws-cdk-lib';

import {
  Construct,
} from 'constructs';

import {
  AddSSMPolicyToRole,
} from './utils';
import {
  ECRRepoNameEnum,
  ECRImageUtil,
} from './utils-images';

import {
  RoleUtil,
} from './utils-role';


interface Props {
  region: string;
  account: string;
  prefix: string;
  bucket: s3.Bucket;
  vpc: ec2.Vpc;
  batchSg: ec2.SecurityGroup;

}
export class BatchUtil {

  public static newInstance(scope: Construct, props: Props, utils: {
    roleUtil: RoleUtil;
    imageUtil: ECRImageUtil;
  }) {
    return new this(scope, props, utils);
  }

  private props: Props
  private scope: Construct
  private batchJobExecutionRole: iam.Role
  private ccBatchJobRole: iam.Role
  private qcBatchJobRole: iam.Role
  private createModelBatchJobRole: iam.Role
  private ccJobQueue: batch.JobQueue
  private fargateJobQueue: batch.JobQueue
  private imageUtil : ECRImageUtil

  private constructor(scope: Construct, props: Props, utils: {
    roleUtil: RoleUtil;
    imageUtil: ECRImageUtil;
  }) {
    this.props = props;
    this.scope = scope;
    this.imageUtil = utils.imageUtil;
    this.batchJobExecutionRole = utils.roleUtil.createBatchJobExecutionRole('batchExecutionRole');
    this.ccBatchJobRole = utils.roleUtil.createCCBatchJobRole('ccBatchJobRole');
    this.qcBatchJobRole = utils.roleUtil.createQCBatchJobRole('qcBatchJobRole');
    this.createModelBatchJobRole = utils.roleUtil.createCreateModelBatchJobRole('createModelBatchJobRole');
    this.ccJobQueue = this.setUpCCBashEnv();
    this.fargateJobQueue = this.setUpFargateBashEnv();
  }

  private setUpCCBashEnv(): batch.JobQueue {
    const ccIstanceTypes = [
      ec2.InstanceType.of(ec2.InstanceClass.C5, ec2.InstanceSize.LARGE), // 2 vcpus, 4G mem
      ec2.InstanceType.of(ec2.InstanceClass.C5, ec2.InstanceSize.XLARGE), // 4 vcpus, 8G mem
      ec2.InstanceType.of(ec2.InstanceClass.C5, ec2.InstanceSize.XLARGE2), // 8 vcpus, 16G mem
      ec2.InstanceType.of(ec2.InstanceClass.C5, ec2.InstanceSize.XLARGE4), // 16 vcpus, 32G mem
      //ec2.InstanceType.of(ec2.InstanceClass.C5, ec2.InstanceSize.XLARGE9), // 36 vcpus, 72 mem
    ];
    const vpc = this.props.vpc;
    const batchSg = this.props.batchSg;

    const batchCCEnvironment = new batch.ComputeEnvironment(this.scope, 'Batch-CC-Compute-Env', {
      computeResources: {
        type: batch.ComputeResourceType.ON_DEMAND,
        vpc,
        vpcSubnets: vpc.selectSubnets({
          subnetType: ec2.SubnetType.PRIVATE_WITH_NAT,
        }),
        allocationStrategy: batch.AllocationStrategy.BEST_FIT,
        instanceTypes: ccIstanceTypes,
        securityGroups: [batchSg],
      },
    });

    Aspects.of(batchCCEnvironment).add(new AddSSMPolicyToRole());

    return new batch.JobQueue(this.scope, 'ccJobQueue', {
      computeEnvironments: [{
        computeEnvironment: batchCCEnvironment,
        order: 1,
      }],
    });
  }

  private setUpFargateBashEnv(): batch.JobQueue {
    const vpc = this.props.vpc;
    const batchSg = this.props.batchSg;

    const batchFargateEnvironment = new batch.ComputeEnvironment(this.scope, 'Batch-Fargate-Compute-Env', {
      computeResources: {
        type: batch.ComputeResourceType.FARGATE,
        vpc,
        vpcSubnets: vpc.selectSubnets({
          subnetType: ec2.SubnetType.PRIVATE_WITH_NAT,
        }),
        securityGroups: [batchSg],
      },
    });

    return new batch.JobQueue(this.scope, 'fargateJobQueue', {
      computeEnvironments: [{
        computeEnvironment: batchFargateEnvironment,
        order: 1,
      }],
    });
  }

  public getCcJobQueue(): batch.JobQueue {
    return this.ccJobQueue;
  }

  public getFargateJobQueue(): batch.JobQueue {
    return this.fargateJobQueue;
  }

  public createCreateModelJobDef(): batch.JobDefinition {

    const image = this.imageUtil.getECRImage(ECRRepoNameEnum.Batch_Create_Model) as ecs.ContainerImage;
    const vcpus = 2;
    const mem = 4;
    const resource = this.getResourceDescription(vcpus, mem);

    return new batch.JobDefinition(this.scope, 'CreateModelJobDef', {
      platformCapabilities: [batch.PlatformCapabilities.FARGATE],
      container: {
        image,
        command: [
          '--aws-region', this.props.region,
          '--resource', `${resource}`,
          '--s3-bucket', this.props.bucket.bucketName,
        ],
        executionRole: this.batchJobExecutionRole,
        jobRole: this.createModelBatchJobRole,
        vcpus,
        memoryLimitMiB: mem * 1024,
        privileged: false,
      },
      timeout: Duration.hours(2),
      retryAttempts: 1,
    });
  }

  public createCCBatchJobDef(defName: string, vcpus: number, mem: number): batch.JobDefinition {

    const image = this.imageUtil.getECRImage(ECRRepoNameEnum.Batch_Sa_Optimizer) as ecs.ContainerImage;
    const resource = this.getResourceDescription(vcpus, mem);

    return new batch.JobDefinition(this.scope, defName, {
      platformCapabilities: [batch.PlatformCapabilities.EC2],
      container: {
        image,
        command: [
          '--model-param', 'M=1&D=4&A=300&HQ=200',
          '--aws-region', this.props.region,
          '--resource', `${resource}`,
          '--s3-bucket', this.props.bucket.bucketName,
        ],
        executionRole: this.batchJobExecutionRole,
        jobRole: this.ccBatchJobRole,
        vcpus,
        memoryLimitMiB: mem * 1024,
        privileged: false,
      },
      timeout: Duration.hours(6),
      retryAttempts: 1,
    });

  }

  public createQCSubmitBatchJobDef(defName: string): batch.JobDefinition {

    const image = this.imageUtil.getECRImage(ECRRepoNameEnum.Batch_Qa_Optimizer) as ecs.ContainerImage;
    const vcpus = 2;
    const mem = 4;
    const resource = this.getResourceDescription(vcpus, mem);

    return new batch.JobDefinition(this.scope, defName, {
      platformCapabilities: [batch.PlatformCapabilities.FARGATE],
      container: {
        image,
        command: [
          '--model-param', 'M=1&D=4&A=300&HQ=200',
          '--aws-region', this.props.region,
          '--resource', `${resource}`,
          '--s3-bucket', this.props.bucket.bucketName,
        ],
        executionRole: this.batchJobExecutionRole,
        jobRole: this.qcBatchJobRole,
        vcpus,
        memoryLimitMiB: mem * 1024,
        privileged: false,
      },
      timeout: Duration.hours(1),
      retryAttempts: 1,
    });
  }

  private getResourceDescription(vcpus: number, mem: number): string {
    return `vCpus${vcpus}_Mem_${mem}G`;
  }


}