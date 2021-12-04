import * as cdk from '@aws-cdk/core';
import * as s3 from '@aws-cdk/aws-s3';
import * as ec2 from '@aws-cdk/aws-ec2';
import * as lambda from '@aws-cdk/aws-lambda';

import {
    ECRRepoNameEnum,
    ECRImageUtil
} from './utils/utils-images'

import {
    RoleUtil
} from './utils/utils-role'

const s3n = require('@aws-cdk/aws-s3-notifications')

interface Props {
    region: string;
    account: string;
    bucket: s3.Bucket;
    prefix: string;
    usePreBuildImage: boolean;
    vpc: ec2.Vpc;
    lambdaSg: ec2.SecurityGroup;
}

export class EventListener extends cdk.Construct {
    private images: ECRImageUtil
    private roleUtil: RoleUtil
    private props: Props

    constructor(scope: cdk.Construct, id: string, props: Props) {
        super(scope, id);
        this.props = props
        this.images = ECRImageUtil.newInstance(scope, this.props)
        this.roleUtil = RoleUtil.newInstance(scope, this.props)
        this.createEventListener(this.props.vpc, this.props.lambdaSg)
    }

    private createEventListener(vpc: ec2.Vpc, lambdaSg: ec2.SecurityGroup) {
        const lambdaRole = this.roleUtil.createGenericLambdaRole("ParseBraketResultLambdaRole")
        const code = this.images.getECRImage(ECRRepoNameEnum.Lambda_ParseBraketResult) as lambda.DockerImageCode
        const parseBraketResultLambda = new lambda.DockerImageFunction(this, 'ParseBraketResultLambda', {
            code,
            memorySize: 512,
            timeout: cdk.Duration.seconds(120),
            vpc,
            vpcSubnets: vpc.selectSubnets({
                subnetType: ec2.SubnetType.PRIVATE_WITH_NAT
            }),
            role: lambdaRole,
            reservedConcurrentExecutions: 20,
            securityGroups: [lambdaSg]
        });

        this.props.bucket.addEventNotification(s3.EventType.OBJECT_CREATED,
            new s3n.LambdaDestination(parseBraketResultLambda), {
                prefix: `${this.props.prefix}/qc_task_output/`,
                suffix: 'results.json'
            });
    }

}