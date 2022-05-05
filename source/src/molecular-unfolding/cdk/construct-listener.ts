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
  aws_ec2 as ec2,
  aws_lambda as lambda,
  aws_events as events,
  aws_events_targets as targets,
  Duration,
} from 'aws-cdk-lib';

import {
  Construct,
} from 'constructs';

import {
  ECRRepoNameEnum,
  ECRImageUtil,
} from './utils/utils-images';

import {
  RoleUtil,
} from './utils/utils-role';

interface Props {
  region: string;
  account: string;
  bucket: s3.Bucket;
  prefix: string;
  vpc: ec2.Vpc;
  lambdaSg: ec2.SecurityGroup;
  stackName: string;
}

export class EventListener extends Construct {
  private images: ECRImageUtil
  private roleUtil: RoleUtil
  private props: Props

  constructor(scope: Construct, id: string, props: Props) {
    super(scope, id);
    this.props = props;
    this.images = ECRImageUtil.newInstance(scope);
    this.roleUtil = RoleUtil.newInstance(scope, this.props);
    this.createEventListener(this.props.vpc, this.props.lambdaSg);
  }

  private createEventListener(vpc: ec2.Vpc, lambdaSg: ec2.SecurityGroup) {
    const lambdaRole = this.roleUtil.createCallBackLambdaRole('ParseBraketResultLambdaRole');
    const code = this.images.getECRImage(ECRRepoNameEnum.Lambda_ParseBraketResult) as lambda.DockerImageCode;
    const parseBraketResultLambda = new lambda.DockerImageFunction(this, 'ParseBraketResultLambda', {
      code,
      memorySize: 2048,
      timeout: Duration.seconds(900),
      vpc,
      vpcSubnets: vpc.selectSubnets({
        subnetType: ec2.SubnetType.PRIVATE_WITH_NAT,
      }),
      role: lambdaRole,
      securityGroups: [lambdaSg],
    });

    const rule = new events.Rule(this, 'braketEventrule', {
      eventPattern: {
        source: ['aws.braket'],
        detailType: ['Braket Task State Change'],
      },
    });

    rule.addTarget(new targets.LambdaFunction(parseBraketResultLambda, {
      maxEventAge: Duration.hours(2),
      retryAttempts: 3,
    }));
  }
}