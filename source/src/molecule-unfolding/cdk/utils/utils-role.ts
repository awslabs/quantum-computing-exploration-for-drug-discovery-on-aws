import * as cdk from '@aws-cdk/core';
import * as iam from '@aws-cdk/aws-iam'
import * as s3 from '@aws-cdk/aws-s3'

interface Props {
    region: string;
    account: string;
    bucket: s3.Bucket;
    prefix: string;
}

export class RoleUtil {
    private props: Props
    private scope: cdk.Construct
    private constructor(scope: cdk.Construct, props: Props) {
        this.props = props
        this.scope = scope
    }

    public static newInstance(scope: cdk.Construct, props: Props) {
        return new this(scope, props);
    }

    public createNotebookIamRole(): iam.Role {
        const role = new iam.Role(this.scope, `NotebookRole`, {
            assumedBy: new iam.ServicePrincipal('sagemaker.amazonaws.com'),
        });

        role.addManagedPolicy(iam.ManagedPolicy.fromAwsManagedPolicyName('AmazonBraketFullAccess'))

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
                `arn:aws:ecr:${this.props.region}:${this.props.account}:repository/*`
            ],
            actions: [
                "ecr:PutImageTagMutability",
                "ecr:StartImageScan",
                "ecr:DescribeImageReplicationStatus",
                "ecr:ListTagsForResource",
                "ecr:UploadLayerPart",
                "ecr:BatchDeleteImage",
                "ecr:BatchGetRepositoryScanningConfiguration",
                "ecr:DeleteRepository",
                "ecr:CompleteLayerUpload",
                "ecr:TagResource",
                "ecr:DescribeRepositories",
                "ecr:BatchCheckLayerAvailability",
                "ecr:ReplicateImage",
                "ecr:GetLifecyclePolicy",
                "ecr:PutLifecyclePolicy",
                "ecr:DescribeImageScanFindings",
                "ecr:GetLifecyclePolicyPreview",
                "ecr:CreateRepository",
                "ecr:PutImageScanningConfiguration",
                "ecr:GetDownloadUrlForLayer",
                "ecr:DeleteLifecyclePolicy",
                "ecr:PutImage",
                "ecr:UntagResource",
                "ecr:BatchGetImage",
                "ecr:StartLifecyclePolicyPreview",
                "ecr:InitiateLayerUpload",
                "ecr:GetRepositoryPolicy"
            ]
        }));

        role.addToPolicy(new iam.PolicyStatement({
            resources: [
                `arn:aws:logs:*:${this.props.account}:log-group:/aws/sagemaker/*`
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


    public createBatchJobExecutionRole(roleName: string): iam.Role {
        const role = new iam.Role(this.scope, `${roleName}`, {
            assumedBy: new iam.ServicePrincipal('ecs-tasks.amazonaws.com'),
        });

        role.addManagedPolicy(iam.ManagedPolicy.fromAwsManagedPolicyName('AmazonEC2ContainerRegistryReadOnly'))

        //role.addManagedPolicy(iam.ManagedPolicy.fromAwsManagedPolicyName('AmazonBraketFullAccess'))

        role.addToPolicy(new iam.PolicyStatement({
            resources: [
                `arn:aws:braket:*:${this.props.account}:quantum-task/*`,
                `arn:aws:braket:*:${this.props.account}:job/*`
            ],
            actions: [
                "braket:GetJob",
                "braket:GetQuantumTask",
                "braket:CancelQuantumTask",
                "braket:CancelJob",
                "braket:ListTagsForResource"
            ]
        }));

        role.addToPolicy(new iam.PolicyStatement({
            resources: [
                '*'
            ],
            actions: [
                "braket:CreateJob",
                "braket:GetDevice",
                "braket:SearchDevices",
                "braket:CreateQuantumTask",
                "braket:SearchJobs",
                "braket:SearchQuantumTasks"
            ]
        }));


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
        return role
    }


    public createAggResultLambdaRole(): iam.Role {
        const role = new iam.Role(this.scope, `AggResultLambdaRole`, {
            assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
        });
        role.addManagedPolicy(iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'))
        //role.addManagedPolicy(iam.ManagedPolicy.fromAwsManagedPolicyName('AmazonAthenaFullAccess'))
        role.addToPolicy(new iam.PolicyStatement({
            resources: [
                `arn:aws:athena:*:${this.props.account}:workgroup/*`,
                `arn:aws:athena:*:${this.props.account}:datacatalog/*`
            ],
            actions: [
                "athena:StartQueryExecution",
                "athena:GetQueryResults"
            ]
        }));

        role.addToPolicy(new iam.PolicyStatement({
            resources: [
                '*'
            ],
            actions: [
                "athena:ListDataCatalogs"
            ]
        }));


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

    public createBraketLambdaRole(roleName: string): iam.Role {
        const role = new iam.Role(this.scope, `${roleName}`, {
            assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
        });
        role.addManagedPolicy(iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'))

        role.addToPolicy(new iam.PolicyStatement({
            resources: [
                `arn:aws:braket:*:${this.props.account}:quantum-task/*`,
                `arn:aws:braket:*:${this.props.account}:job/*`
            ],
            actions: [
                "braket:GetJob",
                "braket:GetQuantumTask",
                "braket:CancelQuantumTask",
                "braket:CancelJob",
                "braket:ListTagsForResource"
            ]
        }));

        role.addToPolicy(new iam.PolicyStatement({
            resources: [
                '*'
            ],
            actions: [
                "braket:CreateJob",
                "braket:GetDevice",
                "braket:SearchDevices",
                "braket:CreateQuantumTask",
                "braket:SearchJobs",
                "braket:SearchQuantumTasks"
            ]
        }));

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


    public createGenericLambdaRole(roleName: string): iam.Role {
        const role = new iam.Role(this.scope, `${roleName}`, {
            assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
        });
        role.addManagedPolicy(iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'))
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


    public createCallBackLambdaRole(roleName: string): iam.Role {
        const role = new iam.Role(this.scope, `${roleName}`, {
            assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
        });
        role.addManagedPolicy(iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'))
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
}