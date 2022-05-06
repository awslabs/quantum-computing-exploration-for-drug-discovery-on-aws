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
  aws_iam as iam,
  aws_lambda as lambda,
  aws_ec2 as ec2,
  aws_stepfunctions as sfn,
  aws_stepfunctions_tasks as tasks,
  aws_sns as sns,
  aws_kms as kms,
  aws_logs as logs,
  aws_s3 as s3,
  aws_events as events,
  aws_events_targets as targets,
  CfnOutput,
  RemovalPolicy,
  Duration,
} from 'aws-cdk-lib';

import {
  Construct,
} from 'constructs';

import {
  grantKmsKeyPerm,
} from './utils/utils';
import {
  BatchUtil,
} from './utils/utils-batch';
import {
  ECRImageUtil,
} from './utils/utils-images';

import {
  LambdaUtil,
} from './utils/utils-lambda';
import {
  RoleUtil,
} from './utils/utils-role';


export interface BatchProps {
  region: string;
  account: string;
  bucket: s3.Bucket;
  prefix: string;
  vpc: ec2.Vpc;
  batchSg: ec2.SecurityGroup;
  lambdaSg: ec2.SecurityGroup;
  stackName: string;
}

export class BatchEvaluation extends Construct {
  stateMachineURLOutput: CfnOutput;
  snsOutput?: CfnOutput;
  private props: BatchProps;
  private images: ECRImageUtil
  private roleUtil: RoleUtil
  private lambdaUtil: LambdaUtil
  private batchUtil: BatchUtil
  private logKey: kms.Key
  private taskParamLambda: lambda.Function
  private waitForTokenLambda: lambda.Function

  // constructor
  constructor(scope: Construct, id: string, props: BatchProps) {
    super(scope, id);
    this.props = props;
    this.images = ECRImageUtil.newInstance(scope);
    this.roleUtil = RoleUtil.newInstance(scope, this.props);

    this.lambdaUtil = LambdaUtil.newInstance(scope, this.props, {
      roleUtil: this.roleUtil,
      imageUtil: this.images,
    });

    this.batchUtil = BatchUtil.newInstance(scope, this.props, {
      roleUtil: this.roleUtil,
      imageUtil: this.images,
    });

    this.logKey = new kms.Key(scope, 'stepFuncsLogKey', {
      enableKeyRotation: true,
    });

    const snsKey = new kms.Key(this, 'SNSKey', {
      enableKeyRotation: true,
    });

    snsKey.addToResourcePolicy(new iam.PolicyStatement({
      actions: [
        'kms:Decrypt',
        'kms:GenerateDataKey',
      ],
      principals: [new iam.ServicePrincipal('events.amazonaws.com')],
      resources: ['*'],
    }));

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
          'kms:ViaService': `sns.${props.region}.amazonaws.com`,
          'kms:CallerAccount': `${props.account}`,
        },
      },
    }));

    const topic = new sns.Topic(this, 'SNS Topic', {
      displayName: 'QC StepFunctions Workflow Execution Topic',
      masterKey: snsKey,
    });

    this.taskParamLambda = this.lambdaUtil.createTaskParametersLambda();
    this.waitForTokenLambda = this.lambdaUtil.createWaitForTokenLambda();

    const checkInputParamsStep = this.createCheckInputStep();
    const createModelStep = this.createCreateModelStep();
    const ccStateMachine = this.createCCStateMachine();
    const qcStateMachine = this.createQCStateMachine();
    const qcAndCCStateMachine = this.createCCAndQCStateMachine(ccStateMachine, qcStateMachine);
    const aggResultStep = this.createAggResultStep();
    const notifyStep = this.createSNSNotifyStep(topic);
    const postSteps = sfn.Chain.start(aggResultStep).next(notifyStep);

    const ccBranch = new tasks.StepFunctionsStartExecution(this, 'Run CC', {
      stateMachine: ccStateMachine,
      integrationPattern: sfn.IntegrationPattern.RUN_JOB,
      associateWithParent: true,
      input: sfn.TaskInput.fromObject({
        execution_id: sfn.JsonPath.stringAt('$.execution_id'),
      }),
      resultPath: '$.ccBranch',
    }).next(postSteps);

    const qcBranch = new tasks.StepFunctionsStartExecution(this, 'Run QC', {
      stateMachine: qcStateMachine,
      integrationPattern: sfn.IntegrationPattern.RUN_JOB,
      associateWithParent: true,
      input: sfn.TaskInput.fromObject({
        execution_id: sfn.JsonPath.stringAt('$.execution_id'),
      }),
      resultPath: '$.qcBranch',
    }).next(postSteps);

    const qcAndCcBranch = new tasks.StepFunctionsStartExecution(this, 'Run QC and CC', {
      stateMachine: qcAndCCStateMachine,
      integrationPattern: sfn.IntegrationPattern.RUN_JOB,
      associateWithParent: true,
      input: sfn.TaskInput.fromObject({
        execution_id: sfn.JsonPath.stringAt('$.execution_id'),
      }),
      resultPath: '$.qcAndCcBranch',
    }).next(postSteps);

    const choiceStep = new sfn.Choice(this, 'Select Running Mode')
      .when(sfn.Condition.isNotPresent('$.runMode'), qcAndCcBranch)
      .when(sfn.Condition.stringEquals('$.runMode', 'CC'), ccBranch)
      .when(sfn.Condition.stringEquals('$.runMode', 'QC'), qcBranch)
      .otherwise(qcAndCcBranch);

    const stateMachineChain = sfn.Chain.start(checkInputParamsStep).next(createModelStep)
      .next(choiceStep);

    const logGroupName = `${this.props.stackName}-BatchEvaluationStateMachineLogGroup`;
    grantKmsKeyPerm(this.logKey, logGroupName);

    const logGroup = new logs.LogGroup(this, 'BatchEvaluationStateMachineLogGroup', {
      encryptionKey: this.logKey,
      logGroupName,
      removalPolicy: RemovalPolicy.DESTROY,
      retention: logs.RetentionDays.THREE_MONTHS,
    });

    const batchEvaluationStateMachine = new sfn.StateMachine(this, 'BatchEvaluationStateMachine', {
      definition: stateMachineChain,
      timeout: Duration.hours(36),
      logs: {
        destination: logGroup,
        level: sfn.LogLevel.ALL,
      },
    });
    logGroup.grantWrite(batchEvaluationStateMachine);

    const stepFuncFailureRule = new events.Rule(this, 'stepFuncFailureRule', {
      eventPattern: {
        source: ['aws.states'],
        detailType: ['Step Functions Execution Status Change'],
        detail: {
          status: ['FAILED', 'TIMED_OUT', 'ABORTED'],
          stateMachineArn: [batchEvaluationStateMachine.stateMachineArn],
        },
      },
    });

    stepFuncFailureRule.addTarget(new targets.SnsTopic(topic, {
      message: events.RuleTargetInput.fromEventPath('$.detail'),
    }));

    // Output //////////////////////////
    this.stateMachineURLOutput = new CfnOutput(this, 'stateMachineURL', {
      value: `https://console.aws.amazon.com/states/home?region=${this.props.region}#/statemachines/view/${batchEvaluationStateMachine.stateMachineArn}`,
      description: 'State Machine URL',
    });
  }

  private createCheckInputStep(): tasks.LambdaInvoke {
    return new tasks.LambdaInvoke(this, 'Check Input', {
      lambdaFunction: this.taskParamLambda,
      payload: sfn.TaskInput.fromObject({
        's3_bucket': this.props.bucket.bucketName,
        's3_prefix': this.props.prefix,
        'param_type': 'CHECK_INPUT',
        'user_input.$': '$',
        'execution_id.$': '$$.Execution.Id',
      }),
      outputPath: '$.Payload',
    });
  }

  private createCreateModelStep(): tasks.BatchSubmitJob {
    const jobQueue = this.batchUtil.getFargateJobQueue();
    const createModelJobDef = this.batchUtil.createCreateModelJobDef();
    const createModelStep = new tasks.BatchSubmitJob(this, 'Create Model', {
      jobDefinitionArn: createModelJobDef.jobDefinitionArn,
      jobName: 'createModelTask',
      jobQueueArn: jobQueue.jobQueueArn,
      integrationPattern: sfn.IntegrationPattern.RUN_JOB,
      containerOverrides: {
        command: sfn.JsonPath.listAt('$.params'),
      },
      resultPath: sfn.JsonPath.stringAt('$.createModelStep'),
      resultSelector: {
        JobId: sfn.JsonPath.stringAt('$.JobId'),
      },
    });
    return createModelStep;
  }

  private createCCAndQCStateMachine(ccStateMachine: sfn.StateMachine, qcStateMachine: sfn.StateMachine): sfn.StateMachine {
    const ccStateMachineStep = new tasks.StepFunctionsStartExecution(this, 'Run CC StateMachine', {
      stateMachine: ccStateMachine,
      integrationPattern: sfn.IntegrationPattern.RUN_JOB,
      input: sfn.TaskInput.fromObject({
        execution_id: sfn.JsonPath.stringAt('$.execution_id'),
      }),
      resultPath: '$.ccStateMachineStep',
      associateWithParent: true,
    });

    const qcStateMachineStep = new tasks.StepFunctionsStartExecution(this, 'Run QC StateMachine', {
      stateMachine: qcStateMachine,
      integrationPattern: sfn.IntegrationPattern.RUN_JOB,
      associateWithParent: true,
      input: sfn.TaskInput.fromObject({
        execution_id: sfn.JsonPath.stringAt('$.execution_id'),
      }),
      resultPath: '$.qcStateMachineStep',
    });

    const ccAndQCParallel = new sfn.Parallel(this, 'ccAndQCParallel');
    ccAndQCParallel.branch(ccStateMachineStep);
    ccAndQCParallel.branch(qcStateMachineStep);

    const logGroupName = `${this.props.stackName}-RunCCAndQCStateMachineLogGroup`;
    grantKmsKeyPerm(this.logKey, logGroupName);

    const logGroup = new logs.LogGroup(this, 'RunCCAndQCStateMachineLogGroup', {
      encryptionKey: this.logKey,
      logGroupName,
      removalPolicy: RemovalPolicy.DESTROY,
      retention: logs.RetentionDays.THREE_MONTHS,
    });

    const ccAndQCStateMachine = new sfn.StateMachine(this, 'RunCCAndQCStateMachine', {
      definition: ccAndQCParallel,
      logs: {
        destination: logGroup,
        level: sfn.LogLevel.ALL,
      },
    });
    logGroup.grantWrite(ccAndQCStateMachine);
    return ccAndQCStateMachine;
  }

  private createQCStateMachine(): sfn.StateMachine {

    const getDeviceListLambdaStep = new tasks.LambdaInvoke(this, 'Get Device List', {
      lambdaFunction: this.taskParamLambda,
      payload: sfn.TaskInput.fromObject({
        's3_bucket': this.props.bucket.bucketName,
        's3_prefix': this.props.prefix,
        'param_type': 'QC_DEVICE_LIST',
        'execution_id': sfn.JsonPath.stringAt('$.execution_id'),
        'context.$': '$$',
      }),
      outputPath: '$.Payload',
    });

    const runOnQCDeviceStateMachine = this.createRunOnQCDeviceStateMachine();

    const runOnQCDeviceStateMachineStep = new tasks.StepFunctionsStartExecution(this, 'Run On Device', {
      stateMachine: runOnQCDeviceStateMachine,
      integrationPattern: sfn.IntegrationPattern.RUN_JOB,
      associateWithParent: true,
      input: sfn.TaskInput.fromObject({
        device_arn: sfn.JsonPath.stringAt('$.ItemValue'),
        execution_id: sfn.JsonPath.stringAt('$.execution_id'),
      }),
    });

    const parallelQCDeviceMap = new sfn.Map(this, 'parallelQCDeviceMap', {
      maxConcurrency: 20,
      itemsPath: sfn.JsonPath.stringAt('$.devices_arns'),
      parameters: {
        'ItemIndex.$': '$$.Map.Item.Index',
        'ItemValue.$': '$$.Map.Item.Value',
        'execution_id.$': '$.execution_id',
      },
      resultPath: '$.parallelQCDeviceMap',
    });
    parallelQCDeviceMap.iterator(runOnQCDeviceStateMachineStep);

    const logGroupName = `${this.props.stackName}-QCStateMachineLogGroup`;
    grantKmsKeyPerm(this.logKey, logGroupName);

    const logGroup = new logs.LogGroup(this, 'QCStateMachineLogGroup', {
      encryptionKey: this.logKey,
      logGroupName,
      removalPolicy: RemovalPolicy.DESTROY,
      retention: logs.RetentionDays.THREE_MONTHS,
    });

    const qcStateMachine = new sfn.StateMachine(this, 'QCStateMachine', {
      definition: getDeviceListLambdaStep.next(parallelQCDeviceMap),
      logs: {
        destination: logGroup,
        level: sfn.LogLevel.ALL,
      },
    });
    logGroup.grantWrite(qcStateMachine);

    return qcStateMachine;
  }

  private createRunOnQCDeviceStateMachine(): sfn.StateMachine {

    const checkQCDeviceLambda = this.lambdaUtil.createCheckQCDeviceLambda();
    const checkQCDeviceStep = new tasks.LambdaInvoke(this, 'Check Device status', {
      lambdaFunction: checkQCDeviceLambda,
      payload: sfn.TaskInput.fromObject({
        execution_id: sfn.JsonPath.stringAt('$.execution_id'),
        device_arn: sfn.JsonPath.stringAt('$.device_arn'),
      }),
      resultSelector: {
        statusPayload: sfn.JsonPath.stringAt('$.Payload'),
      },
      resultPath: sfn.JsonPath.stringAt('$.checkQCDeviceStep'),
    });

    const getParametersLambdaStep = new tasks.LambdaInvoke(this, 'Get Task Paramters', {
      lambdaFunction: this.taskParamLambda,
      payload: sfn.TaskInput.fromObject({
        's3_bucket': this.props.bucket.bucketName,
        's3_prefix': this.props.prefix,
        'param_type': 'PARAMS_FOR_QC_DEVICE',
        'device_arn.$': '$.device_arn',
        'execution_id': sfn.JsonPath.stringAt('$.execution_id'),

      }),
      outputPath: '$.Payload',
    });
    const submitQCTaskStep = this.submitQCTaskAndWaitForTokenStep();

    const parallelQCJobsMap = new sfn.Map(this, 'ParallelQCJobs', {
      maxConcurrency: 20,
      itemsPath: sfn.JsonPath.stringAt('$.qcTaskParams'),
      parameters: {
        'ItemIndex.$': '$$.Map.Item.Index',
        'ItemValue.$': '$$.Map.Item.Value',
        'execution_id.$': '$.execution_id',
      },
      resultPath: '$.parallelQCJobsMap',
    });

    parallelQCJobsMap.iterator(submitQCTaskStep);

    const deviceOfflineFail = new sfn.Fail(this, 'Device Not Online');

    const choiceStep = new sfn.Choice(this, 'Device Online ?')
      .when(sfn.Condition.stringEquals('$.checkQCDeviceStep.statusPayload.deviceStatus', 'ONLINE'),
        getParametersLambdaStep.next(parallelQCJobsMap))
      .otherwise(deviceOfflineFail);

    const chain = sfn.Chain.start(checkQCDeviceStep).next(choiceStep);

    const logGroupName = `${this.props.stackName}-QCDeviceStateMachineLogGroup`;
    grantKmsKeyPerm(this.logKey, logGroupName);

    const logGroup = new logs.LogGroup(this, 'QCDeviceStateMachineLogGroup', {
      encryptionKey: this.logKey,
      logGroupName,
      removalPolicy: RemovalPolicy.DESTROY,
      retention: logs.RetentionDays.THREE_MONTHS,
    });

    const qcDeviceStateMachine = new sfn.StateMachine(this, 'QCDeviceStateMachine', {
      definition: chain,
      logs: {
        destination: logGroup,
        level: sfn.LogLevel.ALL,
      },
    });
    logGroup.grantWrite(qcDeviceStateMachine);
    return qcDeviceStateMachine;
  }

  private createCCStateMachine(): sfn.StateMachine {
    const parametersLambdaStep = new tasks.LambdaInvoke(this, 'Get Task Parameters', {
      lambdaFunction: this.taskParamLambda,
      payload: sfn.TaskInput.fromObject({
        's3_bucket': this.props.bucket.bucketName,
        's3_prefix': this.props.prefix,
        'param_type': 'PARAMS_FOR_CC',
        'execution_id': sfn.JsonPath.stringAt('$.execution_id'),
        'context.$': '$$',
      }),
      outputPath: '$.Payload',
    });
    const ccJobQueue = this.batchUtil.getCcJobQueue();
    const jobDef = this.batchUtil.createCCBatchJobDef('CCJob_Template', 2, 4);

    const stateJson = {
      Type: 'Task',
      Resource: 'arn:aws:states:::batch:submitJob.sync',
      Parameters: {
        'JobDefinition': jobDef.jobDefinitionArn,
        'JobName.$': "States.Format('CCTask{}-{}', $.ItemIndex, $.ItemValue.task_name)",
        'JobQueue': ccJobQueue.jobQueueArn,
        'ContainerOverrides': {
          'Command.$': '$.ItemValue.params',
          'ResourceRequirements': [{
            'Type': 'VCPU',
            'Value.$': "States.Format('{}',$.ItemValue.vcpus)",
          },
          {
            'Type': 'MEMORY',
            'Value.$': "States.Format('{}', $.ItemValue.memory)",
          }],
        },
      },
      Catch: [
        {
          ErrorEquals: [
            'States.TaskFailed',
          ],
          Next: 'Batch Job Complete',
        },
      ],
      ResultSelector: {
        'JobId.$': '$.JobId',
        'JobName.$': '$.JobName',
      },
    };

    const customBatchSubmitJob = new sfn.CustomState(this, 'Run CC Batch Job', {
      stateJson,
    });

    const batchJobCompleted = new sfn.Pass(this, 'Batch Job Complete');

    const parallelCCJobsMap = new sfn.Map(this, 'ParallelCCJobs', {
      maxConcurrency: 20,
      itemsPath: sfn.JsonPath.stringAt('$.ccTaskParams'),
      parameters: {
        'ItemIndex.$': '$$.Map.Item.Index',
        'ItemValue.$': '$$.Map.Item.Value',
        'execution_id.$': '$.execution_id',
      },
      resultPath: '$.parallelCCJobsMap',
    });
    parallelCCJobsMap.iterator(customBatchSubmitJob.next(batchJobCompleted));

    const chain = sfn.Chain.start(parametersLambdaStep).next(parallelCCJobsMap);

    const logGroupName = `${this.props.stackName}-CCStateMachineLogGroup`;
    grantKmsKeyPerm(this.logKey, logGroupName);

    const logGroup = new logs.LogGroup(this, 'CCStateMachineLogGroup', {
      encryptionKey: this.logKey,
      logGroupName,
      removalPolicy: RemovalPolicy.DESTROY,
      retention: logs.RetentionDays.THREE_MONTHS,
    });

    const ccStateMachine = new sfn.StateMachine(this, 'CCStateMachine', {
      definition: chain,
      logs: {
        destination: logGroup,
        level: sfn.LogLevel.ALL,
      },
    });
    logGroup.grantWrite(ccStateMachine);

    ccStateMachine.role.addToPrincipalPolicy(new iam.PolicyStatement({
      resources: [
        `arn:aws:batch:${this.props.region}:${this.props.account}:job-definition/*`,
        `arn:aws:batch:${this.props.region}:${this.props.account}:job-queue/*`,
      ],
      actions: [
        'batch:SubmitJob',
      ],
    }));
    ccStateMachine.role.addToPrincipalPolicy(new iam.PolicyStatement({
      resources: [
        `arn:aws:events:${this.props.region}:${this.props.account}:rule/*`,
      ],
      actions: [
        'events:PutTargets',
        'events:PutRule',
        'events:DescribeRule',
      ],
    }));
    return ccStateMachine;
  }

  private createAggResultStep(): tasks.LambdaInvoke {
    const aggResultLambda = this.lambdaUtil.createAggResultLambda();
    const aggResultStep = new tasks.LambdaInvoke(this, 'Aggregate Result', {
      lambdaFunction: aggResultLambda,
      payload: sfn.TaskInput.fromObject({
        execution_id: sfn.JsonPath.stringAt('$.execution_id'),
        stackName: this.props.stackName,
        s3_prefix: this.props.prefix,
      }),
      resultSelector: {
        'Payload.$': '$.Payload',
      },
      resultPath: '$.aggResultStep',
    });
    return aggResultStep;
  }

  private submitQCTaskAndWaitForTokenStep(): sfn.Chain {
    const jobDef = this.batchUtil.createQCSubmitBatchJobDef('QCJob_Template');
    const batchQueue = this.batchUtil.getFargateJobQueue();

    const submitQCTaskStep = new tasks.BatchSubmitJob(this, 'Submit QC Task', {
      jobDefinitionArn: jobDef.jobDefinitionArn,
      jobName: 'qcTaskSubmitJob',
      jobQueueArn: batchQueue.jobQueueArn,
      containerOverrides: {
        command: sfn.JsonPath.listAt('$.ItemValue.params'),
      },
      resultSelector: {
        'JobId.$': '$.JobId',
        'JobName.$': '$.JobName',
      },
      resultPath: '$.qcTaskSubmitJob',
    });

    const waitForTokenStep = new tasks.LambdaInvoke(this, 'Wait For Complete', {
      lambdaFunction: this.waitForTokenLambda,
      payload: sfn.TaskInput.fromObject({
        execution_id: sfn.JsonPath.stringAt('$.execution_id'),
        task_token: sfn.JsonPath.taskToken,
        s3_bucket: this.props.bucket.bucketName,
        s3_prefix: this.props.prefix,
        batch_job_id: sfn.JsonPath.stringAt('$.qcTaskSubmitJob.JobId'),
        ItemValue: sfn.JsonPath.stringAt('$.ItemValue'),
        ItemIndex: sfn.JsonPath.stringAt('$.ItemIndex'),
      }),
      resultPath: '$.watiForTokenStep',
      integrationPattern: sfn.IntegrationPattern.WAIT_FOR_TASK_TOKEN,
    });

    submitQCTaskStep.addCatch(new sfn.Pass(this, 'Submit Error'), {
      errors: [sfn.Errors.TASKS_FAILED],
    });

    return submitQCTaskStep.next(waitForTokenStep);
  }


  private createSNSNotifyStep(topic: sns.Topic): tasks.SnsPublish {
    topic.addToResourcePolicy(new iam.PolicyStatement({
      effect: iam.Effect.DENY,
      principals: [new iam.AnyPrincipal()],
      actions: [
        'sns:Publish',
        'sns:Subscribe',
      ],
      resources: [
        topic.topicArn,
      ],
      conditions: {
        Bool: {
          'aws:SecureTransport': 'false',
        },
      },
    }));
    const snsStep = new tasks.SnsPublish(this, 'Notify Complete', {
      topic,
      subject: 'QC Step Functions Workflow Execution Succeeded',
      message: sfn.TaskInput.fromObject({
        status: 'SUCCEEDED',
        name: sfn.JsonPath.stringAt('$.execution_id'),
        startDate: sfn.JsonPath.stringAt('$.start_time'),
        stopDate: sfn.JsonPath.stringAt('$.aggResultStep.Payload.endTime'),
      }),
      resultPath: '$.snsStep',
    });

    this.snsOutput = new CfnOutput(this, 'SNS Topic Name', {
      value: topic.topicName,
      description: 'SNS Topic Name',
    });

    return snsStep;
  }
}