import * as cdk from '@aws-cdk/core'
import * as s3 from '@aws-cdk/aws-s3'
import * as kms from '@aws-cdk/aws-kms'
import * as ec2 from '@aws-cdk/aws-ec2'

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
        this.props = props
        const INSTANCE_TYPE = 'ml.c5.xlarge'

        this.roleUtil = RoleUtil.newInstance(this, props);

        const instanceTypeParam = new cdk.CfnParameter(this, "NotebookInstanceType", {
            type: "String",
            default: INSTANCE_TYPE,
            description: "Sagemaker notebook instance type"
        });

        const defaultCodeRepository = this.node.tryGetContext('default_code_repository')
        const defaultCodeRepositoryParam = new cdk.CfnParameter(this, "defaultCodeRepository", {
            type: "String",
            default: defaultCodeRepository,
            description: "default code repository in notebook"
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

        let notebookInstance = null
        if (defaultCodeRepositoryParam.valueAsString.startsWith('https://')) {
            notebookInstance = new CfnNotebookInstance(this, 'Notebook', {
                instanceType: instanceTypeParam.valueAsString,
                roleArn: notebookRole.roleArn,
                rootAccess: 'Enabled',
                lifecycleConfigName: installBraketSdK.attrNotebookInstanceLifecycleConfigName,
                volumeSizeInGb: 50,
                kmsKeyId: qcNotebookKey.keyId,
                securityGroupIds: [this.props.notebookSg.securityGroupId],
                subnetId: this.props.vpc.selectSubnets({
                    subnetType: ec2.SubnetType.PRIVATE_WITH_NAT
                }).subnetIds[0],
                defaultCodeRepository: defaultCodeRepositoryParam.valueAsString
            });
        } else {
            notebookInstance = new CfnNotebookInstance(this, 'Notebook', {
                instanceType: instanceTypeParam.valueAsString,
                roleArn: notebookRole.roleArn,
                rootAccess: 'Enabled',
                lifecycleConfigName: installBraketSdK.attrNotebookInstanceLifecycleConfigName,
                volumeSizeInGb: 50,
                kmsKeyId: qcNotebookKey.keyId,
                securityGroupIds: [this.props.notebookSg.securityGroupId],
                subnetId: this.props.vpc.selectSubnets({
                    subnetType: ec2.SubnetType.PRIVATE_WITH_NAT
                }).subnetIds[0],
            });
        }


        // Output //////////////////////////
        const notebookUrl = `https://console.aws.amazon.com/sagemaker/home?region=${this.props.region}#/notebook-instances/openNotebook/${notebookInstance.attrNotebookInstanceName}?view=classic`

        new cdk.CfnOutput(this, "notebookUrl", {
            value: notebookUrl,
            description: "Notebook URL"
        });
    }

}