import * as path from 'path';
import * as cdk from '@aws-cdk/core';
import * as ec2 from '@aws-cdk/aws-ec2';
import * as lambda from '@aws-cdk/aws-lambda';
import * as iam from '@aws-cdk/aws-iam'
import * as batch from '@aws-cdk/aws-batch'
import * as ecs from '@aws-cdk/aws-ecs'
import * as sfn from '@aws-cdk/aws-stepfunctions';
import * as tasks from '@aws-cdk/aws-stepfunctions-tasks';
import * as s3 from '@aws-cdk/aws-s3'
import * as logs from '@aws-cdk/aws-logs'
import * as kms from '@aws-cdk/aws-kms'
import * as ecr from '@aws-cdk/aws-ecr'
import * as sns from '@aws-cdk/aws-sns'

const s3n = require('@aws-cdk/aws-s3-notifications')

enum ECRRepoNameEnum {
    Batch_Create_Model,
    Batch_Sa_Optimizer,
    Lambda_CheckDevice,
    Lambda_SubmitQCTask
};

import {
    Aspects,
    Construct,
} from '@aws-cdk/core';

import {
    ChangePublicSubnet,
    grantKmsKeyPerm
} from './utils'


export interface BatchProps {
    region: string;
    account: string;
    bucket: s3.Bucket;
}

export class MolUnfBatch extends Construct {

    private batchJobExecutionRole: iam.Role;
    private batchJobRole: iam.Role;
    private props: BatchProps;

    private createBatchJobExecutionRole(roleName: string): iam.Role {
        const role = new iam.Role(this, roleName, {
            assumedBy: new iam.ServicePrincipal('ecs-tasks.amazonaws.com'),
        });

        role.addManagedPolicy(iam.ManagedPolicy.fromAwsManagedPolicyName('AmazonBraketFullAccess'))
        role.addManagedPolicy(iam.ManagedPolicy.fromAwsManagedPolicyName('AmazonEC2ContainerRegistryReadOnly'))

        role.addToPolicy(new iam.PolicyStatement({
            resources: [
                "arn:aws:s3:::*/*"
            ],
            actions: [
                "s3:GetObject",
                "s3:PutObject"
            ]
        }));

        role.addToPolicy(new iam.PolicyStatement({
            resources: [
                'arn:aws:s3:::*'
            ],
            actions: [
                "s3:ListBucket"
            ]
        }));

        role.addToPolicy(new iam.PolicyStatement({
            resources: [
                `arn:aws:logs:*:${this.props.account}:log-group:/aws/batch/*`
            ],
            actions: [
                "logs:CreateLogStream",
                "logs:DescribeLogStreams",
                "logs:PutLogEvents",
                "logs:CreateLogGroup"
            ]
        }));
        role.addToPolicy(new iam.PolicyStatement({
            resources: [
                'arn:aws:braket:::device/qpu/d-wave/*',
            ],
            actions: [
                "braket:GetDevice",
                "braket:GetQuantumTask",
                "braket:SearchQuantumTasks",
                "braket:SearchDevices",
                "braket:ListTagsForResource",
                "braket:CreateQuantumTask",
                "braket:CancelQuantumTask"
            ]
        }));
        return role
    }

    private createAggResultLambdaRole(): iam.Role {
        const role = new iam.Role(this, 'AggResultLambdaRole', {
            assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
        });
        role.addManagedPolicy(iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'))
        role.addManagedPolicy(iam.ManagedPolicy.fromAwsManagedPolicyName('AmazonAthenaFullAccess'))
        role.addToPolicy(new iam.PolicyStatement({
            resources: [
                "arn:aws:s3:::*/*"
            ],
            actions: [
                "s3:GetObject",
                "s3:PutObject"
            ]
        }));

        role.addToPolicy(new iam.PolicyStatement({
            resources: [
                'arn:aws:s3:::*'
            ],
            actions: [
                "s3:ListBucket"
            ]
        }));

        role.addToPolicy(new iam.PolicyStatement({
            effect: iam.Effect.ALLOW,
            resources: [
                '*'
            ],
            actions: [
                "ec2:AttachNetworkInterface",
                "ec2:CreateNetworkInterface",
                "ec2:CreateNetworkInterfacePermission",
                "ec2:DeleteNetworkInterface",
                "ec2:DeleteNetworkInterfacePermission",
                "ec2:DescribeDhcpOptions",
                "ec2:DescribeNetworkInterfaces",
                "ec2:DescribeNetworkInterfacePermissions",
                "ec2:DescribeSubnets",
                "ec2:DescribeVpcs",
                "ec2:DescribeInstances"
            ]
        }));
        role.addToPolicy(new iam.PolicyStatement({
            resources: [
                `arn:aws:logs:*:${this.props.account}:log-group:*`
            ],
            actions: [
                "logs:CreateLogStream",
                "logs:DescribeLogStreams",
                "logs:PutLogEvents",
                "logs:CreateLogGroup"
            ]
        }));
        return role;
    }

    private createBraketLambdaRole(roleName: string): iam.Role {
        const role = new iam.Role(this, roleName, {
            assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
        });
        role.addManagedPolicy(iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'))
        role.addManagedPolicy(iam.ManagedPolicy.fromAwsManagedPolicyName('AmazonBraketFullAccess'))

        role.addToPolicy(new iam.PolicyStatement({
            resources: [
                `arn:aws:logs:*:${this.props.account}:log-group:*`
            ],
            actions: [
                "logs:CreateLogStream",
                "logs:DescribeLogStreams",
                "logs:PutLogEvents",
                "logs:CreateLogGroup"
            ]
        }));

        role.addToPolicy(new iam.PolicyStatement({
            effect: iam.Effect.ALLOW,
            resources: [
                '*'
            ],
            actions: [
                "ec2:AttachNetworkInterface",
                "ec2:CreateNetworkInterface",
                "ec2:CreateNetworkInterfacePermission",
                "ec2:DeleteNetworkInterface",
                "ec2:DeleteNetworkInterfacePermission",
                "ec2:DescribeDhcpOptions",
                "ec2:DescribeNetworkInterfaces",
                "ec2:DescribeNetworkInterfacePermissions",
                "ec2:DescribeSubnets",
                "ec2:DescribeVpcs",
                "ec2:DescribeInstances"
            ]
        }));

        role.addToPolicy(new iam.PolicyStatement({
            actions: [
                "states:ListStateMachines",
                "states:CreateStateMachine",
                "states:DescribeStateMachine",
                "states:StartExecution",
                "states:DeleteStateMachine",
                "states:ListExecutions",
                "states:UpdateStateMachine",
                "states:DescribeStateMachineForExecution",
                "states:GetExecutionHistory",
                "states:StopExecution",
                "states:SendTaskSuccess",
                "states:SendTaskFailure",
                "states:SendTaskHeartbeat"
            ],
            resources: [
                "arn:aws:states:*:*:*"
            ]
        }));

        return role;
    }

    private createGenericLambdaRole(roleName: string): iam.Role {
        const role = new iam.Role(this, roleName, {
            assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
        });
        role.addManagedPolicy(iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'))
        role.addManagedPolicy(iam.ManagedPolicy.fromAwsManagedPolicyName('AmazonAthenaFullAccess'))
        role.addToPolicy(new iam.PolicyStatement({
            resources: [
                "arn:aws:s3:::*/*"
            ],
            actions: [
                "s3:GetObject",
                "s3:PutObject"
            ]
        }));

        role.addToPolicy(new iam.PolicyStatement({
            resources: [
                'arn:aws:s3:::*'
            ],
            actions: [
                "s3:ListBucket"
            ]
        }));

        role.addToPolicy(new iam.PolicyStatement({
            effect: iam.Effect.ALLOW,
            resources: [
                '*'
            ],
            actions: [
                "ec2:AttachNetworkInterface",
                "ec2:CreateNetworkInterface",
                "ec2:CreateNetworkInterfacePermission",
                "ec2:DeleteNetworkInterface",
                "ec2:DeleteNetworkInterfacePermission",
                "ec2:DescribeDhcpOptions",
                "ec2:DescribeNetworkInterfaces",
                "ec2:DescribeNetworkInterfacePermissions",
                "ec2:DescribeSubnets",
                "ec2:DescribeVpcs",
                "ec2:DescribeInstances"
            ]
        }));
        role.addToPolicy(new iam.PolicyStatement({
            resources: [
                `arn:aws:logs:*:${this.props.account}:log-group:*`
            ],
            actions: [
                "logs:CreateLogStream",
                "logs:DescribeLogStreams",
                "logs:PutLogEvents",
                "logs:CreateLogGroup"
            ]
        }));

        role.addToPolicy(new iam.PolicyStatement({
            actions: [
                "states:ListStateMachines",
                "states:CreateStateMachine",
                "states:DescribeStateMachine",
                "states:StartExecution",
                "states:DeleteStateMachine",
                "states:ListExecutions",
                "states:UpdateStateMachine",
                "states:DescribeStateMachineForExecution",
                "states:GetExecutionHistory",
                "states:StopExecution",
                "states:SendTaskSuccess",
                "states:SendTaskFailure",
                "states:SendTaskHeartbeat"
            ],
            resources: [
                "arn:aws:states:*:*:*"
            ]
        }));
        role.addToPolicy(new iam.PolicyStatement({
            actions: [
                "iam:PassRole"
            ],
            resources: [
                "arn:aws:iam:::role/*"
            ]
        }));
        return role;
    }

    // constructor 
    constructor(scope: Construct, id: string, props: BatchProps) {
        super(scope, id);
        this.props = props;

        this.batchJobExecutionRole = this.createBatchJobExecutionRole('executionRole');
        this.batchJobRole = this.createBatchJobExecutionRole('jobRole');

        const hpcIstanceTypes = [
            ec2.InstanceType.of(ec2.InstanceClass.C5, ec2.InstanceSize.LARGE), // 2 vcpus, 4G mem
            ec2.InstanceType.of(ec2.InstanceClass.C5, ec2.InstanceSize.XLARGE), // 4 vcpus, 8G mem
            ec2.InstanceType.of(ec2.InstanceClass.C5, ec2.InstanceSize.XLARGE2), // 8 vcpus, 16G mem
            ec2.InstanceType.of(ec2.InstanceClass.C5, ec2.InstanceSize.XLARGE4), // 16 vcpus, 32G mem
        ];

        const vpc = new ec2.Vpc(this, 'VPC', {
            cidr: '10.1.0.0/16',
            subnetConfiguration: [{
                    cidrMask: 18,
                    name: 'Ingress',
                    subnetType: ec2.SubnetType.PUBLIC
                },
                {
                    cidrMask: 18,
                    name: 'Application',
                    subnetType: ec2.SubnetType.PRIVATE_WITH_NAT
                }
            ]
        });

        vpc.publicSubnets.forEach(s => {
            Aspects.of(s).add(new ChangePublicSubnet())
        });

        const logKey = new kms.Key(this, 'qcLogKey', {
            enableKeyRotation: true
        });
        grantKmsKeyPerm(logKey);

        const vpcFlowlog = new logs.LogGroup(this, "vpcFlowlog", {
            encryptionKey: logKey
        });

        vpc.addFlowLog("logtoCW", {
            destination: ec2.FlowLogDestination.toCloudWatchLogs(vpcFlowlog),
            trafficType: ec2.FlowLogTrafficType.ALL
        });

        const batchSg = new ec2.SecurityGroup(this, "batchSg", {
            vpc,
            allowAllOutbound: true,
            description: "Security Group for QC batch compute environment"
        });

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

        const lambdaSg = new ec2.SecurityGroup(this, "lambdaSg", {
            vpc,
            allowAllOutbound: true,
            description: "Security Group for lambda"
        });

        const lambdaRole = this.createGenericLambdaRole('TaskParametersLambdaRole');

        const taskParamLambda = new lambda.Function(this, 'TaskParametersLambda', {
            runtime: lambda.Runtime.PYTHON_3_8,
            code: lambda.Code.fromAsset(path.join(__dirname, '../lambda/TaskParametersLambda/')),
            handler: 'app.handler',
            memorySize: 512,
            timeout: cdk.Duration.seconds(60),
            vpc,
            vpcSubnets: vpc.selectSubnets({
                subnetType: ec2.SubnetType.PRIVATE_WITH_NAT
            }),
            role: lambdaRole,
            reservedConcurrentExecutions: 10,
            securityGroups: [lambdaSg]
        })

        const checkInputParamsStep = new tasks.LambdaInvoke(this, 'Check Input', {
            lambdaFunction: taskParamLambda,
            payload: sfn.TaskInput.fromObject({
                "s3_bucket": this.props.bucket.bucketName,
                "param_type": "CHECK_INPUT",
                "user_input.$": "$",
                "execution_id.$": "$$.Execution.Id"
            }),
            outputPath: '$.Payload'
        });

        const createModelStep = this.createCreateModelStep(hpcJobQueue);
        const hpcStateMachine = this.createHPCStateMachine(taskParamLambda, hpcJobQueue);
        const qcStateMachine = this.createQCStateMachine(vpc, lambdaSg, taskParamLambda)
        const qcAndHPCStateMachine = this.createHPCAndQCStateMachine(hpcStateMachine, qcStateMachine)

        const aggResultStep = this.createAggResultStep(vpc, lambdaSg);
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

        this.createEventListener(vpc, lambdaSg)

        new cdk.CfnOutput(this, "stateMachineName", {
            value: benchmarkStateMachine.stateMachineName,
            description: "State Machine Name"
        });

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
        const createModelEcrImage = this.getECRImage(ECRRepoNameEnum.Batch_Create_Model) as ecs.ContainerImage

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
        vpc: ec2.Vpc,
        lambdaSg: ec2.SecurityGroup,
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

        const runOnQCDeviceStateMachine = this.createRunOnQCDeviceStateMachine(vpc, lambdaSg, parametersLambda)

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
        vpc: ec2.Vpc,
        lambdaSg: ec2.SecurityGroup,
        parametersLambda: lambda.Function
    ): sfn.StateMachine {

        const checkLambdaRole = this.createBraketLambdaRole('DeviceAvailableCheckLambdaRole');
        const code = this.getECRImage(ECRRepoNameEnum.Lambda_CheckDevice) as lambda.DockerImageCode
        const checkQCDeviceLambda = new lambda.DockerImageFunction(this, 'DeviceAvailableCheckLambda', {
            code,
            memorySize: 512,
            timeout: cdk.Duration.seconds(60),
            vpc,
            vpcSubnets: vpc.selectSubnets({
                subnetType: ec2.SubnetType.PRIVATE_WITH_NAT
            }),
            role: checkLambdaRole,
            reservedConcurrentExecutions: 10,
            securityGroups: [lambdaSg]
        })

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

        const submitQCTaskStep = this.submitQCTaskStep(vpc, lambdaSg);

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
        const hpcEcrImage = this.getECRImage(ECRRepoNameEnum.Batch_Sa_Optimizer) as ecs.ContainerImage
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

    private createAggResultStep(vpc: ec2.Vpc, lambdaSg: ec2.SecurityGroup): tasks.LambdaInvoke {
        const aggLambdaRole = this.createAggResultLambdaRole();
        const aggResultLambda = new lambda.Function(this, 'AggResultLambda', {
            runtime: lambda.Runtime.NODEJS_12_X,
            code: lambda.Code.fromAsset(path.join(__dirname, '../lambda/AthenaTabeLambda/')),
            handler: 'index.handler',
            memorySize: 512,
            timeout: cdk.Duration.seconds(120),
            environment: {
                BUCKET: this.props.bucket.bucketName
            },
            vpc,
            vpcSubnets: vpc.selectSubnets({
                subnetType: ec2.SubnetType.PRIVATE_WITH_NAT
            }),
            role: aggLambdaRole,
            reservedConcurrentExecutions: 10,
            securityGroups: [lambdaSg]
        });

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

    private createEventListener(vpc: ec2.Vpc, lambdaSg: ec2.SecurityGroup) {
        const lambdaRole = this.createGenericLambdaRole("ParseBraketResultLambdaRole")
        const parseBraketResultLambda = new lambda.Function(this, 'ParseBraketResultLambda', {
            runtime: lambda.Runtime.PYTHON_3_8,
            code: lambda.Code.fromAsset(path.join(__dirname, '../lambda/ParseBraketResultLambda/')),
            handler: 'app.handler',
            memorySize: 512,
            timeout: cdk.Duration.seconds(60),
            vpc,
            vpcSubnets: vpc.selectSubnets({
                subnetType: ec2.SubnetType.PRIVATE_WITH_NAT
            }),
            role: lambdaRole,
            reservedConcurrentExecutions: 20,
            securityGroups: [lambdaSg]
        });

        this.props.bucket.addEventNotification(s3.EventType.OBJECT_CREATED,
            new s3n.LambdaDestination(parseBraketResultLambda), {
                prefix: 'molecule-unfolding/qc_task_output/',
                suffix: 'results.json'
            });
    }

    private submitQCTaskStep(vpc: ec2.Vpc, lambdaSg: ec2.SecurityGroup): tasks.LambdaInvoke {
        const lambdaRole = this.createBraketLambdaRole('SubmitQCTaskLambdaRole')
        const code = this.getECRImage(ECRRepoNameEnum.Lambda_SubmitQCTask) as lambda.DockerImageCode
        const submitQCTaskStepLambd = new lambda.DockerImageFunction(this, 'SubmitQCTaskLambda', {
            code,
            memorySize: 512,
            timeout: cdk.Duration.seconds(120),
            vpc,
            vpcSubnets: vpc.selectSubnets({
                subnetType: ec2.SubnetType.PRIVATE_WITH_NAT
            }),
            role: lambdaRole,
            reservedConcurrentExecutions: 20,
            securityGroups: [lambdaSg]
        });

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
                "end_time":  sfn.JsonPath.stringAt("$.aggResultStep.Payload.endTime"),
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


    private getECRImage(name: ECRRepoNameEnum, usePreBuildImage = false): ecs.ContainerImage | lambda.DockerImageCode {

        if (name == ECRRepoNameEnum.Batch_Create_Model) {
            if (usePreBuildImage) {
                return ecs.ContainerImage.fromEcrRepository(
                    ecr.Repository.fromRepositoryName(this, 'create-model', 'molecule-unfolding/create-model')
                );
            }
            return ecs.ContainerImage.fromAsset(
                path.join(__dirname, '../batch-images/create-model'))
        }

        if (name == ECRRepoNameEnum.Batch_Sa_Optimizer) {
            if (usePreBuildImage) {
                return ecs.ContainerImage.fromEcrRepository(
                    ecr.Repository.fromRepositoryName(this, 'sa-optimizer', 'molecule-unfolding/sa-optimizer')
                );
            }

            return ecs.ContainerImage.fromAsset(
                path.join(__dirname, '../batch-images/sa-optimizer'))
        }
        if (name == ECRRepoNameEnum.Lambda_CheckDevice) {
            if (usePreBuildImage) {
                return lambda.DockerImageCode.fromEcr(
                    ecr.Repository.fromRepositoryName(this, 'lambda-device-available-check', 'molecule-unfolding/lambda-device-available-check')
                );
            }
            return lambda.DockerImageCode.fromImageAsset(path.join(__dirname, '../lambda/DeviceAvailableCheckLambda/'));
        }

        if (name == ECRRepoNameEnum.Lambda_SubmitQCTask) {
            if (usePreBuildImage) {
                return lambda.DockerImageCode.fromEcr(
                    ecr.Repository.fromRepositoryName(this, 'lambda-submit-qc-task', 'molecule-unfolding/lambda-submit-qc-task')
                );
            }
            return lambda.DockerImageCode.fromImageAsset(path.join(__dirname, '../lambda/SubmitQCTaskLambda/'));
        }

        throw new Error("Cannot find ecr: " + name);
    }
}