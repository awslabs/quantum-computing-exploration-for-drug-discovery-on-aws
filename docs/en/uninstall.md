To uninstall the AWS QRSDD solution, you must delete the AWS CloudFormation stack. 

You can use either the AWS Management Console or the AWS Command Line Interface (AWS CLI) to delete the CloudFormation stack.

## Uninstall the stack using the AWS Management Console

1. Sign in to the [AWS CloudFormation][cloudformation-console] console.
2. Select this solution’s installation stack.
3. Choose **Delete**.

## Uninstall the stack using AWS Command Line Interface

Determine whether the AWS Command Line Interface (AWS CLI) is available in your environment. For installation instructions, refer to [What Is the AWS Command Line Interface][aws-cli] in the *AWS CLI User Guide*. After confirming that the AWS CLI is available, run the following command.

```bash
aws cloudformation delete-stack --stack-name <installation-stack-name> --region <aws-region>
```

## Delete QuickSight Account (Optional)

Go to the **Account settings** of 
[quicksight admin](https://us-east-1.quicksight.aws.amazon.com/sn/admin) and click **Delete account**。

!!! Warning

    This action may influence other data under this QuickSight Account. 
    Please check in advance.

[cloudformation-console]: https://console.aws.amazon.com/cloudformation/home
[aws-cli]: https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-welcome.html