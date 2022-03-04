在部署解决方案之前，建议您先查看本指南中有关架构图和区域支持等信息。然后按照下面的说明配置解决方案并将其部署到您的帐户中。

**部署时间**：约10分钟


## 部署概述
在亚马逊云科技上部署本解决方案主要包括以下过程：

- 步骤1：检查您的QuickSight账户
- 步骤2：在您的亚马逊云科技账户中启动Amazon CloudFormation模板。
- 步骤3：更新您的QuickSight权限

!!! 注意

    在初次部署时，每个帐户只需进行一次步骤1和步骤3。重复部署时不必这样做

## 部署步骤

### 步骤1: 检查您的QuickSight账户


* 登录到AWS控制台，并找到[QuickSight](https://quicksight.aws.amazon.com/)

* 如果您还没有QuickSight账户，您需要先注册一个（您需要管理员权限注册QuickSight账户，[参考文档](https://docs.aws.amazon.com/quicksight/latest/user/setting-up-create-iam-user.html))。

* 选择 **Enterprise**，点击 continue。

* 在 **Create your QuickSight account** 页面填写必要的信息:

<center>
![Fill information for quicksight](./images/create_quicksight.png)

图 1: 在Quicksight填写信息

</center>

* 进入[quicksight admin](https://us-east-1.quicksight.aws.amazon.com/sn/admin), 并记录您的**QuickSight Username**(不是QuickSight account name).

<center>
![quicksight username](./images/quicksight_username.png)

图 2: Quicksight用户名

</center>

### 步骤2: 部署您的解决方案

我们将AWS CloudFormation的模板部署在了AWS Cloud上。

* 点此通过 AWS CloudFormation模板来[部署解决方案][template-url]。
 
* 模板默认使用US West(Oregon) 启动. 如果想要更换启动模板的 AWS Region, 请在控制台的导航栏中使用 Region selector进行更改。

* 在**Parameters**下方, 检查模板的参数并将其设置为necessary。解决方案采用已下的参数值. 选择 **Next**.

<center>

| 参数   | 描述 |
|:-------------------:|:----:|
| QuickSightUser | **QuickSight Username** |

</center>
    

* 在 **Configure stack options** 页面中, 选择 **Next**.
   
* 在 **Review** 页面中，检查并确认设置。 检查 box acknowledging 确保模板将会创建AWS Identity和Access Management (IAM)资源.

* 选择 **Create stack** 来部署stack.

您可以在AWS CloudFormation控制台中**Status**栏中查看stack的状态。您在大约十分钟内应该看到CREATE_COMPLETE的状态。


### 步骤3: 更新QuickSight的权限

* 定位到Quicksight [admin page](https://us-east-1.quicksight.aws.amazon.com/sn/admin#aws)

* 点击 **Manage**

<center>
![mange quicksight](./images/manage_quicksight.png)

图 3: 管理quicksight

</center>

* 点击**Select S3 Buckets**

<center>
![select s3 quicksight](./images/select_s3_bucket.png)

图 4: 在quicksight里检查s3

</center>

* 检查S3桶 `amazon-braket-qcstack-<AWS account>-<region>`

<center>
![choose s3 quicksight](./images/choose_s3_bucket.png)

图 5: 在quicksight里选择s3

</center>

* 点击 **Finish** 并选择 **Save**


[template-url]: https://console.aws.amazon.com/cloudformation/home?region=us-west-2#/stacks/create/template?stackName=QRADDStack&templateURL=https://aws-gcr-solutions.s3.amazonaws.com/AWS-gcr-qc-life-science/v0.8.2/default/QCStack.template.json