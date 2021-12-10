import * as cdk from '@aws-cdk/core';
import * as s3 from '@aws-cdk/aws-s3';
import setup_vpc_and_sg from './utils/vpc'

import {
  Aspects,
  Construct,
  StackProps,
} from '@aws-cdk/core';

import {
  SolutionStack
} from '../../stack';

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
    const stackName = this.stackName

    const prefix = 'molecule-unfolding'

    const s3bucket = new s3.Bucket(this, 'amazon-braket', {
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      bucketName: `amazon-braket-${this.stackName.toLowerCase()}-${this.account}-${this.region}`,
      autoDeleteObjects: true,
      encryption: s3.BucketEncryption.S3_MANAGED
    });

    const usePreBuildImageStrValue = (this.node.tryGetContext('use_prebuild_iamge') + '').toLowerCase() || 'false'
    let usePreBuildImage = false
    if (usePreBuildImageStrValue.toLowerCase() == 'false') {
      usePreBuildImage = false
    } else {
      usePreBuildImage = true
    }

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


    // Notebook //////////////////////////
    const notebook = new Notebook(this, 'MolUnfNotebook', {
      account: this.account,
      region: this.region,
      bucket: s3bucket,
      prefix,
      usePreBuildImage
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