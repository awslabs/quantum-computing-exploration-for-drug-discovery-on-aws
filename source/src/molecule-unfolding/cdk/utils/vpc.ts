import * as logs from '@aws-cdk/aws-logs'
import * as kms from '@aws-cdk/aws-kms'
import * as ec2 from '@aws-cdk/aws-ec2';
import {
    Aspects,
    Construct
} from '@aws-cdk/core';

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

    const logKey = new kms.Key(scope, 'qcLogKey', {
        enableKeyRotation: true
    });
    grantKmsKeyPerm(logKey);

    const vpcFlowlog = new logs.LogGroup(scope, "vpcFlowlog", {
        encryptionKey: logKey
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