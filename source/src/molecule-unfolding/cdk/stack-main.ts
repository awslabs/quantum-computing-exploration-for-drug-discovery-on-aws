import * as cdk from '@aws-cdk/core'
import * as s3 from '@aws-cdk/aws-s3'
import setup_vpc_and_sg from './utils/vpc'
// import {
//   Asset
// } from '@aws-cdk/aws-s3-assets'
// const path = require('path')

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
  
    //console.log(`usePreBuildImage: ${usePreBuildImage}`)

    new cdk.CfnOutput(this, "bucketName", {
      value: s3bucket.bucketName,
      description: "S3 bucket name"
    });

    const {
      vpc,
      batchSg,
      lambdaSg
    } = setup_vpc_and_sg(this)


    // const codeAsset = new Asset(this, "Code", {
    //   path: path.join(__dirname, "../../")
    // });

    // new cdk.CfnOutput(this, 'SourceCode', {
    //   value: `s3://${codeAsset.s3BucketName}/${codeAsset.s3ObjectKey}`,
    //   description: "SourceCode",
    // });


    // Notebook //////////////////////////
    const notebook = new Notebook(this, 'MolUnfNotebook', {
      account: this.account,
      region: this.region,
      bucket: s3bucket,
      prefix
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
    const benchmarkStepFuncs = new Benchmark(this, 'MolUnfbenchmark', {
      account: this.account,
      region: this.region,
      bucket: s3bucket,
      prefix,
      usePreBuildImage,
      dashboardUrl: dashboard.outputDashboradUrl.value,
      vpc,
      batchSg,
      lambdaSg,
      stackName
    });

    if (usePreBuildImage) {
      //console.log("add addDependency batchStepFuncs -> notebook")
      benchmarkStepFuncs.node.addDependency(notebook)
    }

    // Event Listener Lambda //////////////////////////
    new EventListener(this, 'BraketTaskEventHanlder', {
      account: this.account,
      region: this.region,
      bucket: s3bucket,
      prefix,
      usePreBuildImage,
      vpc,
      lambdaSg,
    });
    Aspects.of(this).add(new AddCfnNag());
  }

}