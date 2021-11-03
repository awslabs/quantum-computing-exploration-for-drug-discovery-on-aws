import * as cdk from '@aws-cdk/core';
import * as s3 from '@aws-cdk/aws-s3';
import * as iam from '@aws-cdk/aws-iam'
import * as kms from '@aws-cdk/aws-kms'

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
} from '../stack';

import {
  AddCfnNag,
  QCLifeScienceBatch
} from './construct-batch'


export class QCLifeScienceStack extends SolutionStack {

  // Methods //////////////////////////

  private createNotebookIamRole(): iam.Role {

    const role = new iam.Role(this, 'gcr-qc-notebook-role', {
      assumedBy: new iam.ServicePrincipal('sagemaker.amazonaws.com'),
    });

    role.addManagedPolicy(iam.ManagedPolicy.fromAwsManagedPolicyName('AmazonBraketFullAccess'))
    role.addToPolicy(new iam.PolicyStatement({
      resources: [
        'arn:aws:s3:::amazon-braket-*',
        'arn:aws:s3:::braketnotebookcdk-*',
        'arn:aws:s3:::qcstack*'
      ],
      actions: [
        "s3:GetObject",
        "s3:PutObject",
        "s3:ListBucket"
      ]
    }));

    role.addToPolicy(new iam.PolicyStatement({
      resources: [
        `arn:aws:logs:*:${this.account}:log-group:/aws/sagemaker/*`
      ],
      actions: [
        "logs:CreateLogStream",
        "logs:DescribeLogStreams",
        "logs:PutLogEvents",
        "logs:CreateLogGroup"
      ]
    }));
    Aspects.of(role).add(new AddCfnNag());
    return role;
  }

  // constructor 
  constructor(scope: Construct, id: string, props: StackProps = {}) {
    super(scope, id, props);
    this.setDescription('(SO8029) CDK for GCR solution: Quantum Computing in HCLS (Notebook)');

    const INSTANCE_TYPE = 'ml.c5.xlarge'
    const CODE_REPO = 'https://github.com/amliuyong/aws-gcr-qc-life-science-public.git'

    const instanceTypeParam = new cdk.CfnParameter(this, "NotebookInstanceType", {
      type: "String",
      default: INSTANCE_TYPE,
      description: "Sagemaker notebook instance type"
    });

    const gitHubParam = new cdk.CfnParameter(this, "GitHubRepo", {
      type: "String",
      default: CODE_REPO,
      description: "Public GitHub repository"
    });

    const s3bucket = new s3.Bucket(this, 'amazon-braket', {
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      bucketName: `amazon-braket-${this.stackName.toLowerCase()}-${this.account}-${this.region}`,
      autoDeleteObjects: true,
      encryption: s3.BucketEncryption.S3_MANAGED
    });
    Aspects.of(s3bucket).add(new AddCfnNag());

    const role = this.createNotebookIamRole()

    const onStartContent = readFileSync(`${__dirname}/../resources/onStart.template`, 'utf-8')

    const base64Encode = (str: string): string => Buffer.from(str, 'binary').toString('base64');
    const onStartContentBase64 = base64Encode(onStartContent)

    const installBraketSdK = new CfnNotebookInstanceLifecycleConfig(this, 'install-braket-sdk', {
      onStart: [{
        "content": onStartContentBase64
      }]
    });

    const qcKey = new kms.Key(this, 'qcKey', {
      enableKeyRotation: true
    });

    const notebookInstnce = new CfnNotebookInstance(this, 'GCRQCLifeScienceNotebook', {
      instanceType: instanceTypeParam.valueAsString,
      roleArn: role.roleArn,
      rootAccess: 'Enabled',
      lifecycleConfigName: installBraketSdK.attrNotebookInstanceLifecycleConfigName,
      defaultCodeRepository: gitHubParam.valueAsString,
      volumeSizeInGb: 50,
      kmsKeyId: qcKey.keyId
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

    // Batch //////////////////////////
    new QCLifeScienceBatch(this, 'QCLifeScienceBatch', {
      account: this.account,
      region: this.region,
      bucket: s3bucket
    });
  }

}