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
  aws_kms as kms,
  aws_logs as logs,
  aws_ec2 as ec2,
  Aspects,
  Stack,
  RemovalPolicy,
} from 'aws-cdk-lib';

import {
  Construct,
} from 'constructs';

import {
  ChangePublicSubnet,
  grantKmsKeyPerm,
} from './utils';


export default (scope: Construct) => {
  const region = Stack.of(scope).region;

  const vpc = new ec2.Vpc(scope, 'VPC', {
    cidr: '10.1.0.0/16',
    maxAzs: 2,
    subnetConfiguration: [{
      cidrMask: 18,
      name: 'Ingress',
      subnetType: ec2.SubnetType.PUBLIC,
    },
    {
      cidrMask: 18,
      name: 'Application',
      subnetType: ec2.SubnetType.PRIVATE_WITH_NAT,
    }],
  });

  vpc.publicSubnets.forEach(s => {
    Aspects.of(s).add(new ChangePublicSubnet());
  });

  vpc.addGatewayEndpoint('S3Endpoint', {
    service: ec2.GatewayVpcEndpointAwsService.S3,
  });

  vpc.addInterfaceEndpoint('BraketEndpoint', {
    service: {
      name: `com.amazonaws.${region}.braket`,
      port: 443,
    },
  });

  const logKey = new kms.Key(scope, 'qcLogKey', {
    enableKeyRotation: true,
  });
  const logGroupName = `${Stack.of(logKey).stackName}-vpcFlowlog`;

  grantKmsKeyPerm(logKey, logGroupName);

  const vpcFlowlog = new logs.LogGroup(scope, 'vpcFlowlog', {
    encryptionKey: logKey,
    logGroupName,
    removalPolicy: RemovalPolicy.DESTROY,
    retention: logs.RetentionDays.THREE_MONTHS,
  });

  vpc.addFlowLog('logtoCW', {
    destination: ec2.FlowLogDestination.toCloudWatchLogs(vpcFlowlog),
    trafficType: ec2.FlowLogTrafficType.ALL,
  });

  const batchSg = new ec2.SecurityGroup(scope, 'batchSg', {
    vpc,
    allowAllOutbound: false,
    description: 'Security Group for QC batch compute environment',
  });

  batchSg.addEgressRule(ec2.Peer.anyIpv4(), ec2.Port.tcp(443));
  batchSg.addEgressRule(ec2.Peer.anyIpv6(), ec2.Port.tcp(443));
  batchSg.addEgressRule(ec2.Peer.anyIpv4(), ec2.Port.tcp(80));
  batchSg.addEgressRule(ec2.Peer.anyIpv6(), ec2.Port.tcp(80));

  const lambdaSg = new ec2.SecurityGroup(scope, 'lambdaSg', {
    vpc,
    allowAllOutbound: false,
    description: 'Security Group for lambda',
  });

  lambdaSg.addEgressRule(ec2.Peer.anyIpv4(), ec2.Port.tcp(443));
  lambdaSg.addEgressRule(ec2.Peer.anyIpv6(), ec2.Port.tcp(443));
  lambdaSg.addEgressRule(ec2.Peer.anyIpv4(), ec2.Port.tcp(80));
  lambdaSg.addEgressRule(ec2.Peer.anyIpv6(), ec2.Port.tcp(80));

  return {
    vpc,
    batchSg,
    lambdaSg,
  };
};