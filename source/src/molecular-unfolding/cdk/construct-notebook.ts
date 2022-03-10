import {
  readFileSync,
} from 'fs';

import {
  aws_s3 as s3,
  aws_kms as kms,
  aws_ec2 as ec2,
  CfnOutput,
} from 'aws-cdk-lib';

import {
  CfnNotebookInstanceLifecycleConfig,
  CfnNotebookInstance,
} from 'aws-cdk-lib/aws-sagemaker';


import {
  Construct,
} from 'constructs';

import {
  RoleUtil,
} from './utils/utils-role';


export interface Props {
  region: string;
  account: string;
  bucket: s3.Bucket;
  prefix: string;
  notebookSg: ec2.SecurityGroup;
  vpc: ec2.Vpc;
  stackName: string;
}

export class Notebook extends Construct {

  private props: Props;
  private roleUtil: RoleUtil;

  // constructor
  constructor(scope: Construct, id: string, props: Props) {
    super(scope, id);
    this.props = props;
    const INSTANCE_TYPE = 'ml.c5.xlarge';

    this.roleUtil = RoleUtil.newInstance(this, props);

    const githubRepo = 'https://github.com/awslabs/quantum-ready-solution-for-drug-discovery';

    const defaultCodeRepository = this.node.tryGetContext('default_code_repository') || githubRepo;

    const notebookRole = this.roleUtil.createNotebookIamRole();

    let onStartContent = readFileSync(`${__dirname}/resources/onStart.template`, 'utf-8');

    const base64Encode = (str: string): string => Buffer.from(str, 'binary').toString('base64');
    const onStartContentBase64 = base64Encode(onStartContent);

    const installBraketSdk = new CfnNotebookInstanceLifecycleConfig(this, 'install-braket-sdk', {
      onStart: [{
        content: onStartContentBase64,
      }],
    });

    const qcNotebookKey = new kms.Key(this, 'qcNotebookKey', {
      enableKeyRotation: true,
    });

    let notebookInstance = null;
    if (defaultCodeRepository.startsWith('https://')) {
      notebookInstance = new CfnNotebookInstance(this, 'Notebook', {
        instanceType: INSTANCE_TYPE,
        roleArn: notebookRole.roleArn,
        rootAccess: 'Enabled', // Lifecycle configurations need root access to be able to set up a notebook instance
        lifecycleConfigName: installBraketSdk.attrNotebookInstanceLifecycleConfigName,
        volumeSizeInGb: 50,
        kmsKeyId: qcNotebookKey.keyId,
        securityGroupIds: [this.props.notebookSg.securityGroupId],
        subnetId: this.props.vpc.selectSubnets({
          subnetType: ec2.SubnetType.PRIVATE_WITH_NAT,
        }).subnetIds[0],
        directInternetAccess: 'Disabled',
        defaultCodeRepository: defaultCodeRepository,
      });
    } else {
      notebookInstance = new CfnNotebookInstance(this, 'Notebook', {
        instanceType: INSTANCE_TYPE,
        roleArn: notebookRole.roleArn,
        rootAccess: 'Enabled',
        lifecycleConfigName: installBraketSdk.attrNotebookInstanceLifecycleConfigName,
        volumeSizeInGb: 50,
        kmsKeyId: qcNotebookKey.keyId,
        securityGroupIds: [this.props.notebookSg.securityGroupId],
        subnetId: this.props.vpc.selectSubnets({
          subnetType: ec2.SubnetType.PRIVATE_WITH_NAT,
        }).subnetIds[0],
        directInternetAccess: 'Disabled',
      });
    }


    // Output //////////////////////////
    const notebookUrl = `https://console.aws.amazon.com/sagemaker/home?region=${this.props.region}#/notebook-instances/openNotebook/${notebookInstance.attrNotebookInstanceName}?view=classic`;

    new CfnOutput(this, 'notebookUrl', {
      value: notebookUrl,
      description: 'Notebook URL',
    });
  }

}