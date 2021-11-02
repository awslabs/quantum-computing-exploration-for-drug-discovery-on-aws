import * as cdk from '@aws-cdk/core';
import * as quicksight from '@aws-cdk/aws-quicksight';
import {
    SolutionStack
} from '../stack'

export class QCDashboradStack extends SolutionStack {

    constructor(scope: cdk.Construct, id: string, props: cdk.StackProps = {}) {
        super(scope, id, props);
        this.setDescription('(SO8029) CDK for GCR solution: Quantum Computing in HCLS (Dashboard)');

        const quicksightTemplateAccountId = process.env.QUICKSIGHT_TEMPLATE_ACCOUNTID
        const quicksightTemplateAccountIdParam = new cdk.CfnParameter(this, "quicksightTemplateAccountId", {
            type: "String",
            default: quicksightTemplateAccountId,
            description: "The AWS account id to host quicksight template in region: us-east-1"
        });

        const defaultQuicksightUser = process.env.QUICKSIGHT_USER || `Admin-OneClick/yonmzn-Isengard`;
        const quickSightUserParam = new cdk.CfnParameter(this, "quickSightUser", {
            type: "String",
            default: defaultQuicksightUser,
            description: "Quicksight User"
        });

        const quicksightUser = `arn:aws:quicksight:us-east-1:${this.account}:user/default/${quickSightUserParam.valueAsString}`;
        const qcDataSource = new quicksight.CfnDataSource(this, "qcDataSource", {
            awsAccountId: this.account,
            dataSourceId: `${this.stackName}-qcdatasource`,
            name: 'qcdatasource',
            type: 'ATHENA',
            dataSourceParameters: {
                athenaParameters: {
                    workGroup: 'primary',
                },
            },
            permissions: [{
                principal: quicksightUser,
                actions: [
                    'quicksight:UpdateDataSourcePermissions',
                    'quicksight:DescribeDataSource',
                    'quicksight:DescribeDataSourcePermissions',
                    'quicksight:PassDataSource',
                    'quicksight:UpdateDataSource',
                    'quicksight:DeleteDataSource'
                ]
            }]
        });

        const columns = [{
                name: 'M',
                type: 'INTEGER'
            },
            {
                name: 'D',
                type: 'INTEGER'
            },
            {
                name: 'Device',
                type: 'STRING'
            },
            {
                name: 'InstanceType',
                type: 'STRING'
            },
            {
                name: 'ComputeType',
                type: 'STRING'
            },
            {
                name: 'mins',
                type: 'DECIMAL'
            },
        ];

        const qcDataset = new quicksight.CfnDataSet(this, "dataset", {
            permissions: [{
                principal: quicksightUser,
                actions: [
                    'quicksight:UpdateDataSetPermissions',
                    'quicksight:DescribeDataSet',
                    'quicksight:DescribeDataSetPermissions',
                    'quicksight:PassDataSet',
                    'quicksight:DescribeIngestion',
                    'quicksight:ListIngestions',
                    'quicksight:UpdateDataSet',
                    'quicksight:DeleteDataSet',
                    'quicksight:CreateIngestion',
                    'quicksight:CancelIngestion'
                ]
            }],
            awsAccountId: this.account,
            name: "qcdataset",
            dataSetId: `${this.stackName}-dataSetId`,
            importMode: 'DIRECT_QUERY',
            physicalTableMap: {
                ATHENATable: {
                    customSql: {
                        dataSourceArn: qcDataSource.attrArn,
                        name: 'all',
                        sqlQuery: 'SELECT M, D, Device, InstanceType, ComputeType, mins FROM "AwsDataCatalog"."default"."qc_batch_performance_view"',
                        columns
                    },
                }
            }
        });

        const templateAccountId = quicksightTemplateAccountIdParam.valueAsString.split('AA').join('');

        const templateArn = `arn:aws:quicksight:us-east-1:${templateAccountId}:template/QC-analysis-template`
        const qcAnaTemplate = new quicksight.CfnTemplate(this, "qcqsAnaTemplate", {
            awsAccountId: this.account,
            templateId: `${this.stackName}-qcqsTemplateId`,
            name: 'qcqsTemplateId',
            permissions: [{
                principal: quicksightUser,
                actions: ['quicksight:DescribeTemplate']
            }],
            sourceEntity: {
                sourceTemplate: {
                    arn: templateArn
                }
            }
        });
        const qcAnalysis = new quicksight.CfnAnalysis(this, "qcPefAnalysis", {
            awsAccountId: this.account,
            analysisId: `${this.stackName}-qcPefAnalysis`,
            name: "qcPefAnalysis",
            permissions: [{
                principal: quicksightUser,
                actions: [
                    'quicksight:RestoreAnalysis',
                    'quicksight:UpdateAnalysisPermissions',
                    'quicksight:DeleteAnalysis',
                    'quicksight:DescribeAnalysisPermissions',
                    'quicksight:QueryAnalysis',
                    'quicksight:DescribeAnalysis',
                    'quicksight:UpdateAnalysis'
                ]
            }],
            sourceEntity: {
                sourceTemplate: {
                    arn: qcAnaTemplate.attrArn,
                    dataSetReferences: [{
                        dataSetPlaceholder: 'qcds',
                        dataSetArn: qcDataset.attrArn
                    }]
                }
            },
        });

        const qcPrefDashboard = new quicksight.CfnDashboard(this, "qcPrefDashboard", {
            dashboardId: `${this.stackName}-qcPrefDashboard`,
            name: 'qcPrefDashboard',
            awsAccountId: this.account,
            permissions: [{
                principal: quicksightUser,
                actions: [
                    'quicksight:DescribeDashboard',
                    'quicksight:ListDashboardVersions',
                    'quicksight:UpdateDashboardPermissions',
                    'quicksight:QueryDashboard',
                    'quicksight:UpdateDashboard',
                    'quicksight:DeleteDashboard',
                    'quicksight:DescribeDashboardPermissions',
                    'quicksight:UpdateDashboardPublishedVersion'
                ]
            }],

            sourceEntity: {
                sourceTemplate: {
                    arn: qcAnaTemplate.attrArn,
                    dataSetReferences: [{
                        dataSetPlaceholder: 'qcds',
                        dataSetArn: qcDataset.attrArn
                    }]
                }
            },
            dashboardPublishOptions: {
                adHocFilteringOption: {
                    availabilityStatus: 'DISABLED'
                }
            }

        });

        new cdk.CfnOutput(this, "datasetID", {
            value: qcDataset.dataSetId ? qcDataset.dataSetId : "",
            description: "dataset ID"
        });

        new cdk.CfnOutput(this, "qcAnalysisArn", {
            value: qcAnalysis.attrArn,
            description: "qcAnalysis arn"
        });

        new cdk.CfnOutput(this, "qcPrefDashboardUrl", {
            value: `https://${this.region}.quicksight.aws.amazon.com/sn/dashboards/${qcPrefDashboard.dashboardId}`,
            description: "DashboardUrl Url"
        });

    }
}