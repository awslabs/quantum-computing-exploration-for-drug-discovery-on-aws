Before you launch the solution, review the architecture, supported regions, and other considerations discussed in this guide. Follow the step-by-step instructions in this section to configure and deploy the solution into your account.

**Time to deploy**: Approximately [10] minutes

## Deployment overview

Use the following steps to deploy this solution on AWS. 

- Check your QuickSight account
- Launch the AWS CloudFormation template into your AWS account to deploy the solution.
- Setup AWS EventBright cross region event if deployment region is not `us-west-2`
- Update QuickSight permissions

## Deployment

### Check your QuickSight

1. Sign in to the AWS Management Console, navigate to [QuickSight](https://quicksight.aws.amazon.com/){target=_blank}

1. If you did not have a QuickSight account, you need to sign up for QuickSight.

1. Get your QuickSight username (not QuickSight account name).


### Deploy solution 

This automated AWS CloudFormation template deploys the solution in the AWS Cloud.


1. Use [Launch solution in AWS Standard Regions][launch-template] to launch the AWS CloudFormation template.   

1. The template launches in the US West 2 (Oregon) Region by default. To launch this solution in a different AWS Region, use the Region selector in the console navigation bar.


1. On the **Create stack** page, verify that the correct template URL is shown in the **Amazon S3 URL** text box and choose **Next**.

1. On the **Specify stack details** page, assign a valid and account level unique name to your solution stack. For information about naming character limitations, refer to [IAM and STS Limits][iam-limit] in the `AWS Identity and Access Management User Guide`.

1. Under **Parameters**, review the parameters for the template and modify them as necessary. This solution uses the following default values.

    |      Parameter      |    Default   |                                                      Description                                                      |
    |:-------------------:|:------------:|:--------------------------------------------------------------------------------------------------------------|
    | MolUnfNotebookNotebookInstanceType | ml.c5.xlarge |  Notebook instance type |
    | MolUnfDashboardquicksightTemplateAccountId | 522244679887 |  Quicksight dashboard template account Id |
    | MolUnfDashboardquickSightUser | | your AWS Quicksight user name |


1. Choose **Next**.

1. On the **Configure stack options** page, choose **Next**.

1. On the **Review** page, review and confirm the settings. Check the box acknowledging that the template will create AWS Identity and Access Management (IAM) resources.

1. Choose **Create stack** to deploy the stack.

    You can view the status of the stack in the AWS CloudFormation Console in the **Status** column. You should receive a CREATE_COMPLETE status in approximately [10] minutes.

1. If your deployment region is not `us-west-2`, need to perform more steps blow.  


### Setup AWS EventBright cross region event

You need to perform blow steps to setup AWS EventBright cross region event if your deployment region is not `us-west-2`

1.  Use the Region selector in the console navigation bar, switch your region to `us-west-2`.

1. Use [Launch solution in AWS Standard Regions][launch-template] to launch the AWS CloudFormation template. 

1. Under **Parameters**, review the parameters for the template and modify them as necessary. This solution uses the following default values.

    |      Parameter      |    Default   |                                                      Description                                                      |
    |:-------------------:|:------------:|:--------------------------------------------------------------------------------------------------------------|
    | TargetRegion | us-east-1 |  the target region   |
   
1. Choose **Next**.

1. On the **Configure stack options** page, choose **Next**.

1. On the **Review** page, review and confirm the settings. Check the box acknowledging that the template will create AWS Identity and Access Management (IAM) resources.

1. Choose **Create stack** to deploy the stack.

    You can view the status of the stack in the AWS CloudFormation Console in the **Status** column. You should receive a CREATE_COMPLETE status less than [1] minute.


### Update QuickSight permissions

1. Navigate to Quicksight [admin page](https://us-east-1.quicksight.aws.amazon.com/sn/admin#aws){target=_blank}

1. Click **Manage**

1. Click **Select S3 Buckets**

1. Check the bucket `amazon-braket-qcstack-<AWS account>-<region>`

1. Click **Finish**

1. Click **Save**



