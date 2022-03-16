Before you launch the solution, review the architecture, supported regions, and other considerations discussed in this guide. Follow the step-by-step instructions in this section to configure and deploy the solution into your account.


!!! notice

    It's good practice to set a billing alarm before deploying this solution. Refer to this [link](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/monitor_estimated_charges_with_cloudwatch.html)


**Time to deploy**: Approximately 10 minutes


## Deployment Overview

- Step 1: Prerequisites
    - Enable Amazon Braket service
    - Create IAM Role for QuickSight
    - Sign up for QuickSight
    - Get QuickSight Username

- Step 2: Launch the AWS CloudFormation template into your AWS account to deploy the solution
- Step 3: Subscribe SNS notification (optional)


## Step 1: Prerequisites

### Enable Amazon Braket service

1. Login AWS Console, find Amazon Braket.

2. Open Amazon Braket, select **I have read and accepted the above terms & conditions**.

3. Click **Enable Amazon Braket**.

### Create IAM Role for QuickSight

1. Go to [IAM Policies](https://console.aws.amazon.com/iamv2/home?#/policies).

2. Click **Create Policy**.

3. In Create policy page, click **JSON** tab, fill below QuickSight policy, this is the least policy that QuickSight can work in this solution.
        
        {
            "Version": "2012-10-17",
            "Statement": [{
                    "Effect": "Allow",
                    "Action": [
                        "athena:BatchGetQueryExecution",
                        "athena:CancelQueryExecution",
                        "athena:GetCatalogs",
                        "athena:GetExecutionEngine",
                        "athena:GetExecutionEngines",
                        "athena:GetNamespace",
                        "athena:GetNamespaces",
                        "athena:GetQueryExecution",
                        "athena:GetQueryExecutions",
                        "athena:GetQueryResults",
                        "athena:GetQueryResultsStream",
                        "athena:GetTable",
                        "athena:GetTables",
                        "athena:ListQueryExecutions",
                        "athena:RunQuery",
                        "athena:StartQueryExecution",
                        "athena:StopQueryExecution",
                        "athena:ListWorkGroups",
                        "athena:ListEngineVersions",
                        "athena:GetWorkGroup",
                        "athena:GetDataCatalog",
                        "athena:GetDatabase",
                        "athena:GetTableMetadata",
                        "athena:ListDataCatalogs",
                        "athena:ListDatabases",
                        "athena:ListTableMetadata"
                    ],
                    "Resource": [
                        "*"
                    ]
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "glue:CreateDatabase",
                        "glue:DeleteDatabase",
                        "glue:GetDatabase",
                        "glue:GetDatabases",
                        "glue:UpdateDatabase",
                        "glue:CreateTable",
                        "glue:DeleteTable",
                        "glue:BatchDeleteTable",
                        "glue:UpdateTable",
                        "glue:GetTable",
                        "glue:GetTables",
                        "glue:BatchCreatePartition",
                        "glue:CreatePartition",
                        "glue:DeletePartition",
                        "glue:BatchDeletePartition",
                        "glue:UpdatePartition",
                        "glue:GetPartition",
                        "glue:GetPartitions",
                        "glue:BatchGetPartition"
                    ],
                    "Resource": [
                        "*"
                    ]
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "s3:GetBucketLocation",
                        "s3:GetObject",
                        "s3:ListBucket",
                        "s3:ListBucketMultipartUploads",
                        "s3:ListMultipartUploadParts",
                        "s3:AbortMultipartUpload",
                        "s3:CreateBucket",
                        "s3:PutObject",
                        "s3:PutBucketPublicAccessBlock"
                    ],
                    "Resource": [
                        "arn:aws:s3:::aws-athena-query-results-*"
                    ]
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "lakeformation:GetDataAccess",
                        "iam:List*"
                    ],
                    "Resource": [
                        "*"
                    ]
                }
            ]
        }

4. Click **Next:Tags**.

5. Click **Next:Review**.

6. Fill **Name**: `qradd-quicksight-service-role-policy`.

7. Click **Create policy**.

8. Go to [IAM Roles](https://console.aws.amazon.com/iamv2/home?#/roles).

9. Click **Create Role**.

10. Select **Custom trust policy** in the Select trusted entity page, fill below trust policy in **Custom trust policy**.
        
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "quicksight.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }


11. Click **Next**.

12. Enter `qradd-quicksight-service-role-policy` in **Permissions policies** search input.

13. Select the policy, Click **Next**.

14. Fill **Role name** : `qradd-quicksight-service-role`.

15. Click **Create role**.

16. Record the name of this role(will be used in deployment steps).

### Sign up for QuickSight

!!! notice
    You need correct AWS Identity and Access Management (IAM) permissions to sign up for QuickSight, please refer to [Signing up for an Amazon QuickSight subscription](https://docs.aws.amazon.com/quicksight/latest/user/signing-up.html)


* Sign in to the AWS Management Console, navigate to [QuickSight](https://quicksight.aws.amazon.com/).

* Choose **Enterprise**, click continue.

* In the **Create your QuickSight account** page, fill the necessary information:

<center>

|      Field Name      |   Value |  Comment |
|:--------------------|:-------------------| :-------------------|
| Authentication method | Choose **Use IAM federated identities & QuickSight-managed users** | The default value|
| Select a region | Choose **US East(N.Virginia)**  | The default value |
| QuickSight account name | Any string value | Unique QuickSight account name|
| Notification email address | your email | |
| IAM Role| Choose **Use an existing role**, select the role: `qradd-quicksight-service-role`| |

</center>


!!! Caution 

    If Quicksight service already used default role, you need to change it to the role created above in page [QuickSight Security & permissions](https://us-east-1.quicksight.aws.amazon.com/sn/admin#aws).
    This action may influence other data under this QuickSight Account. Please check in advance. 
    You can refer to this [document](https://docs.aws.amazon.com/quicksight/latest/user/security_iam_service-with-iam.html#security-create-iam-role) to update Quicksight role and its policy.

### Get QuickSight Username

* (Optional) Navigate to [QuickSight](https://quicksight.aws.amazon.com/), fill your email if QuickSight user is not created for
 your current AWS account.

* Go to [QuickSight Admin](https://us-east-1.quicksight.aws.amazon.com/sn/admin), record your **QuickSight Username**(not QuickSight account name) for your email.

## Step 2: Launch the AWS CloudFormation template into your AWS account to deploy the solution

1. Login AWS console, click [Launch Stack][template-url] to deploy solution via the AWS CloudFormation template.
 
2. The template launches in the US West(Oregon) by default. To launch this solution in a different AWS Region(for example `us-east-1`), use the Region selector in the console navigation bar.

3. In the **Create stack** page, Amazon S3 URL should be filled with this [template URL][cf-template-url] automatically, please review and confirm then click **Next**.

4. Under **Parameters**, review the parameters for the template and modify them as necessary.

5. This solution uses the following values. Choose **Next**.


|      Parameter      |   Description |
|:-------------------|:----|
| QuickSightUser | QuickSight Username, get it from [Manage users](https://us-east-1.quicksight.aws.amazon.com/sn/admin?#users). |
| QuickSightRoleName | QuickSight Service Role name, get it from [Security & permissions](https://us-east-1.quicksight.aws.amazon.com/sn/admin?#aws).|

6. Choose **Next**.

7. On the **Configure stack options** page, choose **Next**.

8. On the **Review** page, review and confirm the settings. Check the box acknowledging that the template will create AWS Identity and Access Management (IAM) resources.

9. Choose **Create stack** to deploy the stack.

You can view the status of the stack in the AWS CloudFormation Console in the **Status** column. You should receive a CREATE_COMPLETE status in approximately 10 minutes.

## Step 3: Subscribe SNS notification (optional)

!!! notice
    This step is optional.

Follow below steps to subscribe SNS notification via Email, you might subscribe the notification via [text messages](https://docs.aws.amazon.com/sns/latest/dg/sns-mobile-phone-number-as-subscriber.html).

1. Get your SNS topic name in the CloudFormation deployment output

    ![SNS name](./images/deploy-output-sns.png)

2. Navigate to [SNS topics](https://console.aws.amazon.com/sns/v3/home?region=us-east-1#/topics) AWS console.

3. Click the SNS topic which is in CloudFormation deployment output.

4. Click **Create subscription** button.

5. Select Email in  **Protocol** list.

6. Fill your email in  **Endpoint**.

7. Click **Create subscription**.

8. Check inbox of your email, you will get an email, click the **Confirm subscription** link to confirm the subscription.


[template-url]: https://console.aws.amazon.com/cloudformation/home?region=us-west-2#/stacks/create/template?stackName=QRADDStack&templateURL={{ cf_template.url }}
[cf-template-url]: {{ cf_template.url }}