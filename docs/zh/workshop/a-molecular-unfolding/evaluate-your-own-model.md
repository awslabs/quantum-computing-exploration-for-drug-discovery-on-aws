## 批量评估自定义模型

本方案为 Apache License Version 2.0 下的开源项目。您可将其做为基本代码，进行更改。

您可以通过以下步骤完全自定义评估代码，并从 CDK 重新部署整个堆栈。

### 先决条件

1. 确保您的工作区中安装了 AWS CLI 和 AWS CDK。详情请参考[AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)。
2. 确认执行部署的用户或 IAM 角色必须至少拥有[permissions](./permissions.json)。

3. 检查部署的[准备工作](../../deployment.md)。

4. 确保您的工作区中运行了 docker。有关如何安装 docker，请参见[Docker Install](https://docs.docker.com/engine/install/)。

### 自定义评估代码

1. 将本方案的 GitHub 仓库 fork 到您自己的 Git 仓库。

2. 将项目克隆到您自己的工作区。

3. 修改源代码。如果您想要修改量子算法，可以在目录`source/src/XXXX/utility`下修改代码，其中 XXXX 为 case 名。

### 将堆栈从 CDK 部署到您的 AWS 账户

1.  检查您的 AWS 账户中的 CloudFormation，确保您的部署区域中没有名为`QCEDDStack`的堆栈。

2.  检查您的 S3 存储桶，确保没有名为 `amazon-braket-qceddstack-<your aws account>-<deployment region>` 的存储桶。

3.  利用 CDK 将更改部署到您的 AWS 账户。

        cd source
        npm install
        npx cdk deploy QCEDDStack  \
         --parameters DeployNotebook=yes \
         --parameters DeployBatchEvaluation=yes \
         --parameters DeployVisualization=yes \
         --parameters QuickSightUser=<your QuickSight user> \
         --parameters QuickSightRoleName=<your QuickSight service role name>

4.  等待部署完成。部署大约需要 10 分钟。

5.  从 CloudFormation 输出中获取输出链接，链接包括：

    - Step Functions URL
    - QuickSight 仪表板链接
    - 笔记本网址
    - S3 存储桶名称

6.  按照[批量评估](batch-evaluation.md)中的步骤运行您自己的代码。

7.  通过 QuickSight 仪表板查看结果。
