在部署解决方案之前，建议您先查看本指南中有关架构图和区域支持等信息。然后按照下面的说明配置解决方案并将其部署到您的帐户中。

**部署时间**：约12分钟

!!! Note "说明"

    建议您在部署此解决方案之前[创建账单告警](https://docs.aws.amazon.com/zh_cn/AmazonCloudWatch/latest/monitoring/monitor_estimated_charges_with_cloudwatch.html)以监控AWS估算费用。

本方案包含两个CloudFormation模版文件，主模版文件和可选的仪表盘模版文件。
主模版文件用来部署笔记本和批量评估，仪表盘模版文件用来部署可视化仪表盘，如果您不想通过仪表板查看批量评估结果，请跳过此模版文件部署，即使您现在没有部署仪表盘模版，您也可以在以后任意时间部署。

## 部署主堆栈
### 准备工作
#### 启动Amazon Braket服务

1. 登录到[AWS管理控制台](https://console.aws.amazon.com/)，并找到Amazon Braket。

2. 打开Amazon Braket控制台，选中**I have read and accepted the above terms & conditions**。

3. 选择**Enable Amazon Braket**。

### 步骤1：启动主CloudFormation堆栈

1. 登录AWS管理控制台，选择按钮[Launch Main Stack][template-main-url]以启动模板。您还可以选择直接[下载主模板][cf-template-main-url]进行部署。

2. 默认情况下，该模板将在您登录控制台后默认的区域启动，即美国西部（俄勒冈）区域。若需在指定的区域中启动该解决方案，请在控制台导航栏中的区域下拉列表中选择。

3. 在**创建堆栈**页面上，Amazon S3 URL文本框中会自动填写这个[主模板URL][cf-template-main-url]，请确认模板URL正确填写，然后选择**下一步**。

4. 在指定堆栈详细信息页面，为您的解决方案堆栈分配一个账户内唯一且符合命名要求的名称。有关命名字符限制的信息，请参阅*AWS Identity and Access Management用户指南*中的[IAM 和 STS 限制](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_iam-limits.html)。

5. 选择**下一步**。

6. 在**配置堆栈选项**页面上，保留默认值并选择**下一步**。

7. 在**审核**页面，查看并确认设置。确保选中确认模板将创建Amazon Identity and Access Management（IAM）资源的复选框。选择**下一步**。

8. 选择**创建堆栈**以部署堆栈。

您可以在AWS CloudFormation控制台的**状态**列中查看stack的状态。正常情况下，大约10分钟内可以看到状态为**CREATE_COMPLETE**。

### 步骤2：（可选）订阅SNS通知

当批量评估执行完成后，如果您想获得Email通知，可以按照下面的步骤订阅SNS通知。您也可以通过短信订阅通知。

1. 登录[AWS CloudFormation控制台](https://console.aws.amazon.com/cloudformation/)。

2. 在**堆栈**页面，选择本方案的堆栈。

3. 选择**输出**页签，记录SNS主题的值。

    ![SNS name](./images/deploy-output-sns.png)

4. 导航至[Amazon SNS控制台](https://console.aws.amazon.com/sns/v3/home?region=us-east-1#/topics)。

5. 选中**主题**，然后点击在CloudFormation部署的输出中的SNS主题。

6. 选择**创建订阅**。

7. 在**协议**列表中，选择**电子邮件**。

8. 在**终端节点**文本框中，输入可以从Amazon SNS接收通知的电子邮件地址。

9. 选择**创建订阅**。

10. 检查您的邮箱，您将收到一封邮件，点击邮件中*Confirm Subscription*链接，确认订阅。


## （可选）部署仪表盘堆栈
!!! Notice "说明"
    
    如果只想部署笔记本和批量评估，请跳过此步骤。如果想通过仪表盘查看批量评估结果，需要执行下面的步骤。

    即使现在跳过部署仪表盘堆栈，您也可以在以后任意时间执行下列步骤部署它。

### 准备工作

#### 创建QuickSight IAM角色

1. 导航至[IAM Policies](https://console.aws.amazon.com/iamv2/home?#/policies)。

2. 从左侧导航栏中选择**策略**，然后选择**创建策略**。该策略将被添加至新创建的IAM角色。

3. 在创建策略页面，点击**JSON**，填写QuickSight策略如下，这是本方案中QuickSight角色所需的最小权限。

        {
            "Version": "2012-10-17",
            "Statement": [
                {
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
                    "Resource": "*"
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "s3:GetObject",
                        "s3:ListBucket"
                    ],
                    "Resource": [
                        "arn:aws:s3:::amazon-braket-qcedd*"
                    ]
                }
            ]
        }

    
    !!! Note "说明"
        
        请忽略输入框下面的Errors提示。

4. 点击**下一步：标签**。

5. 点击**下一步：审核**。

6. 填写策略名称。本示例填入：`qcedd-quicksight-service-role-policy`。

7. 点击**创建策略**。

8. 导航至[IAM Roles](https://console.aws.amazon.com/iamv2/home?#/roles)。

9. 点击**创建角色**。

10. 选择**自定义信任策略**，填写自定义信任策略如下：

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

12. 在**权限策略**搜索框中输入刚刚创建的策略名称：`qcedd-quicksight-service-role-policy`。

13. 选中策略`qcedd-quicksight-service-role-policy`, 点击**下一步**。

14. 填写**角色名称**。本示例填入： `qcedd-quicksight-service-role`。

15. 点击**创建角色**。


#### 注册QuickSight账户

!!! Notice "说明"

    如果您的AWS账户已经注册了QuickSight账户，可以跳过该步骤。

1. 登录到[Amazon QuickSight控制台](https://quicksight.aws.amazon.com/)。

2. 选择**企业版**，点击**继续**。

3. 在**创建您的 QuickSight 账户**页面，完成以下配置。

    - 选择**使用 IAM 联合身份和 QuickSight 托管的用户**。
    - 从QuickSight区域中选择**美国东部（弗吉尼亚北部）区域**。无论您将本方案部署哪个区域，这里都选**美国东部（弗吉尼亚北部）区域**。
    - 输入唯一的**QuickSight账户名称**。
    - 输入用于接收通知的**邮箱地址**。
    - 对于其它参数，采用默认值。

#### 为QuickSight分配创建好的IAM角色

1. 登录到[Amazon QuickSight控制台](https://quicksight.aws.amazon.com/)。
2. 从区域下拉列表中选择**美国东部（弗吉尼亚北部）区域**。
3. 选中右上角的账户名称，点击**管理 QuickSight**。
4. 从左侧导航栏中选择**安全和权限**。
5. 在**QuickSight access to AWS services**区域中选中**管理**。
6. 选择**使用现有角色**，在下拉列表中选择刚刚创建的角色。本示例为`qradd-quicksight-service-role`。

#### 记录QuickSight用户名

1. 从美国东部（弗吉尼亚北部）区域登录[QuickSight管理用户页面](https://us-east-1.quicksight.aws.amazon.com/sn/admin)。

2. 记录右上角的对应您电子邮件的**用户名**。

### 启动仪表盘CloudFormation堆栈

1. 登录AWS管理控制台，选择按钮[Launch Dashboard Stack][template-dashboard-url]以启动模板。您还可以选择直接[下载仪表盘模板][cf-template-dashboard-url]进行部署。

2. 默认情况下，该模板将在您登录控制台后默认的区域启动，即美国西部（俄勒冈）区域。若需在指定的区域中启动该解决方案，请在控制台导航栏中的区域下拉列表中选择。

3. 在**创建堆栈**页面上，Amazon S3 URL文本框中会自动填写这个[仪表板模板URL][cf-template-dashboard-url]，请确认模板URL正确填写，然后选择**下一步**。

4. 在指定堆栈详细信息页面，为您的解决方案堆栈分配一个账户内唯一且符合命名要求的名称。有关命名字符限制的信息，请参阅*AWS Identity and Access Management用户指南*中的[IAM 和 STS 限制](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_iam-limits.html)。

5. 在**参数**部分，查看此解决方案模板的参数并根据需要进行修改。

    参数 | 默认值 | 描述 
    ---|---|---
    QuickSightUser | 无 | 输入QuickSight用户名，从页面[Manage users](https://us-east-1.quicksight.aws.amazon.com/sn/admin?#users)获取。

6. 选择**下一步**。

7. 在**配置堆栈选项**页面上，保留默认值并选择**下一步**。

8. 在**审核**页面，查看并确认设置。选择**下一步**。

9. 选择**创建堆栈**以部署堆栈。

您可以在AWS CloudFormation控制台的**状态**列中查看stack的状态。正常情况下，大约2分钟内可以看到状态为**CREATE_COMPLETE**。


[template-main-url]: https://console.aws.amazon.com/cloudformation/home?region=us-west-2#/stacks/create/template?stackName=QCEDDMain&templateURL={{ cf_template.main_url }}
[cf-template-main-url]: {{ cf_template.main_url }}

[template-dashboard-url]: https://console.aws.amazon.com/cloudformation/home?region=us-west-2#/stacks/create/template?stackName=QCEDDDashboard&templateURL={{ cf_template.dashboard_url }}
[cf-template-dashboard-url]: {{ cf_template.dashboard_url }}

