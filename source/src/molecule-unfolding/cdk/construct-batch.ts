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

enum ECRRepoNameEnum { Create_Model, Sa_Optimizer, Qa_Optimizer };

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

    private createDeviceAvailableCheckLambdaRole(): iam.Role {
        const role = new iam.Role(this, 'DeviceAvailableCheckLambdaRole', {
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

        // const logGroupName = `${cdk.Stack.of(logKey).stackName}-vpcFlowlogGroup`;
        // grantKmsKeyPerm(logKey,logGroupName);
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

        const batchQCEnvironment = new batch.ComputeEnvironment(this, 'Batch-QC-Compute-Env', {
            computeResources: {
                type: batch.ComputeResourceType.FARGATE,
                vpc,
                vpcSubnets: vpc.selectSubnets({
                    subnetType: ec2.SubnetType.PRIVATE_WITH_NAT
                }),
                securityGroups: [batchSg]
            }
        });

        const hpcJobQueue = new batch.JobQueue(this, 'hpcJobQueue', {
            computeEnvironments: [{
                computeEnvironment: batchHPCEnvironment,
                order: 1,
            }, ],
        });

        const qcJobQueue = new batch.JobQueue(this, 'qcJobQueue', {
            computeEnvironments: [{
                computeEnvironment: batchQCEnvironment,
                order: 1,
            }, ],
        });

        const lambdaSg = new ec2.SecurityGroup(this, "lambdaSg", {
            vpc,
            allowAllOutbound: true,
            description: "Security Group for lambda"
        });

        const mValues = [1, 2, 3, 4];
        const createModelStep = this.createCreateModelStep(hpcJobQueue);
        const qcAndHPCbatchParallel = new sfn.Parallel(this, "QCAndHPCParallel");
        const hpcStateMachine = this.createHPCStateMachine(mValues, hpcJobQueue);
        const hpcExecutionStep = new tasks.StepFunctionsStartExecution(this, 'RunHPC', {
            stateMachine: hpcStateMachine,
            integrationPattern: sfn.IntegrationPattern.RUN_JOB
        });

        const qcStateMachine = this.createQCStateMachine(vpc, lambdaSg, mValues, qcJobQueue)
        const qcExecutionStep = new tasks.StepFunctionsStartExecution(this, 'RunQC', {
            stateMachine: qcStateMachine,
            integrationPattern: sfn.IntegrationPattern.RUN_JOB
        });

        const aggResultStep = this.createAggResultStep(vpc, lambdaSg);
        const success = new sfn.Succeed(this, 'Succeed');

        const qcAndHpcStateMachine = new sfn.StateMachine(this, 'QCAndHpcStateMachine', {
            definition: createModelStep.next(
                    qcAndHPCbatchParallel
                    .branch(hpcExecutionStep)
                    .branch(qcExecutionStep))
                .next(aggResultStep)
                .next(success),
            timeout: cdk.Duration.hours(36)
        });

        new cdk.CfnOutput(this, "stateMachine", {
            value: qcAndHpcStateMachine.stateMachineName,
            description: "State Machine Name"
        });

        new cdk.CfnOutput(this, "stateMachineURL", {
            value: `https://console.aws.amazon.com/states/home?region=${this.props.region}#/statemachines/view/${qcAndHpcStateMachine.stateMachineArn}`,
            description: "State Machine URL"
        });
    }


    private createHPCBatchJobDef(defName: string, m: number,
        vcpus: number, mem: number, bucketName: string, image: ecs.ContainerImage): batch.JobDefinition {
        const resource = this.getResourceDescription(vcpus, mem)
        return new batch.JobDefinition(this, defName, {
            platformCapabilities: [batch.PlatformCapabilities.EC2],
            container: {
                image,
                command: [
                    '--M', `${m}`,
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
        const createModelEcrImage = this.getECRImage(ECRRepoNameEnum.Create_Model)

        const createModelJobDef = new batch.JobDefinition(this, 'createModelJobDefinition', {
            platformCapabilities: [batch.PlatformCapabilities.EC2],
            container: {
                image: createModelEcrImage,
                command: [
                    '--aws-region', this.props.region,
                    '--s3-bucket', this.props.bucket.bucketName,
                    '--force-update', '0'
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
            integrationPattern: sfn.IntegrationPattern.RUN_JOB

        });
        return createModelStep;
    }

    private createQCStateMachine(
        vpc: ec2.Vpc,
        lambdaSg: ec2.SecurityGroup,
        mValues: number[],
        qcJobQueue: batch.JobQueue): sfn.StateMachine {

        const qcEcrImage = this.getECRImage(ECRRepoNameEnum.Qa_Optimizer)

        const deviceArns = [
            'arn:aws:braket:::device/qpu/d-wave/DW_2000Q_6',
            'arn:aws:braket:::device/qpu/d-wave/Advantage_system4'
        ];

        const qcJobDef = new batch.JobDefinition(this, 'qcJobDef', {
            platformCapabilities: [batch.PlatformCapabilities.FARGATE],
            container: {
                image: qcEcrImage,
                command: [
                    '--aws-region', this.props.region,
                    '--s3-bucket', this.props.bucket.bucketName,
                    '--device-arn', deviceArns[0],
                    '--M', '1',
                ],

                executionRole: this.batchJobExecutionRole,
                jobRole: this.batchJobRole,
                vcpus: 1,
                memoryLimitMiB: 2 * 1024,
                privileged: false
            },
            timeout: cdk.Duration.minutes(20),
            retryAttempts: 1
        });
        const qcTaskListMap: Map < string, tasks.BatchSubmitJob[] > = new Map();
        for (let m of mValues) {
            // QC
            for (let i = 0; i < deviceArns.length; i++) {
                const deviceName = deviceArns[i].split("/").pop()
                const jobName = `QC-M${m}-${deviceName}`.replace(".", "_");
                const qcBatchTask = new tasks.BatchSubmitJob(this, `${jobName}`, {
                    jobDefinitionArn: qcJobDef.jobDefinitionArn,
                    jobName,
                    jobQueueArn: qcJobQueue.jobQueueArn,
                    containerOverrides: {
                        command: [
                            '--M', `${m}`,
                            '--aws-region', this.props.region,
                            '--device-arn', deviceArns[i],
                            '--s3-bucket', this.props.bucket.bucketName
                        ],
                    },
                    integrationPattern: sfn.IntegrationPattern.RUN_JOB
                });

                if (qcTaskListMap.get(deviceArns[i])) {
                    qcTaskListMap.get(deviceArns[i])?.push(qcBatchTask)
                } else {
                    qcTaskListMap.set(deviceArns[i], [qcBatchTask])
                }
            }
        }

        const checkLambdaRole = this.createDeviceAvailableCheckLambdaRole();
        const checkQCDeviceLambda = new lambda.Function(this, 'DeviceAvailableCheckLambda', {
            runtime: lambda.Runtime.PYTHON_3_8,
            code: lambda.Code.fromAsset(path.join(__dirname, '../lambda/DeviceAvailableCheckLambda/')),
            handler: 'handler.handler',
            memorySize: 512,
            timeout: cdk.Duration.seconds(60),
            vpc,
            vpcSubnets: vpc.selectSubnets({
                subnetType: ec2.SubnetType.PRIVATE_WITH_NAT
            }),
            role: checkLambdaRole,
            reservedConcurrentExecutions: 10,
            securityGroups: [lambdaSg]
        });

        const qcBatchParallel = new sfn.Parallel(this, "qcBatchParallel");
        for (let deviceArn of qcTaskListMap.keys()) {
            const deviceName = deviceArn.split("/").pop()
            const qcDeviceParallel = new sfn.Parallel(this, `qcDeviceParallel-${deviceName}`);
            const checkLambdaStep = new tasks.LambdaInvoke(this, `Check Device [${deviceName}] Status`, {
                lambdaFunction: checkQCDeviceLambda,
                payload: sfn.TaskInput.fromObject({
                    deviceArn: deviceArn
                }),
                outputPath: '$.Payload'
            });

            qcTaskListMap.get(deviceArn)?.forEach(j => {
                qcDeviceParallel.branch(j)
            });

            qcBatchParallel.branch(
                checkLambdaStep.next(
                    new sfn.Choice(this, `Device [${deviceName}] Available?`)
                    .when(sfn.Condition.stringEquals('$.deviceStatus', 'ONLINE'), qcDeviceParallel)
                    .otherwise(
                        new sfn.Wait(this, `Wait 10 Minutes [${deviceName}]`, {
                            time: sfn.WaitTime.duration(cdk.Duration.minutes(10))
                        }).next(checkLambdaStep))
                ));
        }

        const qcStateMachine = new sfn.StateMachine(this, 'QCStateMachine', {
            definition: qcBatchParallel,
            timeout: cdk.Duration.hours(36)
        });
        return qcStateMachine;
    }

    private createHPCStateMachine(mValues: number[], hpcJobQueue: batch.JobQueue): sfn.StateMachine {

        const hpcEcrImage = this.getECRImage(ECRRepoNameEnum.Sa_Optimizer)
        const hpcTaskList = [];
        const vcpuMemList = [
            [2, 2],
            [4, 4],
            [8, 8],
            [16, 16]
        ];
        const hpcJobDefs = vcpuMemList.map(it => {
            return this.createHPCBatchJobDef(`HPCJob_vCpus${it[0]}_Mem${it[1]}G`,
                1,
                it[0], it[1],
                this.props.bucket.bucketName,
                hpcEcrImage
            );
        });

        for (let m of mValues) {
            // HPC
            for (let i = 0; i < vcpuMemList.length; i++) {
                const [vcpu, mem] = vcpuMemList[i];
                const jobDef = hpcJobDefs[i];
                const resource = this.getResourceDescription(vcpu, mem)
                const jobName = `HPC-M${m}-${resource}`.replace(".", "_");

                const hpcBatchTask = new tasks.BatchSubmitJob(this, `${jobName}`, {
                    jobDefinitionArn: jobDef.jobDefinitionArn,
                    jobName,
                    jobQueueArn: hpcJobQueue.jobQueueArn,
                    containerOverrides: {
                        command: [
                            '--M', `${m}`,
                            '--aws-region', this.props.region,
                            '--resource', resource,
                            '--s3-bucket', this.props.bucket.bucketName
                        ],
                    },
                    integrationPattern: sfn.IntegrationPattern.RUN_JOB

                });
                hpcTaskList.push(hpcBatchTask);
            }
        }

        const hpcBatchParallel = new sfn.Parallel(this, "HPCParallel");

        for (const task of hpcTaskList) {
            hpcBatchParallel.branch(task)
        }

        const hpcStateMachine = new sfn.StateMachine(this, 'HPCStateMachine', {
            definition: hpcBatchParallel,
            timeout: cdk.Duration.hours(3)
        });

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
            outputPath: '$.Payload'
        });
        return aggResultStep;
    }

    private getECRImage(name: ECRRepoNameEnum , usePreBuildImage = false): ecs.ContainerImage {

        if (name == ECRRepoNameEnum.Create_Model) {
            if (usePreBuildImage) {
                return ecs.ContainerImage.fromEcrRepository(
                    ecr.Repository.fromRepositoryName(this, 'ecrRepo', 'molecule-unfolding/create-model')
                );
            }
            return ecs.ContainerImage.fromAsset(
                path.join(__dirname, '../docker-images/create-model'))
        }

        if (name == ECRRepoNameEnum.Sa_Optimizer) {
            if (usePreBuildImage) {
                return ecs.ContainerImage.fromEcrRepository(
                    ecr.Repository.fromRepositoryName(this, 'ecrRepo', 'molecule-unfolding/sa-optimizer')
                );
            }

            return ecs.ContainerImage.fromAsset(
                path.join(__dirname, '../docker-images/sa-optimizer'))
        }

        if (name == ECRRepoNameEnum.Qa_Optimizer) {
            if (usePreBuildImage) {
                return ecs.ContainerImage.fromEcrRepository(
                    ecr.Repository.fromRepositoryName(this, 'ecrRepo', 'molecule-unfolding/qa-optimizer')
                );
            }

            return ecs.ContainerImage.fromAsset(
                path.join(__dirname, '../docker-images/qa-optimizer'))
        }
        throw new Error("Cannot find ecr: " + name);
    }
}