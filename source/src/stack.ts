import * as path from 'path';
import * as cdk from '@aws-cdk/core';
import * as ec2 from '@aws-cdk/aws-ec2';
import * as lambda from '@aws-cdk/aws-lambda';
import * as s3 from '@aws-cdk/aws-s3';
import * as iam from '@aws-cdk/aws-iam'
import * as batch from '@aws-cdk/aws-batch'
import * as ecs from '@aws-cdk/aws-ecs'
import * as sfn from '@aws-cdk/aws-stepfunctions';
import * as tasks from '@aws-cdk/aws-stepfunctions-tasks';
import {
  CfnNotebookInstanceLifecycleConfig,
  CfnNotebookInstance
} from '@aws-cdk/aws-sagemaker';

import {
  Construct,
  Stack,
  StackProps,
  CfnMapping,
  CfnParameter,
  CfnParameterProps,
  Aws
} from '@aws-cdk/core';

import {
  readFileSync
} from 'fs';



export class SolutionStack extends Stack {
  private _paramGroup: {
    [grpname: string]: CfnParameter[]
  } = {}

  protected setDescription(description: string) {
    this.templateOptions.description = description;
  }
  protected newParam(id: string, props ? : CfnParameterProps): CfnParameter {
    return new CfnParameter(this, id, props);
  }
  protected addGroupParam(props: {
    [key: string]: CfnParameter[]
  }): void {
    for (const key of Object.keys(props)) {
      const params = props[key];
      this._paramGroup[key] = params.concat(this._paramGroup[key] ? this._paramGroup[key] : []);
    }
    this._setParamGroups();
  }
  private _setParamGroups(): void {
    if (!this.templateOptions.metadata) {
      this.templateOptions.metadata = {};
    }
    const mkgrp = (label: string, params: CfnParameter[]) => {
      return {
        Label: {
          default: label
        },
        Parameters: params.map(p => {
          return p ? p.logicalId : '';
        }).filter(id => id),
      };
    };
    this.templateOptions.metadata['AWS::CloudFormation::Interface'] = {
      ParameterGroups: Object.keys(this._paramGroup).map(key => mkgrp(key, this._paramGroup[key])),
    };
  }
}

class MyImage implements ec2.IMachineImage {
  private mapping: {
    [k1: string]: {
      [k2: string]: any
    }
  } = {};
  constructor(readonly amiMap: {
    [region: string]: string
  }) {
    for (const [region, ami] of Object.entries(amiMap)) {
      this.mapping[region] = {
        ami
      };
    }
  }
  public getImage(parent: Construct): ec2.MachineImageConfig {
    const amiMap = new CfnMapping(parent, 'AmiMap', {
      mapping: this.mapping
    });
    return {
      imageId: amiMap.findInMap(Aws.REGION, 'ami'),
      userData: ec2.UserData.forLinux(),
      osType: ec2.OperatingSystemType.LINUX,
    };
  }
}

export class MyStack extends SolutionStack {
  constructor(scope: Construct, id: string, props: StackProps = {}) {
    super(scope, id, props);

    const vpc = new ec2.Vpc(this, 'VPC');

    new ec2.Instance(this, 'Instance', {
      vpc,
      instanceType: new ec2.InstanceType('t2.micro'),
      machineImage: new MyImage({
        'cn-north-1': 'ami-cn-north-1',
        'cn-northwest-1': 'ami-cn-northwest-1',
      }),
    });

    const layer = new lambda.LayerVersion(this, 'MyLayer', {
      code: lambda.Code.fromAsset(path.join(__dirname, '../lambda/'), {
        bundling: {
          image: lambda.Runtime.NODEJS_12_X.bundlingImage,
          command: [
            'bash', '-xc', [
              'export npm_config_update_notifier=false',
              'export npm_config_cache=$(mktemp -d)', // https://github.com/aws/aws-cdk/issues/8707#issuecomment-757435414
              'cd $(mktemp -d)',
              'cp -v /asset-input/package*.json .',
              'npm i --only=prod',
              'mkdir -p /asset-output/nodejs/',
              'cp -au node_modules /asset-output/nodejs/',
            ].join('&&'),
          ],
        },
      }),
      compatibleRuntimes: [lambda.Runtime.NODEJS_12_X],
      description: 'A layer to test the L2 construct',
    });

    new lambda.Function(this, 'MyHandler', {
      runtime: lambda.Runtime.NODEJS_12_X,
      code: lambda.Code.fromAsset(path.join(__dirname, '../lambda/src')),
      handler: 'index.handler',
      layers: [layer],
    });
  }
}

export class QCLifeScienceStack extends SolutionStack {

  // Methods //////////////////////////

  private createNotebookIamRole(): iam.Role {

    const role = new iam.Role(this, 'gcr-qc-notebook-role', {
      assumedBy: new iam.ServicePrincipal('sagemaker.amazonaws.com'),
    });

    role.addManagedPolicy(iam.ManagedPolicy.fromAwsManagedPolicyName('AmazonBraketFullAccess'))
    role.addToPolicy(new iam.PolicyStatement({
      resources: [
        'arn:aws:s3:::amazon-braket-*',
        'arn:aws:s3:::braketnotebookcdk-*',
        'arn:aws:s3:::qcstack*'
      ],
      actions: [
        "s3:GetObject",
        "s3:PutObject",
        "s3:ListBucket"
      ]
    }));

    role.addToPolicy(new iam.PolicyStatement({
      resources: [
        `arn:aws:logs:*:${this.account}:log-group:/aws/sagemaker/*`
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
        '*'
      ],
      actions: [
        "braket:*"
      ]
    }));
    return role;
  }

  // constructor 

  constructor(scope: Construct, id: string, props: StackProps = {}) {
    super(scope, id, props);
    this.setDescription('(SO8029) CDK for GCR solution: Quantum Computing in HCLS');

    const INSTANCE_TYPE = 'ml.m5.4xlarge'
    const CODE_REPO = 'https://github.com/amliuyong/aws-gcr-qc-life-science-public.git'

    const instanceTypeParam = new cdk.CfnParameter(this, "NotebookInstanceType", {
      type: "String",
      default: INSTANCE_TYPE,
      description: "Sagemaker notebook instance type"
    });

    const gitHubParam = new cdk.CfnParameter(this, "GitHubRepo", {
      type: "String",
      default: CODE_REPO,
      description: "Public GitHub repository"
    });

    const s3bucket = new s3.Bucket(this, 'amazon-braket', {
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      bucketName: `amazon-braket-${this.stackName.toLowerCase()}-${this.account}-${this.region}`,
      autoDeleteObjects: true
    });

    const role = this.createNotebookIamRole()

    const onStartContent = readFileSync(`${__dirname}/resources/onStart.template`, 'utf-8')

    const base64Encode = (str: string): string => Buffer.from(str, 'binary').toString('base64');
    const onStartContentBase64 = base64Encode(onStartContent)

    const installBraketSdK = new CfnNotebookInstanceLifecycleConfig(this, 'install-braket-sdk', {
      onStart: [{
        "content": onStartContentBase64
      }]
    });

    const notebookInstnce = new CfnNotebookInstance(this, 'GCRQCLifeScience', {
      instanceType: instanceTypeParam.valueAsString,
      roleArn: role.roleArn,
      rootAccess: 'Enabled',
      lifecycleConfigName: installBraketSdK.attrNotebookInstanceLifecycleConfigName,
      defaultCodeRepository: gitHubParam.valueAsString,
      volumeSizeInGb: 50,

    });
    // Output //////////////////////////

    new cdk.CfnOutput(this, "notebookName", {
      value: notebookInstnce.attrNotebookInstanceName,
      description: "Notebook name"
    });

    new cdk.CfnOutput(this, "bucketName", {
      value: s3bucket.bucketName,
      description: "S3 bucket name"
    });

    const notebookUrl = `https://console.aws.amazon.com/sagemaker/home?region=${this.region}#/notebook-instances/openNotebook/${notebookInstnce.attrNotebookInstanceName}?view=classic`

    new cdk.CfnOutput(this, "notebookUrl", {
      value: notebookUrl,
      description: "Notebook URL"
    });


    // BATCH  //////////////////////////
    const vpc = new ec2.Vpc(this, 'VPC');
    const batchEnvironment = new batch.ComputeEnvironment(this, 'Batch-Compute-Env', {
      computeResources: {
        type: batch.ComputeResourceType.FARGATE,
        vpc
      }
    });

    const jobQueue = new batch.JobQueue(this, 'JobQueue', {
      computeEnvironments: [{
        computeEnvironment: batchEnvironment,
        order: 1,
      }, ],
    });

    const Advantage_system1 = 'arn:aws:braket:::device/qpu/d-wave/Advantage_system1'
    const vcpus = 4
    const maxMemoryInGB = 9

    const jobDef = this.createBatchJobDef(1, 4, Advantage_system1, vcpus,
      maxMemoryInGB, s3bucket.bucketName)

    new cdk.CfnOutput(this, "batchJobDef", {
      value: jobDef.jobDefinitionName,
      description: "Batch Job Definition Name"
    });

    new cdk.CfnOutput(this, "jobQueue", {
      value: jobQueue.jobQueueName,
      description: "Batch Job Queue Name"
    });

    // step functions
    const vcpusMemValues = [
      [1, 2],
      [2, 4],
      [4, 8]
    ];
    const mValues = [2, 4];
    const dValues = [4];
    const deviceArns = [
      'arn:aws:braket:::device/qpu/d-wave/DW_2000Q_6',
      'arn:aws:braket:::device/qpu/d-wave/Advantage_system1'
    ]

    const taskList = [];

    for (let m of mValues) {
      for (let d of dValues) {
        for (let deviceArn of deviceArns) {
          const deviceName = deviceArn.split('/').pop();
          for (let [vcpus, memory] of vcpusMemValues) {
            const jobName = `M${m}-D${d}-${deviceName}-Vcpus${vcpus}-Mem${memory}`
            const batchTask = new tasks.BatchSubmitJob(this, `${jobName}`, {
              jobDefinitionArn: jobDef.jobDefinitionArn,
              jobName,
              jobQueueArn: jobQueue.jobQueueArn,
              containerOverrides: {
                command: ['--M', `${m}`, '--D', `${d}`, '--device-arn',
                  deviceArn, '--aws-region', this.region, '--instance-type', `vcpus-${vcpus}-mem-${memory}`,
                  '--s3-bucket', s3bucket.bucketName
                ],
                memory: cdk.Size.gibibytes(memory),
                vcpus
              },
              integrationPattern: sfn.IntegrationPattern.RUN_JOB

            });
            taskList.push(batchTask);
          }
        }
      }
    }

    const firstTask = taskList.shift();
    const secondTask = taskList.shift();
    let definition = null;
    if (firstTask && secondTask) {
      definition = firstTask.next(secondTask);
      for (let stepFuncTask of taskList) {
        definition = definition.next(stepFuncTask)
      }
    }

    if (definition) {
      const stateMachine = new sfn.StateMachine(this, 'StateMachine', {
        definition,
        timeout: cdk.Duration.hours(2),
      });

      new cdk.CfnOutput(this, "stateMachine", {
        value: stateMachine.stateMachineName,
        description: "state MachineName"
      });
    }

  }

  private createBatchJobDef(m: number, d: number, device: string, vcpus: number, maxMemoryInGB: number, bucketName: string): batch.JobDefinition {
    return new batch.JobDefinition(this, 'batch-job-def', {
      platformCapabilities: [batch.PlatformCapabilities.FARGATE],
      container: {
        image: ecs.ContainerImage.fromAsset('./src/batch-experiment'),
        command: ['--M', `${m}`, '--D', `${d}`, '--device-arn',
          device, '--aws-region', this.region, '--instance-type', `vcpus-${vcpus}-mem-${maxMemoryInGB}`,
          '--s3-bucket', bucketName
        ],
        vcpus,
        memoryLimitMiB: maxMemoryInGB * 1024,
        executionRole: this.createBatchJobExecutionRole('executionRole'),
        jobRole: this.createBatchJobExecutionRole('jobRole'),
        //privileged: true
      },
      timeout: cdk.Duration.seconds(3600 * 2),
      retryAttempts: 1
    });
  }

  private createBatchJobExecutionRole(roleName: string): iam.Role {
    const role = new iam.Role(this, roleName, {
      assumedBy: new iam.ServicePrincipal('ecs-tasks.amazonaws.com'),
    });

    role.addManagedPolicy(iam.ManagedPolicy.fromAwsManagedPolicyName('AmazonBraketFullAccess'))
    role.addToPolicy(new iam.PolicyStatement({
      resources: [
        'arn:aws:s3:::amazon-braket-*',
        'arn:aws:s3:::braketnotebookcdk-*',
        'arn:aws:s3:::qcstack*'
      ],
      actions: [
        "s3:GetObject",
        "s3:PutObject",
        "s3:ListBucket"
      ]
    }));

    role.addToPolicy(new iam.PolicyStatement({
      resources: [
        `arn:aws:logs:*:${this.account}:log-group:/aws/batch/*`
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
        '*'
      ],
      actions: [
        "braket:*",
        "ecr:*",
        "s3:*"
      ]
    }));

    return role
  }





}