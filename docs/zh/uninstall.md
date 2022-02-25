要卸载亚马逊云科技药物研发量子计算解决方案，请删除CloudFormation堆栈。

您可以使用亚马逊云科技管理控制台或CLI删除CloudFormation堆栈。

## 使用亚马逊云科技管理控制台删除堆栈

1. 登陆
[AWS CloudFormation][cloudformation-console]界面。
2. 选择此解决方案的安装栈。
3. 选择 **Delete**。

## 使用CLI删除堆栈

确定命令行在您的环境中是否可用。
有关安装说明，请参阅CLI用户指南中的[CLI是什么][aws-cli]。
在确认了AWS CLI已经安装，请运行以下命令:

```bash
aws cloudformation delete-stack --stack-name <installation-stack-name> --region <aws-region>
```

## 删除QuickSight账户（可选项）

进入[quicksight admin](https://us-east-1.quicksight.aws.amazon.com/sn/admin) 的 **Account settings**，并点击 **Delete account**。

!!! Warning

    这个操作可能会影响该QuickSight账户下的其他数据，请注意检查

[cloudformation-console]: https://console.aws.amazon.com/cloudformation/home
[aws-cli]: https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-welcome.html
