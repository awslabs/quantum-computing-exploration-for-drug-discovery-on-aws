## 批量评估自定义模型

本方案为Apache License Version 2.0下的开源项目。您可将其做为基本代码，进行更改。

您可以通过以下步骤完全自定义评估代码，并从CDK重新部署整个堆栈。

### 先决条件

1. 确保您的工作区中安装了AWS CLI和 AWS CDK。详情请参考[AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)。
   
2. 确认执行部署的用户或IAM角色必须至少拥有[permissions](./permissions.json)。

3. 检查部署的[准备工作](../../deployment.md)。

4. 确保您的工作区中运行了docker。有关如何安装docker，请参见[Docker Install](https://docs.docker.com/engine/install/)。

### 自定义评估代码

1. 将本方案的GitHub仓库fork到您自己的Git仓库。

2. 将项目克隆到您自己的工作区。

3. 修改源代码。如果您想要修改量子算法，可以在目录`source/src/molecular-unfolding/utility`下修改代码。

### 将堆栈从 CDK 部署到您的 AWS 账户

1. 检查您的AWS账户中的CloudFormation，确保您的部署区域中没有名为`QCEDDStack`的堆栈。

2. 检查您的 S3 存储桶，确保没有名为 `amazon-braket-qceddstack-<your aws account>-<deployment region>` 的存储桶。

3. 利用CDK将更改部署到您的AWS账户。

        cd source
        npm install
        npx cdk deploy QCEDDStack  \
         --parameters DeployNotebook=yes \
         --parameters DeployBatchEvaluation=yes \
         --parameters DeployVisualization=yes \
         --parameters QuickSightUser=<your QuickSight user> \
         --parameters QuickSightRoleName=<your QuickSight service role name>

           
4. 等待部署完成。部署大约需要10分钟。

5. 从CloudFormation输出中获取输出链接，链接包括：
    - Step Functions URL
    - QuickSight仪表板链接
    - 笔记本网址
    - S3存储桶名称

6. 按照[批量评估](batch-evaluation.md)中的步骤运行您自己的代码。

7. 通过QuickSight仪表板查看结果。
