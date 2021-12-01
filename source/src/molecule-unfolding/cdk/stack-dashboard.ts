import * as cdk from '@aws-cdk/core';
import * as quicksight from '@aws-cdk/aws-quicksight';
import {
    SolutionStack
} from '../../stack'

export class MolUnfDashboardStack extends SolutionStack {

    constructor(scope: cdk.Construct, id: string, props: cdk.StackProps = {}) {
        super(scope, id, props);
        this.setDescription('(SO8029) CDK for GCR solution: Quantum Ready For Drug Discovery (Dashboard)');

        const quicksightTemplateAccountId = this.node.tryGetContext('quicksight_template_account_id') || process.env.QUICKSIGHT_TEMPLATE_ACCOUNTID
        const quicksightTemplateAccountIdParam = new cdk.CfnParameter(this, "quicksightTemplateAccountId", {
            type: "String",
            default: quicksightTemplateAccountId,
            description: "The AWS account id to host quicksight template in region: us-east-1"
        });

        const defaultQuicksightUser = this.node.tryGetContext('quicksight_user') || process.env.QUICKSIGHT_USER;
        const quickSightUserParam = new cdk.CfnParameter(this, "quickSightUser", {
            type: "String",
            default: defaultQuicksightUser,
            description: "Quicksight User"
        });

        const quicksightUser = `arn:aws:quicksight:us-east-1:${this.account}:user/default/${quickSightUserParam.valueAsString}`;
        const qcDataSource = new quicksight.CfnDataSource(this, "qcBenchmark-DataSource", {
            awsAccountId: this.account,
            dataSourceId: `${this.stackName}-qcBenchmark-Datasource`,
            name: `${this.stackName}-qcBenchmark-Datasource`,
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
                name: 'execution_id',
                type: 'STRING'
            },
            {
                name: 'compute_type',
                type: 'STRING'
            },
            {
                name: 'resource',
                type: 'STRING'
            },
            {
                name: 'params',
                type: 'STRING'
            },
            {
                name: 'task_duration1',
                type: 'DECIMAL'
            },
            {
                name: 'task_duration2',
                type: 'DECIMAL'
            },
            {
                name: 'task_duration3',
                type: 'DECIMAL'
            },
            {
                name: 'start_time',
                type: 'STRING'
            },
            {
                name: 'experiment_name',
                type: 'STRING'
            },
            {
                name: 'task_id',
                type: 'STRING'
            },
            {
                name: 'model_name',
                type: 'STRING'
            },
            {
                name: 'model_filename',
                type: 'STRING'
            },
            {
                name: 'scenario',
                type: 'STRING'
            },
            {
                name: 'create_time',
                type: 'STRING'
            }
        ];

        const qcDataset = new quicksight.CfnDataSet(this, "qcBenchmark-DataSet", {
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
            dataSetId: `${this.stackName}-qcBenchmark-DataSet`,
            name: `${this.stackName}-qcBenchmark-DataSet`,
            importMode: 'DIRECT_QUERY',
            physicalTableMap: {
                ATHENATable: {
                    customSql: {
                        dataSourceArn: qcDataSource.attrArn,
                        name: 'all',
                        sqlQuery: 'SELECT * FROM "AwsDataCatalog"."default"."qc_benchmark_metrics_hist"',
                        columns
                    },
                }
            }
        });

        const templateAccountId = quicksightTemplateAccountIdParam.valueAsString;

        const templateArn = `arn:aws:quicksight:us-east-1:${templateAccountId}:template/QC-benchmark-analysis-template`
        const qcAnaTemplate = new quicksight.CfnTemplate(this, "qcBenchmark-QSTemplate", {
            awsAccountId: this.account,
            templateId: `${this.stackName}-qcBenchmark-QSTemplate`,
            name: `${this.stackName}-qcBenchmark-QSTemplate`,
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

        const qcBenchmarkDashboard = new quicksight.CfnDashboard(this, "qcBenchmark-Dashboard", {
            dashboardId: `${this.stackName}-qcBenchmark-Dashboard`,
            name: `${this.stackName}-qcBenchmark-Dashboard`,
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

        new cdk.CfnOutput(this, "qcBenchmarkDashboardUrl", {
            value: `https://${this.region}.quicksight.aws.amazon.com/sn/dashboards/${qcBenchmarkDashboard.dashboardId}`,
            description: "Dashboard Url"
        });

    }
}