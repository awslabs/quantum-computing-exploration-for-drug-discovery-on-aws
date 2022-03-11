在部署解决方案之前，建议您先查看本指南中有关架构图和区域支持等信息。然后按照下面的说明配置解决方案并将其部署到您的帐户中。

**部署时间**：约10分钟

!!! Note 说明

    建议您在部署此解决方案之前[创建账单告警](https://docs.aws.amazon.com/zh_cn/AmazonCloudWatch/latest/monitoring/monitor_estimated_charges_with_cloudwatch.html)以监控AWS估算费用。

## 部署概述

在亚马逊云科技上部署本解决方案主要包括以下过程：

- 步骤1：准备工作
    - 启动Amazon Braket服务
    - 创建QuickSight IAM角色
    - 注册QuickSight账户
    - 记录QuickSight用户名
- 步骤2：启动CloudFormation堆栈
- 步骤3：订阅SNS通知（可选）

## 步骤1：准备工作

### 启动Amazon Braket服务

1. 登录到AWS管理控制台，并找到Amazon Braket。

2. 打开Amazon Braket控制台，选中**I have read and accepted the above terms & conditions**。

3. 选择**Enable Amazon Braket**。

### 创建QuickSight IAM角色

1. 导航至[IAM Policies](https://console.aws.amazon.com/iamv2/home?#/policies)。

2. 点击**创建策略**。

3. 在创建策略页面，点击**JSON**，填写QuickSight策略如下，这是在本解决方案中，QuickSight能工作的最小权限。

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

4. 点击**下一步：标签**。

5. 点击**下一步：审核**。

6. 填写策略名称：`qradd-quicksight-service-role-policy`。

7. 点击 **创建策略**。

8. 导航至[IAM Roles](https://console.aws.amazon.com/iamv2/home?#/roles)。

9. 点击**创建角色**。

10. 选择**自定义信任策略**， 填写自定义信任策略如下：

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


11. 点击**下一步**。

12. 在权限策略搜索框中输入 `qradd-quicksight-service-role-policy`。

13. 选中策略`qradd-quicksight-service-role-policy`, 点击**下一步**。

14. 填写**角色名称**： `qradd-quicksight-service-role`。

15. 点击**创建角色**。

16. 记录所创建角色的名字。

### 注册QuickSight账户

!!! Caution 注意

    注册QuickSight账户需要您拥有正确的IAM权限。详情可参见[Signing up for an Amazon QuickSight subscription](https://docs.aws.amazon.com/quicksight/latest/user/signing-up.html)。

1. 登录到AWS管理控制台，并找到QuickSight。

2. 选择**企业版**，单击**继续**。

3. 在**创建您的 QuickSight 账户**页面，完成以下配置。

   - 选择**使用 IAM 联合身份和 QuickSight 托管的用户**。
   - 从QuickSight区域中选择**US East (N.Virginia)**。
   - 输入唯一的**QuickSight账户名称**。
   - 输入用于接收通知的**邮箱地址**。
   - 选择**使用现有角色**，在下拉列表中选择：`qradd-quicksight-service-role`。


!!! Caution 注意

    如果您的QuickSight已经注册并使用了默认的角色，需要到[QuickSight安全性和权限](https://us-east-1.quicksight.aws.amazon.com/sn/admin#aws)修改成上面创建的角色。
    这个操作可能会影响该QuickSight账户下的其他数据，请注意检查。修改QuickSight角色及其权限，您可以参考这个[文档](https://docs.aws.amazon.com/quicksight/latest/user/security_iam_service-with-iam.html#security-create-iam-role)。

### 记录QuickSight用户名

1. 登录[QuickSight管理用户页面](https://us-east-1.quicksight.aws.amazon.com/sn/admin)。

2. 记录对应您的电子邮件的**用户名**。

    !!! Caution 注意

        如果您的登录IAM用户不是注册QuickSight账户的用户时，您需要登录[QuickSight](https://quicksight.aws.amazon.com/)，并在页面中填写您的电子邮件地址。


## 步骤2：启动CloudFormation堆栈

1. 登录到AWS管理控制台，选择按钮[Launch Stack][template-url]以启动模板。您还可以选择直接下载模板进行部署。

2. 默认情况下，该模板将在您登录控制台后默认的区域启动，即美国东部（弗吉尼亚北部）区域。若需在指定的区域中启动该解决方案，请在控制台导航栏中的区域下拉列表中选择。

3. 在**创建堆栈**页面上，Amazon S3 URL文本框中会自动填写这个[模板URL][cf-template-url]，请确认模板URL正确填写，然后选择**下一步**。

4. 在**参数**部分，查看此解决方案模板的参数并根据需要进行修改。

5. 在**Parameters**部分，查看此解决方案模板的参数并根据需要进行修改。

    | 参数   | 描述 |
    |:-------------------|:----|
    | QuickSightUser | 输入QuickSight用户名，从页面[Manage users](https://us-east-1.quicksight.aws.amazon.com/sn/admin?#users)获取。 |
    | QuickSightRoleName | 输入QuickSight服务角色名字，从页面[Security & permissions](https://us-east-1.quicksight.aws.amazon.com/sn/admin?#aws)获取。 |

6. 选择**下一步**。

7. 在**配置堆栈选项**页面上，保留默认值并选择**下一步**。

8. 在**审核**页面，查看并确认设置。确保选中确认模板将创建Amazon Identity and Access Management（IAM）资源的复选框。选择**下一步**。

9. 选择**创建堆栈**以部署堆栈。

您可以在AWS CloudFormation控制台的**状态**列中查看stack的状态。正常情况下，大约10分钟内可以看到状态为**CREATE_COMPLETE**。

## 步骤3：订阅SNS通知（可选）

当批量评估执行完成后，如果您想获得Email通知，可以按照下面的步骤订阅SNS通知，您也可以通过[短信](https://docs.aws.amazon.com/sns/latest/dg/sns-mobile-phone-number-as-subscriber.html)订阅通知。

1. 在CloudFormation部署的输出中获取SNS主题的名字。

    ![SNS name](./images/deploy-output-sns.png)

2. 导航至[SNS 主题](https://console.aws.amazon.com/sns/v3/home?region=us-east-1#/topics)。

3. 点击在CloudFormation部署的输出中的SNS主题。

4. 选择**创建订阅**。

5. 在**协议**列表中，选择*电子邮件*。

6. 在**终端节点**文本框中，输入可以从Amazon SNS接收通知的电子邮件地址。

7. 选择**创建订阅**。

8. 检查您的邮箱，您将收到一封邮件，点击邮件中*Confirm Subscription*链接，确认订阅。

[template-url]: https://console.aws.amazon.com/cloudformation/home?region=us-west-2#/stacks/create/template?stackName=QRADDStack&templateURL=https://aws-gcr-solutions.s3.amazonaws.com/AWS-gcr-qc-life-science/v0.8.8/default/QCStack.template.json
[cf-template-url]: https://aws-gcr-solutions.s3.amazonaws.com/AWS-gcr-qc-life-science/v0.8.8/default/QCStack.template.json
