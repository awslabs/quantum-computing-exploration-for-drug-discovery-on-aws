import * as cdk from '@aws-cdk/core';
import * as s3 from '@aws-cdk/aws-s3';
import * as kms from '@aws-cdk/aws-kms'
import setup_vpc_and_sg from './utils/vpc'

import {
  CfnNotebookInstanceLifecycleConfig,
  CfnNotebookInstance
} from '@aws-cdk/aws-sagemaker';

import {
  Aspects,
  Construct,
  StackProps,
} from '@aws-cdk/core';

import {
  readFileSync
} from 'fs';

import {
  SolutionStack
} from '../../stack';

import {
  AddCfnNag
} from './utils/utils'

import {
  MolUnfBatch
} from './construct-batch'

import {
  MolUnfDashboard
} from './construct-dashboard'

import {
  RoleUtil
} from './utils/utils-role'

import {
  EventListener
} from './construct-listener'

export class MolUnfStack extends SolutionStack {
  private roleUtil: RoleUtil

  // constructor 
  constructor(scope: Construct, id: string, props: StackProps = {}) {
    super(scope, id, props);
    this.setDescription('(SO8029) CDK for GCR solution: Quantum Ready For Drug Discovery');
    const stackName = this.stackName

    const prefix = 'molecule-unfolding'

    const INSTANCE_TYPE = 'ml.c5.xlarge'

    const instanceTypeParam = new cdk.CfnParameter(this, "NotebookInstanceType", {
      type: "String",
      default: INSTANCE_TYPE,
      description: "Sagemaker notebook instance type"
    });

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

    console.log(`usePreBuildImage: ${usePreBuildImage}`)

    this.roleUtil = RoleUtil.newInstance(this, {
      account: this.account,
      region: this.region,
      bucket: s3bucket,
      prefix,
    });

    const notebookRole = this.roleUtil.createNotebookIamRole()

    let onStartContent = readFileSync(`${__dirname}/resources/onStart.template`, 'utf-8')
    if (usePreBuildImage) {
      console.log('replace #_RUN_BUILD_#')
      onStartContent = onStartContent.replace('#_RUN_BUILD_#', '')
    }

    const base64Encode = (str: string): string => Buffer.from(str, 'binary').toString('base64');
    const onStartContentBase64 = base64Encode(onStartContent)

    const installBraketSdK = new CfnNotebookInstanceLifecycleConfig(this, 'install-braket-sdk', {
      onStart: [{
        "content": onStartContentBase64
      }]
    });

    const qcNotebookKey = new kms.Key(this, 'qcNotebookKey', {
      enableKeyRotation: true
    });

    const notebookInstnce = new CfnNotebookInstance(this, 'GCRQCLifeScienceNotebook', {
      instanceType: instanceTypeParam.valueAsString,
      roleArn: notebookRole.roleArn,
      rootAccess: 'Enabled',
      lifecycleConfigName: installBraketSdK.attrNotebookInstanceLifecycleConfigName,
      volumeSizeInGb: 50,
      kmsKeyId: qcNotebookKey.keyId
    });

    // Output //////////////////////////

    new cdk.CfnOutput(this, "notebookName", {
      value: notebookInstnce.attrNotebookInstanceName,
      description: "Notebook name"
    });

    new cdk.CfnOutput(this, "bucketName", {
      value: s3bucket.bucketName,
      description: "S3 bucket name"
    });

    const notebookUrl = `https://console.aws.amazon.com/sagemaker/home?region=${this.region}#/notebook-instances/openNotebook/${notebookInstnce.attrNotebookInstanceName}?view=classic`

    new cdk.CfnOutput(this, "notebookUrl", {
      value: notebookUrl,
      description: "Notebook URL"
    });

    const {vpc, batchSg, lambdaSg} = setup_vpc_and_sg(this)

    // Dashboard //////////////////////////
    const dashboard = new MolUnfDashboard(this, 'MolUnfDashboard', {
      account: this.account,
      region: this.region,
      bucket: s3bucket,
      prefix,
      stackName
    });

    // Batch //////////////////////////
    const batchStepFuncs = new MolUnfBatch(this, 'MolUnfBatch', {
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
      console.log("add addDependency batchStepFuncs -> notebookInstnce")
      batchStepFuncs.node.addDependency(notebookInstnce)
    }

    new EventListener(this, 'BraketTaskEventHanlder', {
      account: this.account,
      region: this.region,
      bucket: s3bucket,
      prefix,
      usePreBuildImage,
      vpc,
      lambdaSg,
    })

    Aspects.of(this).add(new AddCfnNag());
  }

}