import {
    aws_kms as kms
} from 'aws-cdk-lib'

import {
    aws_logs as logs
} from 'aws-cdk-lib'

import {
    aws_ec2 as ec2
} from 'aws-cdk-lib'

import * as cdk from 'aws-cdk-lib'

import {
    Aspects,
} from 'aws-cdk-lib'

import {
    Construct
} from 'constructs'

import {
    ChangePublicSubnet,
    grantKmsKeyPerm
} from './utils'


export default (scope: Construct) => {

    const vpc = new ec2.Vpc(scope, 'VPC', {
        cidr: '10.1.0.0/16',
        maxAzs: 2,
        subnetConfiguration: [{
                cidrMask: 18,
                name: 'Ingress',
                subnetType: ec2.SubnetType.PUBLIC
            },
            {
                cidrMask: 18,
                name: 'Application',
                subnetType: ec2.SubnetType.PRIVATE_WITH_NAT
            }
        ]
    });

    vpc.publicSubnets.forEach(s => {
        Aspects.of(s).add(new ChangePublicSubnet())
    });

    vpc.addGatewayEndpoint('S3Endpoint', {
        service: ec2.GatewayVpcEndpointAwsService.S3
    });

    vpc.addInterfaceEndpoint('EcrDockerEndpoint', {
        service: ec2.InterfaceVpcEndpointAwsService.ECR_DOCKER
    });

    vpc.addInterfaceEndpoint('AthenaEndpoint', {
        service: ec2.InterfaceVpcEndpointAwsService.ATHENA
    });

    vpc.addInterfaceEndpoint('SageMakerNotebookEndpoint', {
        service: ec2.InterfaceVpcEndpointAwsService.SAGEMAKER_NOTEBOOK
    });

    vpc.addInterfaceEndpoint('SNSEndpoint', {
        service: ec2.InterfaceVpcEndpointAwsService.SNS
    });

    const logKey = new kms.Key(scope, 'qcLogKey', {
        enableKeyRotation: true
    });
    const logGroupName = `${cdk.Stack.of(logKey).stackName}-vpcFlowlog`

    grantKmsKeyPerm(logKey, logGroupName);

    const vpcFlowlog = new logs.LogGroup(scope, "vpcFlowlog", {
        encryptionKey: logKey,
        logGroupName,
        removalPolicy: cdk.RemovalPolicy.DESTROY,
        retention: logs.RetentionDays.THREE_MONTHS
    });

    vpc.addFlowLog("logtoCW", {
        destination: ec2.FlowLogDestination.toCloudWatchLogs(vpcFlowlog),
        trafficType: ec2.FlowLogTrafficType.ALL
    });

    const batchSg = new ec2.SecurityGroup(scope, "batchSg", {
        vpc,
        allowAllOutbound: false,
        description: "Security Group for QC batch compute environment"
    });

    batchSg.addEgressRule(ec2.Peer.anyIpv4(), ec2.Port.tcp(443))
    batchSg.addEgressRule(ec2.Peer.anyIpv6(), ec2.Port.tcp(443))
    batchSg.addEgressRule(ec2.Peer.anyIpv4(), ec2.Port.tcp(80))
    batchSg.addEgressRule(ec2.Peer.anyIpv6(), ec2.Port.tcp(80))

    const lambdaSg = new ec2.SecurityGroup(scope, "lambdaSg", {
        vpc,
        allowAllOutbound: false,
        description: "Security Group for lambda"
    });

    lambdaSg.addEgressRule(ec2.Peer.anyIpv4(), ec2.Port.tcp(443))
    lambdaSg.addEgressRule(ec2.Peer.anyIpv6(), ec2.Port.tcp(443))
    lambdaSg.addEgressRule(ec2.Peer.anyIpv4(), ec2.Port.tcp(80))
    lambdaSg.addEgressRule(ec2.Peer.anyIpv6(), ec2.Port.tcp(80))

    return {
        vpc,
        batchSg,
        lambdaSg
    }
}