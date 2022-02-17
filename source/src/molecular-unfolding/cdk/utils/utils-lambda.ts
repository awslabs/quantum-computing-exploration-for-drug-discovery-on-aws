import * as cdk from 'aws-cdk-lib'
import {
    aws_lambda as lambda
} from 'aws-cdk-lib'

import {
    aws_s3 as s3
} from 'aws-cdk-lib'

import {
    aws_ec2 as ec2
} from 'aws-cdk-lib'

import {
    Construct
} from 'constructs'

import {
    RoleUtil
} from './utils-role'

import {
    ECRRepoNameEnum,
    ECRImageUtil
} from './utils-images'

import * as path from 'path'

interface Props {
    region: string;
    account: string;
    bucket: s3.Bucket;
    prefix: string;
    vpc: ec2.Vpc;
    lambdaSg: ec2.SecurityGroup;
}

export class LambdaUtil {
    private props: Props
    private scope: Construct
    private roleUtil: RoleUtil
    private imageUtil: ECRImageUtil

    private constructor(scope: Construct, props: Props,
        utils: {
            roleUtil: RoleUtil,
            imageUtil: ECRImageUtil
        }) {

        this.props = props
        this.scope = scope
        this.roleUtil = utils.roleUtil
        this.imageUtil = utils.imageUtil
    }

    public static newInstance(scope: Construct, props: Props, utils: {
        roleUtil: RoleUtil,
        imageUtil: ECRImageUtil
    }) {
        return new this(scope, props, utils);
    }

    public createAggResultLambda(): lambda.Function {
        const vpc = this.props.vpc;
        const lambdaSg = this.props.lambdaSg;
        const aggLambdaRole = this.roleUtil.createAggResultLambdaRole();
        return new lambda.Function(this.scope, 'AggResultLambda', {
            runtime: lambda.Runtime.NODEJS_14_X,
            code: lambda.Code.fromAsset(path.join(__dirname, '../../lambda/AthenaTabeLambda/')),
            handler: 'index.handler',
            memorySize: 512,
            timeout: cdk.Duration.seconds(120),
            environment: {
                BUCKET: this.props.bucket.bucketName
            },
            vpc,
            vpcSubnets: vpc.selectSubnets({
                subnetType: ec2.SubnetType.PRIVATE_WITH_NAT
            }),
            role: aggLambdaRole,
            reservedConcurrentExecutions: 30,
            securityGroups: [lambdaSg]
        });
    }

    public createCheckQCDeviceLambda(): lambda.Function {
        const checkLambdaRole = this.roleUtil.createCheckQCDeviceLambdaRole('DeviceAvailableCheckLambdaRole');
        const code = this.imageUtil.getECRImage(ECRRepoNameEnum.Lambda_CheckDevice) as lambda.DockerImageCode
        const vpc = this.props.vpc;
        const lambdaSg = this.props.lambdaSg;

        return new lambda.DockerImageFunction(this.scope, 'DeviceAvailableCheckLambda', {
            code,
            memorySize: 512,
            timeout: cdk.Duration.seconds(60),
            vpc,
            vpcSubnets: vpc.selectSubnets({
                subnetType: ec2.SubnetType.PRIVATE_WITH_NAT
            }),
            role: checkLambdaRole,
            reservedConcurrentExecutions: 30,
            securityGroups: [lambdaSg]
        })
    }

    public createWaitForTokenLambda(): lambda.Function {
        const lambdaRole = this.roleUtil.createWaitForTokenLambdaRole('WaitForTokenLambdaRole')
        const vpc = this.props.vpc;
        const lambdaSg = this.props.lambdaSg;

        return new lambda.Function(this.scope, 'WaitForTokenLambda', {
            runtime: lambda.Runtime.PYTHON_3_9,
            code: lambda.Code.fromAsset(path.join(__dirname, '../../lambda/WaitForTokenLambda/')),
            handler: 'app.handler',
            memorySize: 512,
            timeout: cdk.Duration.seconds(120),
            vpc,
            vpcSubnets: vpc.selectSubnets({
                subnetType: ec2.SubnetType.PRIVATE_WITH_NAT
            }),
            role: lambdaRole,
            reservedConcurrentExecutions: 30,
            securityGroups: [lambdaSg]
        });
    }

    public createTaskParametersLambda(): lambda.Function {
        const lambdaRole = this.roleUtil.createTaskParametersLambdaRole('TaskParametersLambdaRole');
        const vpc = this.props.vpc;
        const lambdaSg = this.props.lambdaSg;

        return new lambda.Function(this.scope, 'TaskParametersLambda', {
            runtime: lambda.Runtime.PYTHON_3_9,
            code: lambda.Code.fromAsset(path.join(__dirname, '../../lambda/TaskParametersLambda/')),
            handler: 'app.handler',
            memorySize: 512,
            timeout: cdk.Duration.seconds(60),
            vpc,
            vpcSubnets: vpc.selectSubnets({
                subnetType: ec2.SubnetType.PRIVATE_WITH_NAT
            }),
            role: lambdaRole,
            reservedConcurrentExecutions: 30,
            securityGroups: [lambdaSg]
        })
    }
}