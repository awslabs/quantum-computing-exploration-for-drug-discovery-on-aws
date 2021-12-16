import * as cdk from '@aws-cdk/core';
import * as s3 from '@aws-cdk/aws-s3'
import * as quicksight from '@aws-cdk/aws-quicksight';

interface DashBoardProps {
    region: string;
    account: string;
    bucket: s3.Bucket;
    stackName: string;
    prefix: string;
}

export class Dashboard extends cdk.Construct {
    private props: DashBoardProps
    outputDashboradUrl: cdk.CfnOutput

    constructor(scope: cdk.Construct, id: string, props: DashBoardProps) {
        super(scope, id);
        this.props = props

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

        const templateAccountId = quicksightTemplateAccountIdParam.valueAsString;
        const templateRegion = this.node.tryGetContext('quicksight_template_region') || 'us-east-1'
        const templateArn = `arn:aws:quicksight:${templateRegion}:${templateAccountId}:template/QC-benchmark-analysis-template`

        const quicksightUser = `arn:aws:quicksight:us-east-1:${this.props.account}:user/default/${quickSightUserParam.valueAsString}`;
        const qcDataSource = new quicksight.CfnDataSource(this, "qcBenchmark-DataSource", {
            awsAccountId: this.props.account,
            dataSourceId: `${this.props.stackName}-qcBenchmark-Datasource`,
            name: `${this.props.stackName}-qcBenchmark-Datasource`,
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
                name: 'opt_params',
                type: 'STRING'
            },
            {
                name: 'task_duration',
                type: 'DECIMAL'
            },
            {
                name: 'time_info',
                type: 'STRING'
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
            },
            {
                name: 'result_detail',
                type: 'STRING'
            },
            {
                name: 'result_location',
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
            awsAccountId: this.props.account,
            dataSetId: `${this.props.stackName}-qcBenchmark-DataSet`,
            name: `${this.props.stackName}-qcBenchmark-DataSet`,
            importMode: 'DIRECT_QUERY',
            physicalTableMap: {
                ATHENATable: {
                    customSql: {
                        dataSourceArn: qcDataSource.attrArn,
                        name: 'all',
                        sqlQuery: `SELECT * FROM "AwsDataCatalog"."default"."${this.props.stackName}_qc_benchmark_metrics_hist"`,
                        columns
                    },
                }
            }
        });


        const qcAnaTemplate = new quicksight.CfnTemplate(this, "qcBenchmark-QSTemplate", {
            awsAccountId: this.props.account,
            templateId: `${this.props.stackName}-qcBenchmark-QSTemplate`,
            name: `${this.props.stackName}-qcBenchmark-QSTemplate`,
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
            dashboardId: `${this.props.stackName}-qcBenchmark-Dashboard`,
            name: `${this.props.stackName}-qcBenchmark-Dashboard`,
            awsAccountId: this.props.account,
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

        const qcBenchmarkAnalysis = new quicksight.CfnAnalysis(this, "qcBenchmark-Analysis", {
            analysisId: `${this.props.stackName}-qcBenchmark-Analysis`,
            name: `${this.props.stackName}-qcBenchmark-Analysis`,
            awsAccountId: this.props.account,
            permissions: [{
                principal: quicksightUser,
                actions: [
                    'quicksight:DescribeAnalysis',
                    'quicksight:UpdateAnalysisPermissions',
                    'quicksight:QueryAnalysis',
                    'quicksight:UpdateAnalysis',
                    'quicksight:RestoreAnalysis',
                    'quicksight:DeleteAnalysis',
                    'quicksight:DescribeAnalysisPermissions'
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

        // Output //////////////////////////
        this.outputDashboradUrl = new cdk.CfnOutput(this, "qcBenchmarkDashboardUrl", {
            value: `https://${this.props.region}.quicksight.aws.amazon.com/sn/dashboards/${qcBenchmarkDashboard.dashboardId}`,
            description: "Quicksight Dashboard Url"
        });

        new cdk.CfnOutput(this, "qcBenchmarkAnalysis", {
            value: qcBenchmarkAnalysis.analysisId,
            description: "Quicksight Analysis Id"
        });
    }
}