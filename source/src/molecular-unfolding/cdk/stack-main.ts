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
  aws_s3 as s3,
  StackProps,
  Fn,
  RemovalPolicy,
  CfnOutput,
  Aspects,
  CfnCondition,
  CfnRule,
  CfnStack,
  CfnParameter,
} from 'aws-cdk-lib';

import {
  Construct,
} from 'constructs';

import {
  SolutionStack,
} from '../../stack';

import {
  BatchEvaluationNestStack,
} from './stack-batch-evaluation';
import { NotebookNestStack } from './stack-notebook';
import {
  VisualizationNestStack,
} from './stack-visualization';
import {
  AddCfnNag,
} from './utils/utils';

import setup_vpc_and_sg from './utils/vpc';

export class MainStack extends SolutionStack {
  static SOLUTION_ID = 'SO8027'
  static SOLUTION_NAME = 'Quantum Computing Exploration for Drug Discovery on AWS'
  static SOLUTION_VERSION = process.env.SOLUTION_VERSION || 'v1.0.0'
  static DESCRIPTION = `(${MainStack.SOLUTION_ID}) ${MainStack.SOLUTION_NAME} (Version ${MainStack.SOLUTION_VERSION})`;

  // constructor
  constructor(scope: Construct, id: string, props: StackProps = {}) {

    super(scope, id, props);
    this.setDescription(MainStack.DESCRIPTION);
    const stackName = this.stackName.replace(/[^a-zA-Z0-9_]+/, '').toLocaleLowerCase();

    const deployNotebook = new CfnParameter(this, 'DeployNotebook', {
      description: 'Notebook. Choose yes to activate.',
      default: 'yes',
      type: 'String',
      allowedValues: ['yes', 'no'],
    });
    const deployBatchEvaluation = new CfnParameter(this, 'DeployBatchEvaluation', {
      description: 'Batch Evaluation. Choose yes to activate.',
      default: 'yes',
      type: 'String',
      allowedValues: ['yes', 'no'],
    });
    const deployVisualization = new CfnParameter(this, 'DeployVisualization', {
      description: 'Visualization. Choose yes to activate. If choose yes, you need to grant permissions in advance. For more information, see the section Grant permissions for Visualization in this chapter https://awslabs.github.io/quantum-computing-exploration-for-drug-discovery-on-aws/en/deployment/',
      default: 'no',
      type: 'String',
      allowedValues: ['yes', 'no'],
    });

    const quickSightUserParam = new CfnParameter(this, 'QuickSightUser', {
      type: 'String',
      description: 'QuickSight User, find user name from https://us-east-1.quicksight.aws.amazon.com/sn/admin',
      default: '',
    });

    const quickSightRoleNameParam = new CfnParameter(this, 'QuickSightRoleName', {
      type: 'String',
      description: 'QuickSight IAM role name',
      default: '',
    });

    const conditionDeployNotebook = new CfnCondition(this, 'ConditionDeployNotebook', {
      expression: Fn.conditionEquals(
        deployNotebook.valueAsString, 'yes',
      ),
    });
    const conditionDeployBatchEvaluation = new CfnCondition(this, 'ConditionDeployBatchEvaluation', {
      expression: Fn.conditionEquals(
        deployBatchEvaluation.valueAsString, 'yes',
      ),
    });
    const conditionDeployVisualization = new CfnCondition(this, 'ConditionDeployVisualization', {
      expression: Fn.conditionEquals(
        deployVisualization.valueAsString, 'yes',
      ),
    });

    const scenario = 'Molecular Unfolding';

    this.templateOptions.metadata = {
      'AWS::CloudFormation::Interface': {
        ParameterGroups: [
          {
            Label: { default: `${scenario} - Notebook` },
            Parameters: [deployNotebook.logicalId],
          },

          {
            Label: { default: `${scenario} - Batch Evaluation` },
            Parameters: [deployBatchEvaluation.logicalId],
          },

          {
            Label: { default: `${scenario} - Visualization` },
            Parameters: [
              deployVisualization.logicalId,
              quickSightUserParam.logicalId,
              quickSightRoleNameParam.logicalId,
            ],
          },

        ],
        ParameterLabels: {
          [deployNotebook.logicalId]: {
            default: 'Deploy Notebook',
          },

          [deployBatchEvaluation.logicalId]: {
            default: 'Deploy Batch Evaluation',
          },

          [deployVisualization.logicalId]: {
            default: 'Deploy Visualization',
          },

          [quickSightUserParam.logicalId]: {
            default: 'QuickSight User',
          },

          [quickSightRoleNameParam.logicalId]: {
            default: 'QuickSight Role Name',
          },
        },
      },
    };

    const supportRegions = ['us-west-2', 'us-east-1', 'eu-west-2'];
    new CfnRule(this, 'SupportedRegionsRule', {
      assertions: [{
        assert: Fn.conditionContains(supportRegions, this.region),
        assertDescription: 'supported regions are ' + supportRegions.join(', '),
      }],
    });

    const prefix = scenario.split(' ').join('-').toLowerCase();

    const logS3bucket = new s3.Bucket(this, 'AccessLogS3Bucket', {
      removalPolicy: RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
      enforceSSL: true,
      encryption: s3.BucketEncryption.S3_MANAGED,
    });

    const bucketName = `amazon-braket-${stackName}-${this.account}-${this.region}`;
    const s3bucket = new s3.Bucket(this, 'amazon-braket', {
      removalPolicy: RemovalPolicy.DESTROY,
      bucketName,
      autoDeleteObjects: true,
      enforceSSL: true,
      encryption: s3.BucketEncryption.S3_MANAGED,
      serverAccessLogsBucket: logS3bucket,
      serverAccessLogsPrefix: `accesslogs/${bucketName}/`,
    });

    s3bucket.node.addDependency(logS3bucket);

    new CfnOutput(this, 'BucketName', {
      value: s3bucket.bucketName,
      description: 'S3 Bucket Name',
    });

    const {
      vpc,
      batchSg,
      lambdaSg,
    } = setup_vpc_and_sg(this);

    {
      // Notebook //////////////////////////
      const notebook = new NotebookNestStack(this, 'Notebook', {
        bucket: s3bucket,
        prefix,
        vpc,
        batchSg,
        stackName,
      });
      (notebook.nestedStackResource as CfnStack).cfnOptions.condition = conditionDeployNotebook;
      this.addOutput('NotebookURL', notebook.notebookUrlOutput, conditionDeployNotebook);
      notebook.node.addDependency(s3bucket);
      notebook.node.addDependency(vpc);
    }

    {
      // BatchEvaluation //////////////////////////
      const batchEvaluation = new BatchEvaluationNestStack(this, 'BatchEvaluation', {
        bucket: s3bucket,
        prefix,
        vpc,
        batchSg,
        lambdaSg,
        stackName,
      });
      (batchEvaluation.nestedStackResource as CfnStack).cfnOptions.condition = conditionDeployBatchEvaluation;
      this.addOutput('SNSTopic', batchEvaluation.snsOutput, conditionDeployBatchEvaluation);
      this.addOutput('StateMachineURL', batchEvaluation.stateMachineURLOutput, conditionDeployBatchEvaluation);
      batchEvaluation.node.addDependency(s3bucket);
    }

    {
      // Visualization //////////////////////////
      const dashboard = new VisualizationNestStack(this, 'QuicksightDashboard', {
        prefix,
        stackName,
        bucket: s3bucket,
        quickSightRoleName: quickSightRoleNameParam.valueAsString,
        quicksightUser: quickSightUserParam.valueAsString,
      });
      (dashboard.nestedStackResource as CfnStack).cfnOptions.condition = conditionDeployVisualization;
      this.addOutput('DashboardURL', dashboard.outputDashboardUrl, conditionDeployVisualization);
      dashboard.node.addDependency(s3bucket);
    }
    Aspects.of(this).add(new AddCfnNag());
  }

  private addOutput(name: string, output ? : CfnOutput, condition ? : CfnCondition) {
    if (output && condition) {
      new CfnOutput(this, name, {
        value: output.value,
        description: output.description,
      }).condition = condition;
    }
  }
}