/*
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/


import {
  readFileSync,
} from 'fs';

import * as path from 'path';

import {
  aws_kms as kms,
  aws_ec2 as ec2,
  aws_s3_assets as s3_assets,
  Fn,
} from 'aws-cdk-lib';

import {
  CfnNotebookInstanceLifecycleConfig,
  CfnNotebookInstance,
} from 'aws-cdk-lib/aws-sagemaker';


import {
  Construct,
} from 'constructs';

import * as Mustache from 'mustache';
import { genRandomDigits } from './utils/utils';
import {
  RoleUtil,
} from './utils/utils-role';


export interface Props {
  region: string;
  account: string;
  prefix: string;
  stackName: string;
  bucketName: string;
}

export class Notebook extends Construct {

  notebookUrl: string;
  private props: Props;
  private roleUtil: RoleUtil;

  // constructor
  constructor(scope: Construct, id: string, props: Props) {
    super(scope, id);
    this.props = props;
    const INSTANCE_TYPE = 'ml.c5.2xlarge';

    const srcCodeAsset = new s3_assets.Asset(this, 'srcCodeAsset', {
      path: path.join(__dirname, '../notebook/'),
    });

    this.roleUtil = RoleUtil.newInstance(this, props);

    const notebookRole = this.roleUtil.createNotebookIamRole();
    srcCodeAsset.grantRead(notebookRole);
    let onStartContent = readFileSync(`${__dirname}/resources/onStart.template`, 'utf-8');

    const rawOnStartContent = Mustache.render(onStartContent, {
      s3_code_path: srcCodeAsset.s3ObjectUrl,
      default_bucket: props.bucketName,
    });

    const installBraketSdk = new CfnNotebookInstanceLifecycleConfig(this, 'install-braket-sdk', {
      onStart: [{
        content: Fn.base64(ec2.UserData.custom(rawOnStartContent).render()),
      }],
    });

    const qcNotebookKey = new kms.Key(this, 'qcNotebookKey', {
      enableKeyRotation: true,
    });

    const notebookInstance = new CfnNotebookInstance(this, 'Notebook', {
      instanceType: INSTANCE_TYPE,
      roleArn: notebookRole.roleArn,
      rootAccess: 'Enabled',
      lifecycleConfigName: installBraketSdk.attrNotebookInstanceLifecycleConfigName,
      volumeSizeInGb: 50,
      kmsKeyId: qcNotebookKey.keyId,
      directInternetAccess: 'Enabled',
      notebookInstanceName: `amazon-braket-qc-${genRandomDigits()}`,
    });

    this.notebookUrl = `https://console.aws.amazon.com/sagemaker/home?region=${this.props.region}#/notebook-instances/openNotebook/${notebookInstance.attrNotebookInstanceName}?view=classic`;
  }

}