要卸载药物发现量子计算解决方案，请删除CloudFormation堆栈。

您可以使用亚马逊云科技管理控制台或CLI删除CloudFormation堆栈。

## 使用亚马逊云科技管理控制台删除堆栈

1. 登录[AWS CloudFormation][cloudformation-console]控制台。
2. 在**堆栈**页面上，选择此解决方案的安装堆栈。
3. 选择**删除**。

## 使用CLI删除堆栈

1. 确定命令行在您的环境中是否可用。有关安装说明，请参阅CLI用户指南中的[CLI是什么][aws-cli]。
2. 确认CLI可用后，请运行以下命令:

    ```bash
    aws cloudformation delete-stack --stack-name <installation-stack-name>
    ```

## 删除QuickSight账户（可选）

1. 导航至[QuickSight](https://us-east-1.quicksight.aws.amazon.com/sn/admin)页面。
2. 选择**账户设置**。
3. 选择**删除账户**。

    !!! Warning 注意

        删除QuickSight账户时，所有控制面板、分析和其他相关数据也将被删除。

4.  输入*确认*删除账户。  

[cloudformation-console]: https://console.aws.amazon.com/cloudformation/home
[aws-cli]: https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-welcome.html
