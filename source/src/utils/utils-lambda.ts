import {
  aws_lambda as lambda,
  aws_s3 as s3,
  aws_ec2 as ec2,
  Duration,
} from 'aws-cdk-lib';

import {
  Construct,
} from 'constructs';

import { AppSetting } from '../common/app-setting';

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
  bucket: s3.Bucket;
  prefix: string;
  vpc: ec2.Vpc;
  lambdaSg: ec2.SecurityGroup;
}

export class LambdaUtil {

  public static newInstance(scope: Construct, props: Props, utils: {
    roleUtil: RoleUtil;
    imageUtil: ECRImageUtil;
  }) {
    return new this(scope, props, utils);
  }


  private props: Props
  private scope: Construct
  private roleUtil: RoleUtil
  private imageUtil: ECRImageUtil

  private constructor(scope: Construct, props: Props,
    utils: {
      roleUtil: RoleUtil;
      imageUtil: ECRImageUtil;
    }) {

    this.props = props;
    this.scope = scope;
    this.roleUtil = utils.roleUtil;
    this.imageUtil = utils.imageUtil;
  }

  public createAggResultLambda(lambdaPath: string): lambda.Function {
    const vpc = this.props.vpc;
    const lambdaSg = this.props.lambdaSg;
    const aggLambdaRole = this.roleUtil.createAggResultLambdaRole();

    return new lambda.Function(this.scope, 'AggResultLambda', {
      runtime: lambda.Runtime.PYTHON_3_9,
      // code: lambda.Code.fromAsset(path.join(__dirname, '../../lambda/AthenaTableLambda/')),
      code: lambda.Code.fromAsset(`${lambdaPath}/athena-table/`),
      handler: 'app.handler',
      memorySize: 512,
      timeout: Duration.seconds(120),
      vpc,
      vpcSubnets: vpc.selectSubnets({
        subnetType: ec2.SubnetType.PRIVATE_WITH_NAT,
      }),
      role: aggLambdaRole,
      securityGroups: [lambdaSg],
      environment: {
        BUCKET: this.props.bucket.bucketName,
        SOLUTION_ID: AppSetting.SOLUTION_ID,
        SOLUTION_VERSION: AppSetting.SOLUTION_VERSION,
      },
    });
  }

  public createCheckQCDeviceLambda(imagePath: string): lambda.Function {
    const checkLambdaRole = this.roleUtil.createCheckQCDeviceLambdaRole('DeviceAvailableCheckLambdaRole');
    const code = this.imageUtil.getECRImage(ECRRepoNameEnum.Lambda_CheckDevice, imagePath) as lambda.DockerImageCode;
    const vpc = this.props.vpc;
    const lambdaSg = this.props.lambdaSg;

    // console.log('CheckQCDeviceLambda:'+code);

    return new lambda.DockerImageFunction(this.scope, 'DeviceAvailableCheckLambda', {
      code,
      memorySize: 512,
      timeout: Duration.seconds(60),
      vpc,
      vpcSubnets: vpc.selectSubnets({
        subnetType: ec2.SubnetType.PRIVATE_WITH_NAT,
      }),
      role: checkLambdaRole,
      securityGroups: [lambdaSg],
      environment: {
        SOLUTION_ID: AppSetting.SOLUTION_ID,
        SOLUTION_VERSION: AppSetting.SOLUTION_VERSION,
      },
    });
  }

  public createWaitForTokenLambda(lambdaPath: string): lambda.Function {
    const lambdaRole = this.roleUtil.createWaitForTokenLambdaRole('WaitForTokenLambdaRole');
    const vpc = this.props.vpc;
    const lambdaSg = this.props.lambdaSg;

    return new lambda.Function(this.scope, 'WaitForTokenLambda', {
      runtime: lambda.Runtime.PYTHON_3_9,
      code: lambda.Code.fromAsset(`${lambdaPath}/wait-for-token/`),
      handler: 'app.handler',
      memorySize: 512,
      timeout: Duration.seconds(120),
      vpc,
      vpcSubnets: vpc.selectSubnets({
        subnetType: ec2.SubnetType.PRIVATE_WITH_NAT,
      }),
      role: lambdaRole,
      securityGroups: [lambdaSg],
      environment: {
        SOLUTION_ID: AppSetting.SOLUTION_ID,
        SOLUTION_VERSION: AppSetting.SOLUTION_VERSION,
      },
    });
  }

  public createTaskParametersLambda(lambdaPath: string): lambda.Function {
    const lambdaRole = this.roleUtil.createTaskParametersLambdaRole('TaskParametersLambdaRole');
    const vpc = this.props.vpc;
    const lambdaSg = this.props.lambdaSg;

    return new lambda.Function(this.scope, 'TaskParametersLambda', {
      runtime: lambda.Runtime.PYTHON_3_9,
      // code: lambda.Code.fromAsset(path.join(__dirname, '../../lambda/TaskParametersLambda/')),
      code: lambda.Code.fromAsset(`${lambdaPath}/task-parameter/`),
      handler: 'app.handler',
      memorySize: 512,
      timeout: Duration.seconds(60),
      vpc,
      vpcSubnets: vpc.selectSubnets({
        subnetType: ec2.SubnetType.PRIVATE_WITH_NAT,
      }),
      role: lambdaRole,
      securityGroups: [lambdaSg],
      environment: {
        SOLUTION_ID: AppSetting.SOLUTION_ID,
        SOLUTION_VERSION: AppSetting.SOLUTION_VERSION,
      },
    });
  }
}