import * as cdk from 'aws-cdk-lib'

import {
    aws_s3 as s3
} from 'aws-cdk-lib'

import {
    aws_ec2 as ec2
} from 'aws-cdk-lib'


import {
    aws_lambda as lambda
} from 'aws-cdk-lib'


import {
    aws_events as events
} from 'aws-cdk-lib'


import {
    aws_events_targets as targets
} from 'aws-cdk-lib'

import {
    Construct
} from 'constructs'

import {
    ECRRepoNameEnum,
    ECRImageUtil
} from './utils/utils-images'

import {
    RoleUtil
} from './utils/utils-role'

//const s3n = require('@aws-cdk/aws-s3-notifications')

interface Props {
    region: string;
    account: string;
    bucket: s3.Bucket;
    prefix: string;
    usePreBuildImage: boolean;
    vpc: ec2.Vpc;
    lambdaSg: ec2.SecurityGroup;
    stackName: string
}

export class EventListener extends Construct {
    private images: ECRImageUtil
    private roleUtil: RoleUtil
    private props: Props

    constructor(scope: Construct, id: string, props: Props) {
        super(scope, id);
        this.props = props
        this.images = ECRImageUtil.newInstance()
        this.roleUtil = RoleUtil.newInstance(scope, this.props)
        this.createEventListener(this.props.vpc, this.props.lambdaSg)
    }

    private createEventListener(vpc: ec2.Vpc, lambdaSg: ec2.SecurityGroup) {
        const lambdaRole = this.roleUtil.createCallBackLambdaRole("ParseBraketResultLambdaRole")
        const code = this.images.getECRImage(ECRRepoNameEnum.Lambda_ParseBraketResult) as lambda.DockerImageCode
        const parseBraketResultLambda = new lambda.DockerImageFunction(this, 'ParseBraketResultLambda', {
            code,
            memorySize: 2048,
            timeout: cdk.Duration.seconds(900),
            vpc,
            vpcSubnets: vpc.selectSubnets({
                subnetType: ec2.SubnetType.PRIVATE_WITH_NAT
            }),
            role: lambdaRole,
            reservedConcurrentExecutions: 30,
            securityGroups: [lambdaSg]
        });

        const rule = new events.Rule(this, 'braketEventrule', {
            eventPattern: {
                source: ["aws.braket"],
                detailType: ["Braket Task State Change"]
            },
        });

        rule.addTarget(new targets.LambdaFunction(parseBraketResultLambda, {
            maxEventAge: cdk.Duration.hours(2),
            retryAttempts: 3,
        }));

        // this.props.bucket.addEventNotification(s3.EventType.OBJECT_CREATED,
        //     new s3n.LambdaDestination(parseBraketResultLambda), {
        //         prefix: `${this.props.prefix}/qc_task_output/`,
        //         suffix: 'results.json'
        //     });
    }



}