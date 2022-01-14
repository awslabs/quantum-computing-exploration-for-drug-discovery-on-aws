import * as cdk from '@aws-cdk/core'
import * as s3 from '@aws-cdk/aws-s3'
import setup_vpc_and_sg from './utils/vpc'

import {
  Aspects,
  Construct,
  StackProps,
} from '@aws-cdk/core'

import {
  SolutionStack
} from '../../stack'

import {
  AddCfnNag
} from './utils/utils'

import {
  Benchmark
} from './construct-benchmark'

import {
  Dashboard
} from './construct-dashboard'

import {
  Notebook
} from './construct-notebook'

import {
  EventListener
} from './construct-listener'

export class MainStack extends SolutionStack {

  // constructor 
  constructor(scope: Construct, id: string, props: StackProps = {}) {
    super(scope, id, props);
    this.setDescription('(SO8029) CDK for GCR solution: Quantum Ready For Drug Discovery');
    const stackName = this.stackName.replace(/[^a-zA-Z0-9_]+/, '').toLocaleLowerCase()

    const prefix = 'molecule-unfolding'

    const logS3bucket = new s3.Bucket(this, 'AccessLogS3Bucket', {
      removalPolicy: cdk.RemovalPolicy.RETAIN,
      //autoDeleteObjects: true,
      enforceSSL: true,
      encryption: s3.BucketEncryption.S3_MANAGED,
    });

    const bucketName = `amazon-braket-${stackName}-${this.account}-${this.region}`
    const s3bucket = new s3.Bucket(this, 'amazon-braket', {
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      bucketName,
      autoDeleteObjects: true,
      enforceSSL: true,
      encryption: s3.BucketEncryption.S3_MANAGED,
      serverAccessLogsBucket: logS3bucket,
      serverAccessLogsPrefix: `accesslogs/${bucketName}/`
    });

    let usePreBuildImage = stackName.endsWith('dev')

    new cdk.CfnOutput(this, "bucketName", {
      value: s3bucket.bucketName,
      description: "S3 bucket name"
    });

    const {
      vpc,
      batchSg,
      lambdaSg
    } = setup_vpc_and_sg(this)


    // Notebook //////////////////////////
    new Notebook(this, 'MolUnfNotebook', {
      account: this.account,
      region: this.region,
      bucket: s3bucket,
      prefix,
      notebookSg: batchSg,
      vpc,
      stackName
    });

    // Dashboard //////////////////////////
    const dashboard = new Dashboard(this, 'MolUnfDashboard', {
      account: this.account,
      region: this.region,
      bucket: s3bucket,
      prefix,
      stackName
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
      stackName
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
      stackName
    });

    Aspects.of(this).add(new AddCfnNag());
  }

}