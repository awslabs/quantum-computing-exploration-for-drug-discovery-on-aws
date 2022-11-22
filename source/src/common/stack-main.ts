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
import * as path from 'path';

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

// import {
//   VisualizationNestStack,
// } from '../batch-evaluation/molecular-unfolding/cdk/stack-visualization';

import {
  SolutionStack,
} from '../stack';

import {
  AddCfnNag, genTimeStampStr,
} from '../utils/utils';

import setup_vpc_and_sg from '../utils/vpc';

import { AppSetting } from './app-setting';

import {
  BatchEvaluationNestStack,
} from './stack-batch-evaluation';

import { NotebookNestStack } from './stack-notebook';

export class MainStack extends SolutionStack {

  static DESCRIPTION = `(${AppSetting.SOLUTION_ID}) ${AppSetting.SOLUTION_NAME} (Version ${AppSetting.SOLUTION_VERSION})`;
  static MOLECULAR_UNFOLDING = ' - Molecular Unfolding'
  static RNA_FOLDING = ' - Rna Folding'
  static MOLECULAR_UNFOLDING_CASE_PATH = '../batch-evaluation/molecular-unfolding';
  // static MOLECULAR_UNFOLDING_IMAGE_REL_PATH = '../batch-evaluation/molecular-unfolding/image';
  static RNA_FOLDING_CASE_PATH = '../batch-evaluation/rna-folding';
  // static RNA_FOLDING_IMAGE_REL_PATH = '../batch-evaluation/rna-folding/image';

  // constructor
  constructor(scope: Construct, id: string, props: StackProps = {}) {

    super(scope, id, props);
    this.setDescription(MainStack.DESCRIPTION);
    let stackName = this.stackName.replace(/[^a-zA-Z0-9_]+/, '').toLocaleLowerCase();

    const molecularUnfolding = new CfnParameter(this, 'molecularUnfolding', {
      description: 'Deploy the library for molecular unfolding? Choose yes to activate.',
      default: 'yes',
      type: 'String',
      allowedValues: ['yes', 'no'],
    });

    const RnaFolding = new CfnParameter(this, 'RnaFolding', {
      description: 'Deploy the library for rna folding? Choose yes to activate.',
      default: 'yes',
      type: 'String',
      allowedValues: ['yes', 'no'],
    });


    // const deployBatchEvaluation = new CfnParameter(this, 'DeployBatchEvaluation', {
    //   description: 'Batch Evaluation. Choose yes to activate.',
    //   default: 'yes',
    //   type: 'String',
    //   allowedValues: ['yes', 'no'],
    // });

    // const deployVisualization = new CfnParameter(this, 'DeployVisualization', {
    //   description: 'Visualization. Choose yes to activate. If choose yes, you need to grant permissions in advance. For more information, see the section Grant permissions for Visualization in this chapter https://awslabs.github.io/quantum-computing-exploration-for-drug-discovery-on-aws/en/deployment/',
    //   default: 'no',
    //   type: 'String',
    //   allowedValues: ['yes', 'no'],
    // });

    // const deployNotebook = new CfnParameter(this, 'DeployNotebook', {
    //   description: 'Notebook. Choose yes to activate.',
    //   default: 'yes',
    //   type: 'String',
    //   allowedValues: ['yes', 'no'],
    // });
    // const deployBatchEvaluation = new CfnParameter(this, 'DeployBatchEvaluation', {
    //   description: 'Batch Evaluation. Choose yes to activate.',
    //   default: 'yes',
    //   type: 'String',
    //   allowedValues: ['yes', 'no'],
    // });
    // const deployVisualization = new CfnParameter(this, 'DeployVisualization', {
    //   description: 'Visualization. Choose yes to activate. If choose yes, you need to grant permissions in advance. For more information, see the section Grant permissions for Visualization in this chapter https://awslabs.github.io/quantum-computing-exploration-for-drug-discovery-on-aws/en/deployment/',
    //   default: 'no',
    //   type: 'String',
    //   allowedValues: ['yes', 'no'],
    // });

    // const quickSightUserParam = new CfnParameter(this, 'QuickSightUser', {
    //   type: 'String',
    //   description: 'QuickSight User, find user name from https://us-east-1.quicksight.aws.amazon.com/sn/admin',
    //   default: '',
    // });

    // const quickSightRoleNameParam = new CfnParameter(this, 'QuickSightRoleName', {
    //   type: 'String',
    //   description: 'QuickSight IAM role name',
    //   default: '',
    // });

    const conditionDeployMolecularUnfolding = new CfnCondition(this, 'ConditionDeployMolecularUnfolding', {
      expression: Fn.conditionEquals(
        molecularUnfolding.valueAsString, 'yes',
      ),
    });

    const conditionDeployRnaFolding = new CfnCondition(this, 'ConditionDeployRnaFolding', {
      expression: Fn.conditionEquals(
        RnaFolding.valueAsString, 'yes',
      ),
    });
    // const conditionDeployNotebook = new CfnCondition(this, 'ConditionDeployNotebook', {
    //   expression: Fn.conditionEquals(
    //     deployNotebook.valueAsString, 'yes',
    //   ),
    // });
    // const conditionDeployBatchEvaluation = new CfnCondition(this, 'ConditionDeployBatchEvaluation', {
    //   expression: Fn.conditionEquals(
    //     deployBatchEvaluation.valueAsString, 'yes',
    //   ),
    // });
    // const conditionDeployVisualization = new CfnCondition(this, 'ConditionDeployVisualization', {
    //   expression: Fn.conditionEquals(
    //     deployVisualization.valueAsString, 'yes',
    //   ),
    // });

    // const scenario = 'Molecular Unfolding';

    const scenario = 'Quantum Computing Industry Solution Libraries';
    this.templateOptions.metadata = {
      'AWS::CloudFormation::Interface': {
        ParameterGroups: [
          {
            Label: { default: `${scenario}` + MainStack.MOLECULAR_UNFOLDING },
            Parameters: [molecularUnfolding.logicalId],
          },
          {
            Label: { default: `${scenario}` + MainStack.RNA_FOLDING },
            Parameters: [RnaFolding.logicalId],
          },
        ],
        ParameterLabels: {
          [molecularUnfolding.logicalId]: {
            default: 'Deploy Molecular Unfolding',
          },
          [RnaFolding.logicalId]: {
            default: 'Deploy Rna Folding',
          },
        },
      },
    };

    // this.templateOptions.metadata = {
    //   'AWS::CloudFormation::Interface': {
    //     ParameterGroups: [
    //       {
    //         Label: { default: `${scenario} - Notebook` },
    //         Parameters: [deployNotebook.logicalId],
    //       },

    //       {
    //         Label: { default: `${scenario} - Batch Evaluation` },
    //         Parameters: [deployBatchEvaluation.logicalId],
    //       },

    //       {
    //         Label: { default: `${scenario} - Visualization` },
    //         Parameters: [
    //           deployVisualization.logicalId,
    //           quickSightUserParam.logicalId,
    //           quickSightRoleNameParam.logicalId,
    //         ],
    //       },

    //     ],
    //     ParameterLabels: {
    //       [molecularUnfolding.logicalId]: {
    //         default: 'Deploy Notebook',
    //       },

    //       [deployBatchEvaluation.logicalId]: {
    //         default: 'Deploy Batch Evaluation',
    //       },

    //       [deployVisualization.logicalId]: {
    //         default: 'Deploy Visualization',
    //       },

    //       [quickSightUserParam.logicalId]: {
    //         default: 'QuickSight User',
    //       },

    //       [quickSightRoleNameParam.logicalId]: {
    //         default: 'QuickSight Role Name',
    //       },
    //     },
    //   },
    // };

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

    const bucketName = `amazon-braket-${stackName}-${genTimeStampStr(new Date)}`;
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
      // notebook //////////////////////////
      const notebook = new NotebookNestStack(this, 'notebook', {
        bucket: s3bucket,
        prefix: prefix,
        vpc,
        batchSg,
        stackName: this.stackName,
        description: MainStack.DESCRIPTION,
      });
      (notebook.nestedStackResource as CfnStack).cfnOptions.condition = conditionDeployMolecularUnfolding;
      this.addOutput('NotebookURL', notebook.notebookUrlOutput);
      notebook.node.addDependency(s3bucket);
      notebook.node.addDependency(vpc);
    }

    {
      // molecularUnfoldingBatchEvaluation //////////////////////////
      const molecularUnfoldingBatchEvaluation = new BatchEvaluationNestStack(this, 'MolecularUnfoldingBatchEvaluation', {
        bucket: s3bucket,
        prefix: prefix + MainStack.MOLECULAR_UNFOLDING,
        vpc,
        batchSg,
        lambdaSg,
        stackName: this.stackName,
        description: MainStack.DESCRIPTION,
        casePath: path.join(__dirname, MainStack.MOLECULAR_UNFOLDING_CASE_PATH),
        caseName: AppSetting.MOLECULAR_UNFOLDING,
      });
      // (batchEvaluation.nestedStackResource as CfnStack).cfnOptions.condition = conditionDeployMolecularUnfolding;
      // this.addOutput('SNSTopic', batchEvaluation.snsOutput, conditionDeployBatchEvaluation);
      // this.addOutput('StateMachineURL', batchEvaluation.stateMachineURLOutput, conditionDeployBatchEvaluation);
      this.addOutput('SNSTopic-MolecularUnfolding' + MainStack.MOLECULAR_UNFOLDING, molecularUnfoldingBatchEvaluation.snsOutput, conditionDeployMolecularUnfolding);
      (molecularUnfoldingBatchEvaluation.nestedStackResource as CfnStack).cfnOptions.condition = conditionDeployMolecularUnfolding;
      this.addOutput('StateMachineURL-MolecularUnfolding' + MainStack.MOLECULAR_UNFOLDING, molecularUnfoldingBatchEvaluation.stateMachineURLOutput, conditionDeployMolecularUnfolding);
      molecularUnfoldingBatchEvaluation.node.addDependency(s3bucket);
    }

    {
      // rnaFoldingBatchEvaluation //////////////////////////
      const rnaFoldingBatchEvaluation = new BatchEvaluationNestStack(this, 'RnaFoldingBatchEvaluation', {
        bucket: s3bucket,
        prefix: prefix + MainStack.RNA_FOLDING,
        vpc,
        batchSg,
        lambdaSg,
        stackName: this.stackName,
        description: MainStack.DESCRIPTION,
        casePath: path.join(__dirname, MainStack.RNA_FOLDING_CASE_PATH),
        caseName: AppSetting.RNA_FOLDING,
      });
      // (batchEvaluation.nestedStackResource as CfnStack).cfnOptions.condition = conditionDeployMolecularUnfolding;
      // this.addOutput('SNSTopic', batchEvaluation.snsOutput, conditionDeployBatchEvaluation);
      // this.addOutput('StateMachineURL', batchEvaluation.stateMachineURLOutput, conditionDeployBatchEvaluation);
      this.addOutput('SNSTopic-RnaFolding' + MainStack.RNA_FOLDING, rnaFoldingBatchEvaluation.snsOutput, conditionDeployRnaFolding);
      (rnaFoldingBatchEvaluation.nestedStackResource as CfnStack).cfnOptions.condition = conditionDeployMolecularUnfolding;
      this.addOutput('StateMachineURL-RnaFolding' + MainStack.RNA_FOLDING, rnaFoldingBatchEvaluation.stateMachineURLOutput, conditionDeployRnaFolding);
      rnaFoldingBatchEvaluation.node.addDependency(s3bucket);
    }


    // {
    //   // visualization //////////////////////////
    //   const dashboard = new VisualizationNestStack(this, 'Dashboard', {
    //     prefix: prefix,
    //     stackName: this.stackName,
    //     bucket: s3bucket,
    //     quickSightRoleName: quickSightRoleNameParam.valueAsString,
    //     quicksightUser: quickSightUserParam.valueAsString,
    //   });
    //   // (dashboard.nestedStackResource as CfnStack).cfnOptions.condition = conditionDeployMolecularUnfolding;
    //   // this.addOutput('DashboardURL', dashboard.outputDashboardUrl, conditionDeployVisualization);
    //   this.addOutput('WorkspaceURL', dashboard.outputDashboardUrl);
    //   dashboard.node.addDependency(s3bucket);
    // }

    // {
    //   // rnaFoldingVisualization //////////////////////////
    //   const rnaFoldingVisualization = new VisualizationNestStack(this, 'QuicksightDashboard', {
    //     prefix: prefix + MainStack.RNA_FOLDING,
    //     stackName: this.stackName,
    //     bucket: s3bucket,
    //     quickSightRoleName: quickSightRoleNameParam.valueAsString,
    //     quicksightUser: quickSightUserParam.valueAsString,
    //   });
    //   // (dashboard.nestedStackResource as CfnStack).cfnOptions.condition = conditionDeployMolecularUnfolding;
    //   // this.addOutput('DashboardURL', dashboard.outputDashboardUrl, conditionDeployVisualization);
    //   this.addOutput('DashboardURL' + MainStack.RNA_FOLDING, rnaFoldingVisualization.outputDashboardUrl, conditionDeployRnaFolding);
    //   rnaFoldingVisualization.node.addDependency(s3bucket);
    // }
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