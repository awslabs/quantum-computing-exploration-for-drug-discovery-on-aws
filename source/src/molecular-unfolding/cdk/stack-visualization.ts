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
  NestedStack,
  NestedStackProps,
  aws_s3 as s3,
  aws_iam as iam,
  CfnOutput,
  CfnRule,
  Fn,
} from 'aws-cdk-lib';
import {
  Construct,
} from 'constructs';
import {
  Dashboard,
} from './construct-dashboard';
import {
  MainStack,
} from './stack-main';

export interface VisualizationNestStackProps extends NestedStackProps {
  readonly prefix: string;
  readonly stackName: string;
  readonly quicksightUser: string;
  readonly bucket: s3.Bucket;
}

export class VisualizationNestStack extends NestedStack {
  outputDashboardUrl: CfnOutput;
  outputQuicksightRoleArn: CfnOutput;
  constructor(scope: Construct, id: string, props: VisualizationNestStackProps) {

    super(scope, id, props);
    const featureName = 'Visualization';
    this.templateOptions.description = `(${MainStack.SOLUTION_ID}-visualization) ${MainStack.SOLUTION_NAME} - ${featureName} (Version ${MainStack.SOLUTION_VERSION})`;

    new CfnRule(this, 'VisualizationParameterRule', {
      assertions: [{
        assert: Fn.conditionNot(
          Fn.conditionEquals(props.quicksightUser, ''),
        ),
        assertDescription: 'Parameter QuickSightUser is not set',
      }],
    });

    const quicksightRole = this.createQuickSightRole(scope);
    props.bucket.grantRead(quicksightRole);

    this.outputQuicksightRoleArn = new CfnOutput(scope, 'outputQuickSightRoleArn', {
      value: quicksightRole.roleArn,
      description: 'QuickSight Role Arn',
    });

    // Dashboard //////////////////////////
    const dashboard = new Dashboard(this, 'Dashboard', {
      account: this.account,
      region: this.region,
      stackName: props.stackName,
      quicksightUser: props.quicksightUser,
    });
    this.outputDashboardUrl = dashboard.outputDashboardUrl;
  }

  private createQuickSightRole(scope: Construct): iam.Role {
    const role = new iam.Role(scope, 'qcedd-quicksight-service-role', {
      assumedBy: new iam.ServicePrincipal('quicksight.amazonaws.com'),
    });
    role.addToPolicy(new iam.PolicyStatement({
      resources: [
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
      actions: [
        '*',
      ],
    }));
    role.addToPolicy(new iam.PolicyStatement({
      resources: [
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
      actions: [
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