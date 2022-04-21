To uninstall Quantum Computing Exploration for Drug Discovery on AWS, you must delete the AWS CloudFormation stack. 

You can use either the AWS Management Console or the AWS Command Line Interface (CLI) to delete the CloudFormation stack.

## Using the AWS Management Console

1. Sign in to the [AWS CloudFormation][cloudformation-console] console.
2. Select this solution’s installation stack.
3. Choose **Delete**.

## Using AWS Command Line Interface

Determine whether the AWS CLI is available in your environment. For installation instructions, see [What Is the AWS Command Line Interface][aws-cli] in the *AWS CLI User Guide*. After confirming that the AWS CLI is available, run the following command.

```bash
$ aws cloudformation delete-stack --stack-name <installation-stack-name>
```

## Delete QuickSight Account (Optional)

1. Go to [QuickSight](https://us-east-1.quicksight.aws.amazon.com/sn/admin).

2. Choose **Account settings**. 

3. Choose **Delete account**.

    !!! Caution "Caution"

         All users on this account will be permanently deleted along with all dashboards, analyses, and other related data. 

4. Enter *Confirm* to delete the account.

## Delete QuickSight Role (Optional)

1. Go to [IAM Role](https://console.aws.amazon.com/iamv2/home#/roles) AWS console.

2. Search for the role name. For example, `qradd-quicksight-service-role`.

3. Select the role.

4. Choose **Delete**.

[cloudformation-console]: https://console.aws.amazon.com/cloudformation/home
[aws-cli]: https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-welcome.html
