import * as cdk from '@aws-cdk/core'
import * as s3 from '@aws-cdk/aws-s3'
import * as kms from '@aws-cdk/aws-kms'

import {
    CfnNotebookInstanceLifecycleConfig,
    CfnNotebookInstance
} from '@aws-cdk/aws-sagemaker'

import {
    readFileSync
} from 'fs'

import {
    Construct,
} from '@aws-cdk/core'

import {
    RoleUtil
} from './utils/utils-role'



export interface Props {
    region: string;
    account: string;
    bucket: s3.Bucket;
    prefix: string;
    stackName: string
}

export class Notebook extends Construct {

    private props: Props;
    private roleUtil: RoleUtil;

    // constructor 
    constructor(scope: Construct, id: string, props: Props) {
        super(scope, id);
        this.props = props
        const INSTANCE_TYPE = 'ml.c5.xlarge'

        this.roleUtil = RoleUtil.newInstance(this, props);

        const instanceTypeParam = new cdk.CfnParameter(this, "NotebookInstanceType", {
            type: "String",
            default: INSTANCE_TYPE,
            description: "Sagemaker notebook instance type"
        });

        const notebookRole = this.roleUtil.createNotebookIamRole()

        let onStartContent = readFileSync(`${__dirname}/resources/onStart.template`, 'utf-8')
        
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

        // const gitConfigProperty = {
        //     // TODO:
        //     // this will be set to the github repository of this project after open source
        //     repositoryUrl: 'TBD',
        // };

        const notebookInstnce = new CfnNotebookInstance(this, 'Notebook', {
            instanceType: instanceTypeParam.valueAsString,
            roleArn: notebookRole.roleArn,
            rootAccess: 'Enabled',
            lifecycleConfigName: installBraketSdK.attrNotebookInstanceLifecycleConfigName,
            volumeSizeInGb: 50,
            kmsKeyId: qcNotebookKey.keyId,
            //defaultCodeRepository: gitConfigProperty.repositoryUrl
        });

        
        // Output //////////////////////////
        const notebookUrl = `https://console.aws.amazon.com/sagemaker/home?region=${this.props.region}#/notebook-instances/openNotebook/${notebookInstnce.attrNotebookInstanceName}?view=classic`

        new cdk.CfnOutput(this, "notebookUrl", {
            value: notebookUrl,
            description: "Notebook URL"
        });
    }

}