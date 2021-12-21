import * as cdk from '@aws-cdk/core'
import * as ec2 from '@aws-cdk/aws-ec2'
import * as lambda from '@aws-cdk/aws-lambda'
import * as iam from '@aws-cdk/aws-iam'
import * as sfn from '@aws-cdk/aws-stepfunctions'
import * as tasks from '@aws-cdk/aws-stepfunctions-tasks'
import * as s3 from '@aws-cdk/aws-s3'
import * as sns from '@aws-cdk/aws-sns'
import * as kms from '@aws-cdk/aws-kms'
import * as logs from '@aws-cdk/aws-logs'

import {
    Construct,
} from '@aws-cdk/core';

import {
    ECRImageUtil
} from './utils/utils-images'

import {
    RoleUtil
} from './utils/utils-role'

import {
    LambdaUtil
} from './utils/utils-lambda'

import {
    BatchUtil
} from './utils/utils-batch'

import {
    grantKmsKeyPerm
} from './utils/utils'

export interface BatchProps {
    region: string;
    account: string;
    bucket: s3.Bucket;
    usePreBuildImage: boolean;
    dashboardUrl: string;
    prefix: string;
    vpc: ec2.Vpc;
    batchSg: ec2.SecurityGroup;
    lambdaSg: ec2.SecurityGroup;
    stackName: string;
}

export class Benchmark extends Construct {

    private props: BatchProps;
    private images: ECRImageUtil
    private roleUtil: RoleUtil
    private lambdaUtil: LambdaUtil
    private batchUtil: BatchUtil
    private logKey: kms.Key

    // constructor 
    constructor(scope: Construct, id: string, props: BatchProps) {
        super(scope, id);
        this.props = props;
        this.images = ECRImageUtil.newInstance(scope, this.props)
        this.roleUtil = RoleUtil.newInstance(scope, this.props)

        this.lambdaUtil = LambdaUtil.newInstance(scope, this.props, {
            roleUtil: this.roleUtil,
            imageUtil: this.images
        });

        this.batchUtil = BatchUtil.newInstance(scope, this.props, {
            roleUtil: this.roleUtil,
            imageUtil: this.images
        })

        this.logKey = new kms.Key(scope, 'stepFuncsLogKey', {
            enableKeyRotation: true
        });

        const taskParamLambda = this.lambdaUtil.createTaskParametersLambda()

        const checkInputParamsStep = this.createCheckInputStep(taskParamLambda)
        const createModelStep = this.createCreateModelStep();
        const hpcStateMachine = this.createHPCStateMachine(taskParamLambda);
        const qcStateMachine = this.createQCStateMachine(taskParamLambda)
        const qcAndHPCStateMachine = this.createHPCAndQCStateMachine(hpcStateMachine, qcStateMachine)
        const aggResultStep = this.createAggResultStep();
        const notifyStep = this.createSNSNotifyStep();
        const postSteps = sfn.Chain.start(aggResultStep).next(notifyStep)

        const hpcBranch = new tasks.StepFunctionsStartExecution(this, "Run HPC", {
            stateMachine: hpcStateMachine,
            integrationPattern: sfn.IntegrationPattern.RUN_JOB,
            associateWithParent: true,
            input: sfn.TaskInput.fromObject({
                "execution_id": sfn.JsonPath.stringAt("$.execution_id")
            }),
            resultPath: "$.hpcBranch"
        }).next(postSteps)

        const qcBranch = new tasks.StepFunctionsStartExecution(this, "Run QC", {
            stateMachine: qcStateMachine,
            integrationPattern: sfn.IntegrationPattern.RUN_JOB,
            associateWithParent: true,
            input: sfn.TaskInput.fromObject({
                "execution_id": sfn.JsonPath.stringAt("$.execution_id")
            }),
            resultPath: "$.qcBranch"
        }).next(postSteps)

        const qcAndHpcBranch = new tasks.StepFunctionsStartExecution(this, "Run QC and HPC", {
            stateMachine: qcAndHPCStateMachine,
            integrationPattern: sfn.IntegrationPattern.RUN_JOB,
            associateWithParent: true,
            input: sfn.TaskInput.fromObject({
                "execution_id": sfn.JsonPath.stringAt("$.execution_id")
            }),
            resultPath: "$.qcAndHpcBranch"
        }).next(postSteps)

        const choiceStep = new sfn.Choice(this, "Select Running Mode")
            .when(sfn.Condition.isNotPresent("$.runMode"), qcAndHpcBranch)
            .when(sfn.Condition.stringEquals("$.runMode", 'HPC'), hpcBranch)
            .when(sfn.Condition.stringEquals("$.runMode", 'QC'), qcBranch)
            .otherwise(qcAndHpcBranch)

        const statchMachineChain = sfn.Chain.start(checkInputParamsStep).next(createModelStep)
            .next(choiceStep)

        const logGroupName = `${this.props.stackName}-BenchmarkStateMachineLogGroup`
        grantKmsKeyPerm(this.logKey, logGroupName)

        const logGroup = new logs.LogGroup(this, 'BenchmarkStateMachineLogGroup', {
            encryptionKey: this.logKey,
            logGroupName,
            removalPolicy: cdk.RemovalPolicy.DESTROY,
            retention: logs.RetentionDays.THREE_MONTHS
        });

        const benchmarkStateMachine = new sfn.StateMachine(this, 'BenchmarkStateMachine', {
            definition: statchMachineChain,
            timeout: cdk.Duration.hours(36),
            logs: {
                destination: logGroup,
                level: sfn.LogLevel.ALL,
            },
        });
        logGroup.grantWrite(benchmarkStateMachine)

        // Output //////////////////////////
        new cdk.CfnOutput(this, "stateMachineURL", {
            value: `https://console.aws.amazon.com/states/home?region=${this.props.region}#/statemachines/view/${benchmarkStateMachine.stateMachineArn}`,
            description: "State Machine URL"
        });
    }

    private createCheckInputStep(taskParamLambda: lambda.Function): tasks.LambdaInvoke {
        return new tasks.LambdaInvoke(this, 'Check Input', {
            lambdaFunction: taskParamLambda,
            payload: sfn.TaskInput.fromObject({
                "s3_bucket": this.props.bucket.bucketName,
                "s3_prefix": this.props.prefix,
                "param_type": "CHECK_INPUT",
                "user_input.$": "$",
                "execution_id.$": "$$.Execution.Id"
            }),
            outputPath: '$.Payload'
        });
    }

    private createCreateModelStep(): tasks.BatchSubmitJob {
        const hpcJobQueue = this.batchUtil.getHpcJobQueue()
        const createModelJobDef = this.batchUtil.createCreateModelJobDef()

        const createModelStep = new tasks.BatchSubmitJob(this, 'Create Model', {
            jobDefinitionArn: createModelJobDef.jobDefinitionArn,
            jobName: "createModelTask",
            jobQueueArn: hpcJobQueue.jobQueueArn,
            integrationPattern: sfn.IntegrationPattern.RUN_JOB,
            containerOverrides: {
                command: sfn.JsonPath.listAt('$.params')
            },
            resultPath: sfn.JsonPath.stringAt("$.createModelStep"),
            resultSelector: {
                "JobId": sfn.JsonPath.stringAt("$.JobId")
            }
        });
        return createModelStep;
    }

    private createHPCAndQCStateMachine(hpcStateMachine: sfn.StateMachine, qcStateMachine: sfn.StateMachine): sfn.StateMachine {
        const hpcStateMachineStep = new tasks.StepFunctionsStartExecution(this, "Run HPC StateMachine", {
            stateMachine: hpcStateMachine,
            integrationPattern: sfn.IntegrationPattern.RUN_JOB,
            input: sfn.TaskInput.fromObject({
                "execution_id": sfn.JsonPath.stringAt("$.execution_id")
            }),
            resultPath: "$.hpcStateMachineStep",
            associateWithParent: true
        });

        const qcStateMachineStep = new tasks.StepFunctionsStartExecution(this, "Run QC StateMachine", {
            stateMachine: qcStateMachine,
            integrationPattern: sfn.IntegrationPattern.RUN_JOB,
            associateWithParent: true,
            input: sfn.TaskInput.fromObject({
                "execution_id": sfn.JsonPath.stringAt("$.execution_id")
            }),
            resultPath: "$.qcStateMachineStep",
        });

        const hpcAndQCParallel = new sfn.Parallel(this, "hpcAndQCParallel")
        hpcAndQCParallel.branch(hpcStateMachineStep)
        hpcAndQCParallel.branch(qcStateMachineStep)

        const logGroupName = `${this.props.stackName}-RunHPCAndQCStateMachineLogGroup`
        grantKmsKeyPerm(this.logKey, logGroupName)

        const logGroup = new logs.LogGroup(this, 'RunHPCAndQCStateMachineLogGroup', {
            encryptionKey: this.logKey,
            logGroupName,
            removalPolicy: cdk.RemovalPolicy.DESTROY,
            retention: logs.RetentionDays.THREE_MONTHS
        });

        const hpcAndQCStateMachine = new sfn.StateMachine(this, 'RunHPCAndQCStateMachine', {
            definition: hpcAndQCParallel,
            logs: {
                destination: logGroup,
                level: sfn.LogLevel.ALL,
            },
        });
        logGroup.grantWrite(hpcAndQCStateMachine)
        return hpcAndQCStateMachine;
    }

    private createQCStateMachine(parametersLambda: lambda.Function): sfn.StateMachine {

        const getDeviceListLambdaStep = new tasks.LambdaInvoke(this, 'Get Device List', {
            lambdaFunction: parametersLambda,
            payload: sfn.TaskInput.fromObject({
                "s3_bucket": this.props.bucket.bucketName,
                "s3_prefix": this.props.prefix,
                "param_type": "QC_DEVICE_LIST",
                "execution_id": sfn.JsonPath.stringAt("$.execution_id"),
                "context.$": "$$"
            }),
            outputPath: '$.Payload'
        });

        const runOnQCDeviceStateMachine = this.createRunOnQCDeviceStateMachine(parametersLambda)

        const runOnQCDeviceStateMachineStep = new tasks.StepFunctionsStartExecution(this, "Run On Device", {
            stateMachine: runOnQCDeviceStateMachine,
            integrationPattern: sfn.IntegrationPattern.RUN_JOB,
            associateWithParent: true,
            input: sfn.TaskInput.fromObject({
                "device_arn": sfn.JsonPath.stringAt("$.ItemValue"),
                "execution_id": sfn.JsonPath.stringAt("$.execution_id")
            })
        });

        const parallelQCDeviceMap = new sfn.Map(this, 'parallelQCDeviceMap', {
            maxConcurrency: 20,
            itemsPath: sfn.JsonPath.stringAt('$.devices_arns'),
            parameters: {
                "ItemIndex.$": "$$.Map.Item.Index",
                "ItemValue.$": "$$.Map.Item.Value",
                "execution_id.$": "$.execution_id"
            },
            resultPath: "$.parallelQCDeviceMap"
        });
        parallelQCDeviceMap.iterator(runOnQCDeviceStateMachineStep);

        const logGroupName = `${this.props.stackName}-QCStateMachineLogGroup`
        grantKmsKeyPerm(this.logKey, logGroupName)

        const logGroup = new logs.LogGroup(this, 'QCStateMachineLogGroup', {
            encryptionKey: this.logKey,
            logGroupName,
            removalPolicy: cdk.RemovalPolicy.DESTROY,
            retention: logs.RetentionDays.THREE_MONTHS
        });

        const qcStateMachine = new sfn.StateMachine(this, 'QCStateMachine', {
            definition: getDeviceListLambdaStep.next(parallelQCDeviceMap),
            logs: {
                destination: logGroup,
                level: sfn.LogLevel.ALL,
            },
        });
        logGroup.grantWrite(qcStateMachine)
        
        return qcStateMachine;
    }

    private createRunOnQCDeviceStateMachine(parametersLambda: lambda.Function): sfn.StateMachine {

        const checkQCDeviceLambda = this.lambdaUtil.createCheckQCDeviceLambda()
        const checkQCDeviceStep = new tasks.LambdaInvoke(this, "Check Device status", {
            lambdaFunction: checkQCDeviceLambda,
            payload: sfn.TaskInput.fromObject({
                "execution_id": sfn.JsonPath.stringAt("$.execution_id"),
                "device_arn": sfn.JsonPath.stringAt("$.device_arn")
            }),
            resultSelector: {
                "statusPayload": sfn.JsonPath.stringAt('$.Payload'),
            },
            resultPath: sfn.JsonPath.stringAt('$.checkQCDeviceStep')
        });

        const getParametersLambdaStep = new tasks.LambdaInvoke(this, 'Get Task Paramters', {
            lambdaFunction: parametersLambda,
            payload: sfn.TaskInput.fromObject({
                "s3_bucket": this.props.bucket.bucketName,
                "s3_prefix": this.props.prefix,
                "param_type": "PARAMS_FOR_QC_DEVICE",
                "device_arn.$": "$.device_arn",
                "execution_id": sfn.JsonPath.stringAt("$.execution_id")

            }),
            outputPath: '$.Payload'
        });

        const submitQCTaskStep = this.submitQCTaskStep();

        const parallelQCJobsMap = new sfn.Map(this, 'ParallelQCJobs', {
            maxConcurrency: 20,
            itemsPath: sfn.JsonPath.stringAt('$.qcTaskParams'),
            parameters: {
                "ItemIndex.$": "$$.Map.Item.Index",
                "ItemValue.$": "$$.Map.Item.Value",
                "execution_id.$": "$.execution_id"
            },
            resultPath: "$.parallelQCJobsMap"
        });

        parallelQCJobsMap.iterator(submitQCTaskStep);

        const deviceOfflineFail = new sfn.Fail(this, "Device Not Online")

        const choiceStep = new sfn.Choice(this, "Device Online ?")
            .when(sfn.Condition.stringEquals("$.checkQCDeviceStep.statusPayload.deviceStatus", 'ONLINE'),
                getParametersLambdaStep.next(parallelQCJobsMap))
            .otherwise(deviceOfflineFail)

        const chain = sfn.Chain.start(checkQCDeviceStep).next(choiceStep);

        const logGroupName = `${this.props.stackName}-QCDeviceStateMachineLogGroup`
        grantKmsKeyPerm(this.logKey, logGroupName)

        const logGroup = new logs.LogGroup(this, 'QCDeviceStateMachineLogGroup', {
            encryptionKey: this.logKey,
            logGroupName,
            removalPolicy: cdk.RemovalPolicy.DESTROY,
            retention: logs.RetentionDays.THREE_MONTHS
        });

        const qcDeviceStateMachine = new sfn.StateMachine(this, 'QCDeviceStateMachine', {
            definition: chain,
            logs: {
                destination: logGroup,
                level: sfn.LogLevel.ALL,
            },
        });
        logGroup.grantWrite(qcDeviceStateMachine)
        return qcDeviceStateMachine;
    }

    private createHPCStateMachine(parametersLambda: lambda.Function): sfn.StateMachine {
        const parametersLambdaStep = new tasks.LambdaInvoke(this, 'Get Task Parameters', {
            lambdaFunction: parametersLambda,
            payload: sfn.TaskInput.fromObject({
                "s3_bucket": this.props.bucket.bucketName,
                "s3_prefix": this.props.prefix,
                "param_type": "PARAMS_FOR_HPC",
                "execution_id": sfn.JsonPath.stringAt("$.execution_id"),
                "context.$": "$$"
            }),
            outputPath: '$.Payload'
        });
        const hpcJobQueue = this.batchUtil.getHpcJobQueue()
        const jobDef = this.batchUtil.createHPCBatchJobDef("HPCJob_Template", 2, 4);

        const stateJson = {
            End: true,
            Type: "Task",
            Resource: "arn:aws:states:::batch:submitJob.sync",
            Parameters: {
                JobDefinition: jobDef.jobDefinitionArn,
                "JobName.$": "States.Format('HPCTask{}-{}', $.ItemIndex, $.ItemValue.task_name)",
                JobQueue: hpcJobQueue.jobQueueArn,
                ContainerOverrides: {
                    "Command.$": "$.ItemValue.params",
                    ResourceRequirements: [{
                            Type: "VCPU",
                            "Value.$": "States.Format('{}',$.ItemValue.vcpus)"
                        },
                        {
                            Type: "MEMORY",
                            "Value.$": "States.Format('{}', $.ItemValue.memory)"
                        }
                    ]
                }
            },
            "ResultSelector": {
                "JobId.$": "$.JobId",
                "JobName.$": "$.JobName"
            }
        };

        const customBatchSubmitJob = new sfn.CustomState(this, 'Run HPC Batch Task', {
            stateJson
        });

        const parallelHPCJobsMap = new sfn.Map(this, 'ParallelHPCJobs', {
            maxConcurrency: 20,
            itemsPath: sfn.JsonPath.stringAt('$.hpcTaskParams'),
            parameters: {
                "ItemIndex.$": "$$.Map.Item.Index",
                "ItemValue.$": "$$.Map.Item.Value",
                "execution_id.$": "$.execution_id"
            },
            resultPath: "$.parallelHPCJobsMap"
        });
        parallelHPCJobsMap.iterator(customBatchSubmitJob);

        const chain = sfn.Chain.start(parametersLambdaStep).next(parallelHPCJobsMap);

        const logGroupName = `${this.props.stackName}-HPCStateMachineLogGroup`
        grantKmsKeyPerm(this.logKey, logGroupName)

        const logGroup = new logs.LogGroup(this, 'HPCStateMachineLogGroup', {
            encryptionKey: this.logKey,
            logGroupName,
            removalPolicy: cdk.RemovalPolicy.DESTROY,
            retention: logs.RetentionDays.THREE_MONTHS
        });

        const hpcStateMachine = new sfn.StateMachine(this, 'HPCStateMachine', {
            definition: chain,
            logs: {
                destination: logGroup,
                level: sfn.LogLevel.ALL,
            },
        });
        logGroup.grantWrite(hpcStateMachine)

        hpcStateMachine.role.addToPrincipalPolicy(new iam.PolicyStatement({
            resources: [
                `arn:aws:batch:${this.props.region}:${this.props.account}:job-definition/*`,
                `arn:aws:batch:${this.props.region}:${this.props.account}:job-queue/*`
            ],
            actions: [
                "batch:SubmitJob",
            ]
        }));
        hpcStateMachine.role.addToPrincipalPolicy(new iam.PolicyStatement({
            resources: [
                `arn:aws:events:${this.props.region}:${this.props.account}:rule/*`,
            ],
            actions: [
                "events:PutTargets",
                "events:PutRule",
                "events:DescribeRule"
            ]
        }));
        return hpcStateMachine
    }

    private createAggResultStep(): tasks.LambdaInvoke {
        const aggResultLambda = this.lambdaUtil.createAggResultLambda()
        const aggResultStep = new tasks.LambdaInvoke(this, 'Aggregate Result', {
            lambdaFunction: aggResultLambda,
            payload: sfn.TaskInput.fromObject({
                "execution_id": sfn.JsonPath.stringAt("$.execution_id"),
                "stackName": this.props.stackName,
                "s3_prefix": this.props.prefix
            }),
            resultSelector: {
                "Payload.$": "$.Payload"
            },
            resultPath: '$.aggResultStep'
        });
        return aggResultStep;
    }

    private submitQCTaskStep(): tasks.LambdaInvoke {
        const submitQCTaskStepLambd = this.lambdaUtil.createSubmitQCTaskLambda()
        const submitQCTaskStep = new tasks.LambdaInvoke(this, 'Submit QC Task', {
            lambdaFunction: submitQCTaskStepLambd,
            payload: sfn.TaskInput.fromObject({
                "execution_id": sfn.JsonPath.stringAt("$.execution_id"),
                "task_token": sfn.JsonPath.taskToken,
                "s3_bucket": this.props.bucket.bucketName,
                "s3_prefix": this.props.prefix,
                "ItemValue": sfn.JsonPath.stringAt("$.ItemValue"),
                "ItemIndex": sfn.JsonPath.stringAt("$.ItemIndex")
            }),
            resultPath: '$.submitQCTaskStep',
            integrationPattern: sfn.IntegrationPattern.WAIT_FOR_TASK_TOKEN
        });
        return submitQCTaskStep;
    }

    private createSNSNotifyStep(): tasks.SnsPublish {
        const topic = new sns.Topic(this, 'SNS Topic', {
            displayName: 'QC Stepfunctions Execution Complete Topic',
            masterKey: kms.Alias.fromAliasName(this, 'snsKey', 'alias/aws/sns')
        });
    
        topic.addToResourcePolicy(new iam.PolicyStatement({
            effect: iam.Effect.DENY,
            principals: [new iam.AnyPrincipal()],
            actions: [
                "sns:Publish",
                "sns:Subscribe"
            ],
            resources: [
                topic.topicArn
            ],
            conditions: {
                Bool: {
                    "aws:SecureTransport": "false"
                }
            }
        }))
        const snsStep = new tasks.SnsPublish(this, 'Notify Complete', {
            topic,
            message: sfn.TaskInput.fromObject({
                "execution_id": sfn.JsonPath.stringAt("$.execution_id"),
                "start_time": sfn.JsonPath.stringAt("$.start_time"),
                "end_time": sfn.JsonPath.stringAt("$.aggResultStep.Payload.endTime"),
                "dashboard": this.props.dashboardUrl,
                "status": "Complete"
            }),
            resultPath: '$.snsStep',
        });

        new cdk.CfnOutput(this, 'SNS Topic Name', {
            value: topic.topicName,
            description: "SNS Topic Name",
        });

        return snsStep
    }
}