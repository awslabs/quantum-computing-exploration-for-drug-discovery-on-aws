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
import * as quicksight from '@aws-cdk/aws-quicksight';

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

  private batchJobExecutionRole: iam.Role;
  private batchJobRole: iam.Role;

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

  private createAggResultLambdaRole(): iam.Role {
    const role = new iam.Role(this, 'AggResultLambdaRole', {
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
    });
    role.addManagedPolicy(iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'))
    role.addManagedPolicy(iam.ManagedPolicy.fromAwsManagedPolicyName('AmazonAthenaFullAccess'))
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

    const defaultQuicksightUser = `Admin-OneClick/yonmzn-Isengard`;

    const quickSightUserParam = new cdk.CfnParameter(this, "quickSightUser", {
      type: "String",
      default: defaultQuicksightUser,
      description: "quicksight user ARN"
    });
    const quicksightUser = `arn:aws:quicksight:us-east-1:${this.account}:user/default/${quickSightUserParam.valueAsString}`;

    const s3bucket = new s3.Bucket(this, 'amazon-braket', {
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      bucketName: `amazon-braket-${this.stackName.toLowerCase()}-${this.account}-${this.region}`,
      autoDeleteObjects: true
    });

    const role = this.createNotebookIamRole()

    const onStartContent = readFileSync(`${__dirname}/../resources/onStart.template`, 'utf-8')

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

    this.batchJobExecutionRole = this.createBatchJobExecutionRole('executionRole');
    this.batchJobRole = this.createBatchJobExecutionRole('jobRole');

    const instanceTypes = [
      ec2.InstanceType.of(ec2.InstanceClass.C5, ec2.InstanceSize.LARGE), // 2 vcpus, 4G mem
      ec2.InstanceType.of(ec2.InstanceClass.C5, ec2.InstanceSize.XLARGE), // 4 vcpus, 8G mem
      ec2.InstanceType.of(ec2.InstanceClass.C5, ec2.InstanceSize.XLARGE2), // 8 vcpus, 16G mem
      ec2.InstanceType.of(ec2.InstanceClass.C5, ec2.InstanceSize.XLARGE4), // 16 vcpus, 32G mem
    ];

    const vpc = new ec2.Vpc(this, 'VPC');
    const batchEnvironment = new batch.ComputeEnvironment(this, 'Batch-Compute-Env', {
      computeResources: {
        type: batch.ComputeResourceType.ON_DEMAND,
        vpc,
        allocationStrategy: batch.AllocationStrategy.BEST_FIT,
        instanceTypes
      }
    });

    const jobQueue = new batch.JobQueue(this, 'JobQueue', {
      computeEnvironments: [{
        computeEnvironment: batchEnvironment,
        order: 1,
      }, ],
    });

    const Advantage_system1 = 'arn:aws:braket:::device/qpu/d-wave/Advantage_system1';
    const vcpuMemList = [
      [2, 2],
      [4, 4],
      [8, 8],
      [16, 16]
    ];

    const jobDefs = vcpuMemList.map(it => {
      return this.createBatchJobDef(`QCJob_vCpus${it[0]}_Mem${it[1]}G`, 1, 4, Advantage_system1, it[0], it[1], s3bucket.bucketName);
    });

    new cdk.CfnOutput(this, "jobQueue", {
      value: jobQueue.jobQueueName,
      description: "Batch Job Queue Name"
    });

    // step functions
    const mValues = [1, 2, 3, 4];
    const dValues = [4];
    const deviceArns = [
      'arn:aws:braket:::device/qpu/d-wave/DW_2000Q_6',
      'arn:aws:braket:::device/qpu/d-wave/Advantage_system1',
      'arn:aws:braket:::device/qpu/d-wave/Advantage_system4'
    ];
    const taskList = [];

    for (let m of mValues) {
      for (let d of dValues) {
        for (let deviceArn of deviceArns) {
          const deviceName = deviceArn.split('/').pop();
          for (let i = 0; i < vcpuMemList.length; i++) {

            const [vcpu, mem] = vcpuMemList[i];
            const jobDef = jobDefs[i];
            const instanceType = this.getInstanceType(vcpu, mem)
            const jobName = `M${m}-D${d}-${deviceName}-${instanceType}`.replace(".", "_");

            const batchTask = new tasks.BatchSubmitJob(this, `${jobName}`, {
              jobDefinitionArn: jobDef.jobDefinitionArn,
              jobName,
              jobQueueArn: jobQueue.jobQueueArn,
              containerOverrides: {
                command: ['--M', `${m}`, '--D', `${d}`, '--device-arn',
                  deviceArn, '--aws-region', this.region, '--instance-type', `${instanceType}`,
                  '--s3-bucket', s3bucket.bucketName
                ],
              },
              integrationPattern: sfn.IntegrationPattern.RUN_JOB

            });
            taskList.push(batchTask);
          }
        }
      }
    }

    const batchParallel = new sfn.Parallel(this, "QCBatchParallel");

    for (const task of taskList) {
      batchParallel.branch(task)
    }

    const aggResultLambda = new lambda.Function(this, 'AggResultLambda', {
      runtime: lambda.Runtime.NODEJS_12_X,
      code: lambda.Code.fromAsset(path.join(__dirname, './lambda/AthenaTabeLambda/')),
      handler: 'index.handler',
      memorySize: 512,
      timeout: cdk.Duration.seconds(120),
      environment: {
        BUCKET: s3bucket.bucketName
      },
      role: this.createAggResultLambdaRole()
    });

    const aggResultStep = new tasks.LambdaInvoke(this, 'Aggregate Result', {
      lambdaFunction: aggResultLambda,
      outputPath: '$.Payload'
    });
    const success = new sfn.Succeed(this, 'Succeed');

    batchParallel.next(aggResultStep).next(success);


    // quicksight
    const qcDataSource = new quicksight.CfnDataSource(this, "qcDataSource", {
      awsAccountId: this.account,
      dataSourceId: `${this.stackName}-qcdatasource`,
      name: 'qcdatasource',
      type: 'ATHENA',
      dataSourceParameters: {
        athenaParameters: {
          workGroup: 'primary',
        },
      },
      permissions: [{
        principal: quicksightUser,
        actions: [
          'quicksight:UpdateDataSourcePermissions',
          'quicksight:DescribeDataSource',
          'quicksight:DescribeDataSourcePermissions',
          'quicksight:PassDataSource',
          'quicksight:UpdateDataSource',
          'quicksight:DeleteDataSource'
        ]
      }]
    });

    const columns = [{
        name: 'M',
        type: 'INTEGER'
      },
      {
        name: 'D',
        type: 'INTEGER'
      },
      {
        name: 'Device',
        type: 'STRING'
      },
      {
        name: 'InstanceType',
        type: 'STRING'
      },
      {
        name: 'ComputeType',
        type: 'STRING'
      },
      {
        name: 'mins',
        type: 'DECIMAL'
      },
    ];

    const qcDataset = new quicksight.CfnDataSet(this, "dataset", {
      permissions: [{
        principal: quicksightUser,
        actions: [
          'quicksight:UpdateDataSetPermissions',
          'quicksight:DescribeDataSet',
          'quicksight:DescribeDataSetPermissions',
          'quicksight:PassDataSet',
          'quicksight:DescribeIngestion',
          'quicksight:ListIngestions',
          'quicksight:UpdateDataSet',
          'quicksight:DeleteDataSet',
          'quicksight:CreateIngestion',
          'quicksight:CancelIngestion'
        ]
      }],
      awsAccountId: this.account,
      name: "qcdataset",
      dataSetId: `${this.stackName}-dataSetId`,
      importMode: 'DIRECT_QUERY',
      physicalTableMap: {
        ATHENATable: {
          customSql: {
            dataSourceArn: qcDataSource.attrArn,
            name: 'all',
            sqlQuery: 'SELECT M, D, Device, InstanceType, ComputeType, mins FROM "AwsDataCatalog"."default"."qc_batch_performance_view"',
            columns
          },
        }
      }
    });

    const templateArn = 'arn:aws:quicksight:us-east-1:080766874269:template/QC-analysis-template'

    const qcAnaTemplate = new quicksight.CfnTemplate(this, "qcqsAnaTemplate", {
      awsAccountId: this.account,
      templateId: `${this.stackName}-qcqsTemplateId`,
      name: 'qcqsTemplateId',
      permissions: [{
        principal: quicksightUser,
        actions: ['quicksight:DescribeTemplate']
      }],
      sourceEntity: {
        sourceTemplate: {
          arn: templateArn
        }
      }
    });

    const qcAnalysis = new quicksight.CfnAnalysis(this, "qcPefAnalysis", {
      awsAccountId: this.account,
      analysisId: `${this.stackName}-qcPefAnalysis`,
      name: "qcPefAnalysis",
      permissions: [{
        principal: quicksightUser,
        actions: [
          'quicksight:RestoreAnalysis',
          'quicksight:UpdateAnalysisPermissions',
          'quicksight:DeleteAnalysis',
          'quicksight:DescribeAnalysisPermissions',
          'quicksight:QueryAnalysis',
          'quicksight:DescribeAnalysis',
          'quicksight:UpdateAnalysis'
        ]
      }],
      sourceEntity: {
        sourceTemplate: {
          arn: qcAnaTemplate.attrArn,
          dataSetReferences: [{
            dataSetPlaceholder: 'qcds',
            dataSetArn: qcDataset.attrArn
          }]
        }
      },
    });

    const qcPrefDashboard = new quicksight.CfnDashboard(this, "qcPrefDashboard", {
      dashboardId: `${this.stackName}-qcPrefDashboard`,
      name: 'qcPrefDashboard',
      awsAccountId: this.account,
      permissions: [{
        principal: quicksightUser,
        actions: [
          'quicksight:DescribeDashboard',
          'quicksight:ListDashboardVersions',
          'quicksight:UpdateDashboardPermissions',
          'quicksight:QueryDashboard',
          'quicksight:UpdateDashboard',
          'quicksight:DeleteDashboard',
          'quicksight:DescribeDashboardPermissions',
          'quicksight:UpdateDashboardPublishedVersion'
        ]
      }],

      sourceEntity: {
        sourceTemplate: {
          arn: qcAnaTemplate.attrArn,
          dataSetReferences: [{
            dataSetPlaceholder: 'qcds',
            dataSetArn: qcDataset.attrArn
          }]
        }
      },
      dashboardPublishOptions: {
        adHocFilteringOption: {
          availabilityStatus: 'DISABLED'
        }
      }

    });



    new cdk.CfnOutput(this, "qcAnalysisArn", {
      value: qcAnalysis.attrArn,
      description: "qcAnalysis arn"
    });

    new cdk.CfnOutput(this, "qcPrefDashboardUrl", {
      value: `https://${this.region}.quicksight.aws.amazon.com/sn/dashboards/${qcPrefDashboard.dashboardId}`,
      description: "DashboardUrl Url"
    });


    const stateMachine = new sfn.StateMachine(this, 'QCBatchStateMachine', {
      definition: batchParallel,
      timeout: cdk.Duration.hours(2)
    });

    new cdk.CfnOutput(this, "stateMachine", {
      value: stateMachine.stateMachineName,
      description: "State Machine Name"
    });

    new cdk.CfnOutput(this, "datasetID", {
      value: qcDataset.dataSetId ? qcDataset.dataSetId : "",
      description: "dataset ID"
    });
  }



  private createBatchJobDef(defName: string, m: number, d: number, device: string,
    vcpus: number, mem: number, bucketName: string): batch.JobDefinition {
    const instanceType = this.getInstanceType(vcpus, mem)
    return new batch.JobDefinition(this, defName, {
      platformCapabilities: [batch.PlatformCapabilities.EC2],
      container: {
        image: ecs.ContainerImage.fromAsset(path.join(__dirname, './batch-experiment')),
        command: ['--M', `${m}`, '--D', `${d}`, '--device-arn',
          device, '--aws-region', this.region, '--instance-type', `${instanceType}`,
          '--s3-bucket', bucketName
        ],
        executionRole: this.batchJobExecutionRole,
        jobRole: this.batchJobRole,
        vcpus,
        memoryLimitMiB: mem * 1024,
        privileged: true
      },
      timeout: cdk.Duration.seconds(3600 * 2),
      retryAttempts: 1
    });
  }

  private getInstanceType(vcpus: number, mem: number): string {
    return `vCpus${vcpus}_Mem_${mem}G`;
  }
}