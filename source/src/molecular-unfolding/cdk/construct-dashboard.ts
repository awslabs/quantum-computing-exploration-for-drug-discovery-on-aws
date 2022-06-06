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
  aws_quicksight as quicksight,
  CfnOutput,
  aws_s3 as s3,
  aws_iam as iam,
} from 'aws-cdk-lib';

import {
  Construct,
} from 'constructs';


interface DashBoardProps {
  region: string;
  account: string;
  stackName: string;
  quicksightUser: string;
  bucket: s3.Bucket;
}

export class Dashboard extends Construct {
  private props: DashBoardProps
  outputDashboardUrl: CfnOutput
  outputQuicksightRoleArn: CfnOutput

  constructor(scope: Construct, id: string, props: DashBoardProps) {
    super(scope, id);
    this.props = props;

    const quicksightRole = this.createQuickSightRole(scope);
    props.bucket.grantRead(quicksightRole);

    this.outputQuicksightRoleArn = new CfnOutput(scope, 'outputQuickSightRoleArn', {
      value: quicksightRole.roleArn,
      description: 'QuickSight Role Arn',
    });

    const quicksightUser = `arn:aws:quicksight:us-east-1:${this.props.account}:user/default/${this.props.quicksightUser}`;

    const templateArn = 'arn:aws:quicksight:us-east-1:366590864501:template/qc-batch-evaluation-analysis-template-v1';

    const qcDataSource = new quicksight.CfnDataSource(this, 'qcBatchEvaluation-DataSource', {
      awsAccountId: this.props.account,
      dataSourceId: `${this.props.stackName}-qcBatchEvaluation-Datasource`,
      name: `${this.props.stackName}-qcBatchEvaluation-Datasource`,
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
          'quicksight:DeleteDataSource',
        ],
      }],
    });

    const columns = [{
      name: 'execution_id',
      type: 'STRING',
    },
    {
      name: 'compute_type',
      type: 'STRING',
    },
    {
      name: 'resolver',
      type: 'STRING',
    },
    {
      name: 'complexity',
      type: 'INTEGER',
    },
    {
      name: 'end_to_end_time',
      type: 'DECIMAL',
    },
    {
      name: 'running_time',
      type: 'DECIMAL',
    },
    {
      name: 'time_info',
      type: 'STRING',
    },
    {
      name: 'start_time',
      type: 'STRING',
    },
    {
      name: 'experiment_name',
      type: 'STRING',
    },
    {
      name: 'task_id',
      type: 'STRING',
    },
    {
      name: 'model_name',
      type: 'STRING',
    },
    {
      name: 'model_filename',
      type: 'STRING',
    },
    {
      name: 'scenario',
      type: 'STRING',
    },
    {
      name: 'resource',
      type: 'STRING',
    },
    {
      name: 'model_param',
      type: 'STRING',
    },
    {
      name: 'opt_param',
      type: 'STRING',
    },
    {
      name: 'create_time',
      type: 'STRING',
    },
    {
      name: 'result_detail',
      type: 'STRING',
    },
    {
      name: 'result_location',
      type: 'STRING',
    }];

    const qcDataset = new quicksight.CfnDataSet(this, 'qcBatchEvaluation-DataSet', {
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
          'quicksight:CancelIngestion',
        ],
      }],
      awsAccountId: this.props.account,
      dataSetId: `${this.props.stackName}-qcBatchEvaluation-DataSet`,
      name: `${this.props.stackName}-qcBatchEvaluation-DataSet`,
      importMode: 'DIRECT_QUERY',
      physicalTableMap: {
        ATHENATable: {
          customSql: {
            dataSourceArn: qcDataSource.attrArn,
            name: 'all',
            sqlQuery: `SELECT * FROM "AwsDataCatalog"."qc_db"."${this.props.stackName}_qc_batch_evaluation_metrics"`,
            columns,
          },
        },
      },
    });


    const qcAnaTemplate = new quicksight.CfnTemplate(this, 'qcBatchEvaluation-QSTemplate', {
      awsAccountId: this.props.account,
      templateId: `${this.props.stackName}-qcBatchEvaluation-QSTemplate`,
      name: `${this.props.stackName}-qcBatchEvaluation-QSTemplate`,
      permissions: [{
        principal: quicksightUser,
        actions: ['quicksight:DescribeTemplate'],
      }],
      sourceEntity: {
        sourceTemplate: {
          arn: templateArn,
        },
      },
    });

    const qcBatchEvaluationDashboard = new quicksight.CfnDashboard(this, 'qcBatchEvaluation-Dashboard', {
      dashboardId: `${this.props.stackName}-qcBatchEvaluation-Dashboard`,
      name: `${this.props.stackName}-qcBatchEvaluation-Dashboard`,
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
          'quicksight:UpdateDashboardPublishedVersion',
        ],
      }],

      sourceEntity: {
        sourceTemplate: {
          arn: qcAnaTemplate.attrArn,
          dataSetReferences: [{
            dataSetPlaceholder: 'qcds',
            dataSetArn: qcDataset.attrArn,
          }],
        },
      },
      dashboardPublishOptions: {
        adHocFilteringOption: {
          availabilityStatus: 'DISABLED',
        },
      },

    });

    new quicksight.CfnAnalysis(this, 'qcBatchEvaluation-Analysis', {
      analysisId: `${this.props.stackName}-qcBatchEvaluation-Analysis`,
      name: `${this.props.stackName}-qcBatchEvaluation-Analysis`,
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
          'quicksight:DescribeAnalysisPermissions',
        ],
      }],

      sourceEntity: {
        sourceTemplate: {
          arn: qcAnaTemplate.attrArn,
          dataSetReferences: [{
            dataSetPlaceholder: 'qcds',
            dataSetArn: qcDataset.attrArn,
          }],
        },
      },

    });

    // Output //////////////////////////
    this.outputDashboardUrl = new CfnOutput(this, 'qcBatchEvaluationDashboardUrl', {
      value: `https://${this.props.region}.quicksight.aws.amazon.com/sn/dashboards/${qcBatchEvaluationDashboard.dashboardId}`,
      description: 'Quicksight Dashboard URL',
    });
  }


  private createQuickSightRole(scope: Construct): iam.Role {
    const role = new iam.Role(scope, 'qcedd-quicksight-service-role', {
      assumedBy: new iam.ServicePrincipal('quicksight.amazonaws.com'),
    });
    role.addToPolicy(new iam.PolicyStatement({
      actions: [
        'athena:BatchGetQueryExecution',
        'athena:CancelQueryExecution',
        'athena:GetCatalogs',
        'athena:GetExecutionEngine',
        'athena:GetExecutionEngines',
        'athena:GetNamespace',
        'athena:GetNamespaces',
        'athena:GetQueryExecution',
        'athena:GetQueryExecutions',
        'athena:GetQueryResults',
        'athena:GetQueryResultsStream',
        'athena:GetTable',
        'athena:GetTables',
        'athena:ListQueryExecutions',
        'athena:RunQuery',
        'athena:StartQueryExecution',
        'athena:StopQueryExecution',
        'athena:ListWorkGroups',
        'athena:ListEngineVersions',
        'athena:GetWorkGroup',
        'athena:GetDataCatalog',
        'athena:GetDatabase',
        'athena:GetTableMetadata',
        'athena:ListDataCatalogs',
        'athena:ListDatabases',
        'athena:ListTableMetadata',
      ],
      resources: [
        '*',
      ],
    }));
    role.addToPolicy(new iam.PolicyStatement({
      actions: [
        'glue:CreateDatabase',
        'glue:DeleteDatabase',
        'glue:GetDatabase',
        'glue:GetDatabases',
        'glue:UpdateDatabase',
        'glue:CreateTable',
        'glue:DeleteTable',
        'glue:BatchDeleteTable',
        'glue:UpdateTable',
        'glue:GetTable',
        'glue:GetTables',
        'glue:BatchCreatePartition',
        'glue:CreatePartition',
        'glue:DeletePartition',
        'glue:BatchDeletePartition',
        'glue:UpdatePartition',
        'glue:GetPartition',
        'glue:GetPartitions',
        'glue:BatchGetPartition',
      ],
      resources: [
        '*',
      ],
    }));
    role.addToPolicy(new iam.PolicyStatement({
      actions: [
        's3:GetBucketLocation',
        's3:GetObject',
        's3:ListBucket',
        's3:ListBucketMultipartUploads',
        's3:ListMultipartUploadParts',
        's3:AbortMultipartUpload',
        's3:CreateBucket',
        '1s3:PutObject',
        's3:PutBucketPublicAccessBlock',
      ],
      resources: [
        'arn:aws:s3:::aws-athena-query-results-*',
      ],
    }));

    return role;
  }
}