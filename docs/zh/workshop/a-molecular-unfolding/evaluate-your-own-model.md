
批量评估自定义的模型有两种方法：

- 批量评估mol2文件，无需更改代码
- 完全自定义评估代码

## 批量评估mol2文件，无需更改代码

如果您有mol2文件，可以按照以下步骤批量评估：

1. 将您的mol2文件上传到CloudFormation输出中的S3存储桶，或您自己的S3存储桶。如果您想使用自己的S3存储桶，存储桶名称必须遵循以下格式：`braket-*` 或 `amazon-braket-*`。

2. 在Step Functions输入中将mol2文件的S3 uri指定为`molFile` 的值

     
        {
            "molFile" : "<您的 mol2 文件的 s3 uri>"
        }
   

       例如
    
        {
           “molFile”：“s3://amazon-braket-gcr-qc-sol-common/qc/raw_model/117_ideal.mol2”
        }

    
    有关完整的输入参数和架构，请参考[输入规范](../batch-evaluation/#输入规范)。

3. 按照[批量评估](../batch-evaluation/#start-execution)中的步骤运行Step Functions。

## 完全自定义评估代码


您可以利用Apache License Version 2.0下的开源项目做为基本代码，对其进行更改，完全自定义评估代码。

请按照以下步骤进行更改并从CDK重新部署整个堆栈。

### 先决条件

1. 确保您的工作区中安装了AWS CLI和 AWS CDK。详情请参考[AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)。
   
2. 确认执行部署的用户或IAM角色必须至少拥有[permissions](./permissions.json)。

3. [检查您的QuickSight账户](../../../deployment/#check-your-quicksight)。

4. 确保您的工作区中运行了docker。有关如何安装docker，请参见[Docker Install](https://docs.docker.com/engine/install/)。

### 自定义评估代码

1. 将本方案的github仓库fork到自己的git仓库。

2. 将项目克隆到自己的工作区。

3. 修改源代码

    !!! caution "注意"
        
        文件source/src/molecular-unfolding/cdk/construct-notebook.ts中变量githubRepo应该修改为您的git仓库。


### 将堆栈从 CDK 部署到您的 AWS 账户

1. 检查您的AWS账户中的CloudFormation，确保您的部署区域中没有名为`QCStack`的堆栈。

2. 检查您的 S3 存储桶，确保没有名为 `amazon-braket-qcstack-<your aws account>-<deployment region>` 的存储桶。

3. 利用CDK将更改部署到您的AWS账户。

    ```bash
    cd source
    npm install
    npx cdk deploy QCStack --parameters QuickSightUser=<your QuickSight user>
    ```
           
4. 等待部署完成。部署大约需要10分钟。

5. 从CloudFormation输出中获取输出链接，链接包括：
    - Step Functions URL
    - QuickSight仪表板链接
    - 笔记本网址
    - S3存储桶名称

6. 按照[批量评估](../batch-evaluation/)中的步骤运行您自己的代码。

7. 通过QuickSight仪表板[查看结果](../batch-evaluation/#view-dashboard)。
