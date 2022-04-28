部署解决方案之前，您可以下载解决方案使用的以下亚马逊云科技CloudFormation模板。

 [QCEDDMain.template][cf-template-main-url]：使用此模板启动解决方案和部署笔记本、批量评估组件。默认配置部署[AWS SageMaker Notebook](https://docs.aws.amazon.com/sagemaker/latest/dg/nbi.html)、[Amazon S3](https://aws.amazon.com/s3/)、[AWS Identity and Access Management(IAM)](https://aws.amazon.com/iam/)、[Amazon Virtual Private Cloud(Amazon VPC)](https://aws.amazon.com/vpc/)、[Amazon Braket](https://aws.amazon.com/braket/)、[AWS Step Functions](https://aws.amazon.com/step-functions/)、[AWS Batch](https://aws.amazon.com/batch/)、[Amazon EventBridge](https://aws.amazon.com/eventbridge/)、[AWS Lambda](https://aws.amazon.com/lambda/)和[Amazon Athena](https://aws.amazon.com/athena/)，但您可以自定义模板以满足您的特定需求。


 [QCEDDDashboard.template][cf-template-dashboard-url]：使用此模板部署可视化仪表盘。 默认配置部署[Amazon QuickSight](https://aws.amazon.com/quicksight/)，但您可以自定义模板以满足您的特定需求。


[cf-template-main-url]: {{ cf_template.main_url }}

[cf-template-dashboard-url]: {{ cf_template.dashboard_url }}
