This solution uses AWS CloudFormation to automate the deployment of the Quantum Computing Exploration for Drug Discovery on AWS with all associated components in the AWS Cloud. It includes the following CloudFormation template, which you can download before deployment:

 [QCEDDMain.template][cf-template-main-url]: Use this template to launch the solution and deploy notebook and batch evaluation. 
 The default configuration deploys [AWS SageMaker Notebook](https://docs.aws.amazon.com/sagemaker/latest/dg/nbi.html), [Amazon Braket](https://aws.amazon.com/braket/), [AWS Step Functions](https://aws.amazon.com/step-functions/), [AWS Batch](https://aws.amazon.com/batch/), [Amazon EventBridge](https://aws.amazon.com/eventbridge/), [AWS Lambda](https://aws.amazon.com/lambda/) and [Amazon Athena](https://aws.amazon.com/athena/), but you can customize the template to meet your specific needs.


 [QCEDDDashboard.template][cf-template-dashboard-url]: Use this template to deploy visualization. The default configuration deploys [Amazon QuickSight](https://aws.amazon.com/quicksight/), but you can customize the template to meet your specific needs.


[cf-template-main-url]: {{ cf_template.main_url }}

[cf-template-dashboard-url]: {{ cf_template.dashboard_url }}
