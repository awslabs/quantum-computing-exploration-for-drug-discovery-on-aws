import * as cdk from '@aws-cdk/core';
import * as ec2 from '@aws-cdk/aws-ec2';
import * as lambda from '@aws-cdk/aws-lambda';
import * as iam from '@aws-cdk/aws-iam'
import * as batch from '@aws-cdk/aws-batch'
import * as ecs from '@aws-cdk/aws-ecs'
import * as sfn from '@aws-cdk/aws-stepfunctions';
import * as tasks from '@aws-cdk/aws-stepfunctions-tasks';
import * as s3 from '@aws-cdk/aws-s3'
import * as sns from '@aws-cdk/aws-sns'


import {
    Construct,
} from '@aws-cdk/core';


import {
    ECRRepoNameEnum,
    ECRImageUtil
} from './utils/utils-images'

import {
    RoleUtil
} from './utils/utils-role'

import {
    LambdaUtil
} from './utils/utils-lambda'


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
}

export class Benchmark extends Construct {

    private batchJobExecutionRole: iam.Role;
    private batchJobRole: iam.Role;
    private props: BatchProps;
    private images: ECRImageUtil
    private roleUtil: RoleUtil
    private lambdaUtil: LambdaUtil

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
        this.batchJobExecutionRole = this.roleUtil.createBatchJobExecutionRole('executionRole');
        this.batchJobRole = this.roleUtil.createBatchJobExecutionRole('jobRole');

        const hpcIstanceTypes = [
            ec2.InstanceType.of(ec2.InstanceClass.C5, ec2.InstanceSize.LARGE), // 2 vcpus, 4G mem
            ec2.InstanceType.of(ec2.InstanceClass.C5, ec2.InstanceSize.XLARGE), // 4 vcpus, 8G mem
            ec2.InstanceType.of(ec2.InstanceClass.C5, ec2.InstanceSize.XLARGE2), // 8 vcpus, 16G mem
            ec2.InstanceType.of(ec2.InstanceClass.C5, ec2.InstanceSize.XLARGE4), // 16 vcpus, 32G mem
        ];
        const vpc = this.props.vpc
        const batchSg = this.props.batchSg

        const batchHPCEnvironment = new batch.ComputeEnvironment(this, 'Batch-HPC-Compute-Env', {
            computeResources: {
                type: batch.ComputeResourceType.ON_DEMAND,
                vpc,
                vpcSubnets: vpc.selectSubnets({
                    subnetType: ec2.SubnetType.PRIVATE_WITH_NAT
                }),
                allocationStrategy: batch.AllocationStrategy.BEST_FIT_PROGRESSIVE,
                instanceTypes: hpcIstanceTypes,
                securityGroups: [batchSg]
            }
        });

        const hpcJobQueue = new batch.JobQueue(this, 'hpcJobQueue', {
            computeEnvironments: [{
                computeEnvironment: batchHPCEnvironment,
                order: 1,
            }, ],
        });

        const taskParamLambda = this.lambdaUtil.createTaskParametersLambda()
        const checkInputParamsStep = new tasks.LambdaInvoke(this, 'Check Input', {
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

        const createModelStep = this.createCreateModelStep(hpcJobQueue);
        const hpcStateMachine = this.createHPCStateMachine(taskParamLambda, hpcJobQueue);
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

        const benchmarkStateMachine = new sfn.StateMachine(this, 'BenchmarkStateMachine', {
            definition: statchMachineChain,
            timeout: cdk.Duration.hours(36)
        });

        // Output //////////////////////////
        new cdk.CfnOutput(this, "stateMachineURL", {
            value: `https://console.aws.amazon.com/states/home?region=${this.props.region}#/statemachines/view/${benchmarkStateMachine.stateMachineArn}`,
            description: "State Machine URL"
        });
    }


    private createHPCBatchJobDef(defName: string,
        vcpus: number, mem: number, bucketName: string, image: ecs.ContainerImage): batch.JobDefinition {
        const resource = this.getResourceDescription(vcpus, mem)
        return new batch.JobDefinition(this, defName, {
            platformCapabilities: [batch.PlatformCapabilities.EC2],
            container: {
                image,
                command: [
                    '--model-param', 'M=1&D=4&A=300&HQ=200',
                    '--aws-region', this.props.region,
                    '--resource', `${resource}`,
                    '--s3-bucket', bucketName
                ],
                executionRole: this.batchJobExecutionRole,
                jobRole: this.batchJobRole,
                vcpus,
                memoryLimitMiB: mem * 1024,
                privileged: false
            },
            timeout: cdk.Duration.hours(2),
            retryAttempts: 1
        });
    }

    private getResourceDescription(vcpus: number, mem: number): string {
        return `vCpus${vcpus}_Mem_${mem}G`;
    }

    private createCreateModelStep(hpcJobQueue: batch.JobQueue): tasks.BatchSubmitJob {
        const createModelEcrImage = this.images.getECRImage(ECRRepoNameEnum.Batch_Create_Model) as ecs.ContainerImage

        const createModelJobDef = new batch.JobDefinition(this, 'createModelJobDefinition', {
            platformCapabilities: [batch.PlatformCapabilities.EC2],
            container: {
                image: createModelEcrImage,
                command: [
                    '--aws-region', this.props.region,
                    '--s3-bucket', this.props.bucket.bucketName,
                ],
                executionRole: this.batchJobExecutionRole,
                jobRole: this.batchJobRole,
                vcpus: 2,
                memoryLimitMiB: 2 * 1024,
                privileged: false
            },
            timeout: cdk.Duration.minutes(10),
            retryAttempts: 1
        });

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

        const hpcAndQCStateMachine = new sfn.StateMachine(this, 'RunHPCAndQCStateMachine', {
            definition: hpcAndQCParallel,
        });
        return hpcAndQCStateMachine;
    }

    private createQCStateMachine(
        parametersLambda: lambda.Function
    ): sfn.StateMachine {

        const getDeviceListLambdaStep = new tasks.LambdaInvoke(this, 'Get Device List', {
            lambdaFunction: parametersLambda,
            payload: sfn.TaskInput.fromObject({
                "s3_bucket": this.props.bucket.bucketName,
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
        const qcStateMachine = new sfn.StateMachine(this, 'QCStateMachine', {
            definition: getDeviceListLambdaStep.next(parallelQCDeviceMap),
            timeout: cdk.Duration.hours(36)
        });
        return qcStateMachine;
    }

    private createRunOnQCDeviceStateMachine(
        parametersLambda: lambda.Function
    ): sfn.StateMachine {

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

        const qcStateMachine = new sfn.StateMachine(this, 'QCDeviceStateMachine', {
            definition: chain,
        });
        return qcStateMachine;
    }

    private createHPCStateMachine(parametersLambda: lambda.Function, hpcJobQueue: batch.JobQueue): sfn.StateMachine {
        const hpcEcrImage = this.images.getECRImage(ECRRepoNameEnum.Batch_Sa_Optimizer) as ecs.ContainerImage
        const parametersLambdaStep = new tasks.LambdaInvoke(this, 'Get Task Parameters', {
            lambdaFunction: parametersLambda,
            payload: sfn.TaskInput.fromObject({
                "s3_bucket": this.props.bucket.bucketName,
                "param_type": "PARAMS_FOR_HPC",
                "execution_id": sfn.JsonPath.stringAt("$.execution_id"),
                "context.$": "$$"
            }),
            outputPath: '$.Payload'
        });

        const jobDef = this.createHPCBatchJobDef("HPCJob_Template",
            2, 2, this.props.bucket.bucketName, hpcEcrImage
        );
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

        const hpcStateMachine = new sfn.StateMachine(this, 'HPCStateMachine', {
            definition: chain,

        });
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
                "execution_id": sfn.JsonPath.stringAt("$.execution_id")
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
        });
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
            description: "SNS Topic Name"
        });

        return snsStep
    }
}