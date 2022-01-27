Before you launch the solution, review the architecture, supported regions, and other considerations discussed in this guide. Follow the step-by-step instructions in this section to configure and deploy the solution into your account.

**Time to deploy**: Approximately 10 minutes

## Deployment overview

Use the following steps to deploy this solution on AWS.

- Check your QuickSight account
- Launch the AWS CloudFormation template into your AWS account to deploy the solution.
- Update QuickSight permissions

## Deployment

### Check your QuickSight

* Sign in to the AWS Management Console, navigate to
[QuickSight](https://quicksight.aws.amazon.com/)

* If you did not have a QuickSight account, you need to sign up for QuickSight.

* Choose **Enterprise**, click continue

* In the **Create your QuickSight account** page, fill the necessary information:
![Fill information for quicksight](./images/create_quicksight.png)

* Go to [quicksight admin](https://us-east-1.quicksight.aws.amazon.com/sn/admin), record your **QuickSight Username**(not QuickSight account name).

![quicksight username](./images/quicksight_username.png)

### Deploy solution

This automated AWS CloudFormation template deploys the solution in the AWS Cloud.

* Use 
[Launch solution in AWS Standard Regions](https://console.aws.amazon.com/cloudformation/home?region=us-west-2#/stacks/new?stackName=qrsdd-stack) to launch the AWS CloudFormation template.

* The template launches in the US West 2 (Oregon) Region by default. To launch this solution in a different AWS Region, use the Region selector in the console navigation bar.

* On the **Create stack** page, verify that the correct [quantum-ready-solution-for-drug-discovery.template](template.md) is shown in the **Amazon S3 URL** text box and choose **Next**.

* Under **Parameters**, review the parameters for the template and modify them as necessary. This solution uses the following values. Choose **Next**.

    |      Parameter      |                                                         Description                                                      |
    |:-------------------:|:----:|
    | MolUnfDashboardquickSightUser | **Quicksight Username** |


* On the **Configure stack options** page, choose **Next**.

* On the **Review** page, review and confirm the settings. Check the box acknowledging that the template will create AWS Identity and Access Management (IAM) resources.

* Choose **Create stack** to deploy the stack.


You can view the status of the stack in the AWS CloudFormation Console in the **Status** column. You should receive a CREATE_COMPLETE status in approximately 10 minutes.


### Update QuickSight permissions

* Navigate to Quicksight [admin page](https://us-east-1.quicksight.aws.amazon.com/sn/admin#aws)

* Click **Manage**
![mange quicksight](./images/manage_quicksight.png)

* Click **Select S3 Buckets**
![select s3 quicksight](./images/select_s3_bucket.png)

* Check the bucket `amazon-braket-qcstack-<AWS account>-<region>`
![choose s3 quicksight](./images/choose_s3_bucket.png)

* Click **Finish** and then **Save**


