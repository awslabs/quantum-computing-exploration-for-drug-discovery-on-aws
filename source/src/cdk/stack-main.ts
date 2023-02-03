/*
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

Licensed under the Apache License, Version 2.0 (the 'License');
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an 'AS IS' BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/
import {
  aws_events as events,
  aws_events_targets as targets,
  aws_sns as sns,
  aws_s3 as s3,
  aws_kms as kms,
  aws_iam as iam,
  StackProps,
  Fn,
  CfnOutput,
  Aspects,
  CfnParameter,
  CfnRule,
  CfnCondition,
} from 'aws-cdk-lib';
import { EventField } from 'aws-cdk-lib/aws-events';

import {
  Construct,
} from 'constructs';

import {
  SolutionStack,
} from '../stack';
import { Notebook } from './construct-notebook';
import { AddCfnNag } from './utils/utils';


import setup_vpc_and_sg from './utils/vpc';


export class MainStack extends SolutionStack {
  static SOLUTION_ID = 'SO8027'
  static SOLUTION_NAME = 'Quantum Computing Exploration'
  static SOLUTION_VERSION = process.env.SOLUTION_VERSION || 'v1.1.0'
  static DESCRIPTION = `(${MainStack.SOLUTION_ID}) ${MainStack.SOLUTION_NAME} (Version ${MainStack.SOLUTION_VERSION})`;
  notebookUrlOutput: CfnOutput;

  // constructor
  constructor(scope: Construct, id: string, props: StackProps = {}) {

    super(scope, id, props);
    this.setDescription(MainStack.DESCRIPTION);
    const stackName = this.stackName.replace(/[^a-zA-Z0-9_]+/, '').toLocaleLowerCase();

    const snsEmail = new CfnParameter(this, 'snsEmail', {
      type: 'String',
      description: 'Email address for subscription - optional',
      allowedPattern: '^(\\w[-\\w.+]*@([A-Za-z0-9][-A-Za-z0-9]+\\.)+[A-Za-z]{2,14})?$',
    });

    const conditionSnsEmail = new CfnCondition(this, 'ConditionSnsEmail', {
      expression: Fn.conditionNot(
        Fn.conditionEquals(snsEmail.valueAsString, ''),
      ),
    });

    // const conditionSnsEmail = Fn.conditionNot(
    //   Fn.conditionEquals(snsEmail.valueAsString, '',)
    // );

    this.templateOptions.metadata = {
      'AWS::CloudFormation::Interface': {
        ParameterGroups: [
          {
            Label: { default: 'Email for receive notification' },
            Parameters: [snsEmail.logicalId],
          },
        ],
        ParameterLabels: {
          [snsEmail.logicalId]: {
            default: '',
          },
        },
      },
    };

    const supportRegions = ['us-west-1', 'us-west-2', 'us-east-1', 'eu-west-2'];
    new CfnRule(this, 'SupportedRegionsRule', {
      assertions: [{
        assert: Fn.conditionContains(supportRegions, this.region),
        assertDescription: 'supported regions are ' + supportRegions.join(', '),
      }],
    });

    const prefix = MainStack.SOLUTION_NAME.split(' ').join('-').toLowerCase();

    const {
      vpc,
      notebookSg,
    } = setup_vpc_and_sg(this);

    {
      const snsKey = new kms.Key(this, 'SNSKey', {
        enableKeyRotation: true,
      });

      const iamPolicyStatement = new iam.PolicyStatement({
        actions: [
          'kms:Decrypt',
          'kms:GenerateDataKey',
        ],
        principals: [new iam.ServicePrincipal('events.amazonaws.com')],
        resources: ['*'],
      });

      snsKey.addToResourcePolicy(iamPolicyStatement);

      snsKey.addToResourcePolicy(new iam.PolicyStatement({
        actions: [
          'kms:Decrypt',
          'kms:GenerateDataKey*',
          'kms:CreateGrant',
          'kms:ListGrants',
          'kms:DescribeKey',
        ],
        principals: [new iam.AnyPrincipal()],
        resources: ['*'],
        conditions: {
          StringEquals: {
            'kms:ViaService': `sns.${this.region}.amazonaws.com`,
            'kms:CallerAccount': `${this.account}`,
          },
        },
      }));
      // SNS Topic
      const topic = new sns.Topic(this, 'SubscriptionsTopic', {
        masterKey: snsKey,
      });

      const cfnTopic = topic.node.defaultChild as sns.CfnTopic;

      // eventBridge
      const eventRule = new events.Rule(this, 'eventRule', {
        eventPattern: {
          detail: {
            status: ['COMPLETED'],
          },
          source: ['aws.braket'],
          detailType: ['Braket Job State Change'],
        },
      });

      const subscription = new sns.CfnSubscription(this, 'emailSubcription', {
        topicArn: cfnTopic.ref,
        protocol: 'email',
        endpoint: snsEmail.valueAsString,
      });
      subscription.cfnOptions.condition = conditionSnsEmail;

      eventRule.addTarget(new targets.SnsTopic(topic, {
        message: events.RuleTargetInput.fromText(
          `Reminder: Job [${EventField.fromPath('$.detail.jobArn')}] is [${EventField.fromPath(
            '$.detail.status')}], StartedTime:[${EventField.fromPath('$.detail.startedAt')}], FinishedTime:[${EventField.fromPath('$.detail.endedAt')}]`,
        ),
      }));

      new CfnOutput(this, 'SNSTopic', {
        value: topic.topicName,
        description: `SNS Topic Name(${prefix})`,
      });
    }

    const logS3bucket = new s3.Bucket(this, 'accessLogs', {
      enforceSSL: true,
      encryption: s3.BucketEncryption.S3_MANAGED,
    });

    const s3bucket = new s3.Bucket(this, 'amazon-braket', {
      enforceSSL: true,
      encryption: s3.BucketEncryption.S3_MANAGED,
      serverAccessLogsBucket: logS3bucket,
      serverAccessLogsPrefix: 'accessLogs/',
    });

    {
      // Notebook //////////////////////////
      const notebook = new Notebook(this, 'Notebook', {
        account: this.account,
        region: this.region,
        prefix,
        vpc,
        notebookSg,
        stackName,
        bucketName: s3bucket.bucketName,
      });

      this.notebookUrlOutput = new CfnOutput(this, 'NotebookURL', {
        value: notebook.notebookUrl,
        description: 'Notebook URL',
      });

      notebook.node.addDependency(s3bucket);
      notebook.node.addDependency(vpc);
    }

    Aspects.of(this).add(new AddCfnNag());
  }
}
