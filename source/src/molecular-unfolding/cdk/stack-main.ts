
import {
  aws_s3 as s3,
  Aspects,
  StackProps,
  CfnCondition,
  Fn,
  RemovalPolicy,
  CfnOutput,
  CfnRule
} from 'aws-cdk-lib';


import {
  Construct,
} from 'constructs';

import {
  SolutionStack,
} from '../../stack';


import {
  Benchmark,
} from './construct-benchmark';

import {
  Dashboard,
} from './construct-dashboard';

import {
  EventListener,
} from './construct-listener';
import {
  Notebook,
} from './construct-notebook';

import create_custom_resources from './utils/custom-resource';
import {
  AddCfnNag,
  AddCondition,
} from './utils/utils';
import setup_vpc_and_sg from './utils/vpc';

export class MainStack extends SolutionStack {

  // constructor
  constructor(scope: Construct, id: string, props: StackProps = {}) {
    const DESCRIPTION = '(SO8033) Quantum Ready Solution For Drug Discovery';
    super(scope, id, props);
    this.setDescription(DESCRIPTION);
    const stackName = this.stackName.replace(/[^a-zA-Z0-9_]+/, '').toLocaleLowerCase();

    new CfnRule(this, 'deploymentRegionRules', {
      'assertions': [{
        'assert': Fn.conditionContains(['us-west-2', 'us-east-1'], this.region),
        'assertDescription': 'deployment regions'
      }]
    });

    const prefix = 'molecular-unfolding';

    const crossEventRegionCondition = new CfnCondition(this, 'CrossEventRegionCondition', {
      expression: Fn.conditionNot(
        Fn.conditionEquals(this.region, 'us-west-2'),
      ),
    });

    const logS3bucket = new s3.Bucket(this, 'AccessLogS3Bucket', {
      removalPolicy: RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
      enforceSSL: true,
      encryption: s3.BucketEncryption.S3_MANAGED,
    });

    const bucketName = `amazon-braket-${stackName}-${this.account}-${this.region}`;
    const s3bucket = new s3.Bucket(this, 'amazon-braket', {
      removalPolicy: RemovalPolicy.DESTROY,
      bucketName,
      autoDeleteObjects: true,
      enforceSSL: true,
      encryption: s3.BucketEncryption.S3_MANAGED,
      serverAccessLogsBucket: logS3bucket,
      serverAccessLogsPrefix: `accesslogs/${bucketName}/`,
    });
    s3bucket.node.addDependency(logS3bucket);

    let usePreBuildImage = stackName.endsWith('dev');

    new CfnOutput(this, 'bucketName', {
      value: s3bucket.bucketName,
      description: 'S3 bucket name',
    });

    const {
      vpc,
      batchSg,
      lambdaSg,
    } = setup_vpc_and_sg(this);

    create_custom_resources(this, {
      vpc,
      sg: lambdaSg,
      crossEventRegionCondition,
    });
    Aspects.of(this).add(new AddCondition(crossEventRegionCondition));

    // Notebook //////////////////////////
    new Notebook(this, 'MolUnfNotebook', {
      account: this.account,
      region: this.region,
      bucket: s3bucket,
      prefix,
      notebookSg: batchSg,
      vpc,
      stackName,
    });

    // Dashboard //////////////////////////
    const dashboard = new Dashboard(this, 'MolUnfDashboard', {
      account: this.account,
      region: this.region,
      bucket: s3bucket,
      prefix,
      stackName,
    });

    // Benchmark StepFuncs //////////////////////////
    new Benchmark(this, 'MolUnfBenchmark', {
      account: this.account,
      region: this.region,
      bucket: s3bucket,
      prefix,
      usePreBuildImage,
      dashboardUrl: dashboard.outputDashboardUrl.value,
      vpc,
      batchSg,
      lambdaSg,
      stackName,
    });


    // Event Listener Lambda //////////////////////////
    new EventListener(this, 'BraketTaskEventHandler', {
      account: this.account,
      region: this.region,
      bucket: s3bucket,
      prefix,
      usePreBuildImage,
      vpc,
      lambdaSg,
      stackName,
    });
    Aspects.of(this).add(new AddCfnNag());
  }

}