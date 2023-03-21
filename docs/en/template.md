This solution uses AWS CloudFormation to automate the deployment of the Quantum Computing Exploration for Drug Discovery on AWS with all associated components in the AWS Cloud. It includes the following CloudFormation template, which you can download before deployment:

[quantum-computing-exploration-for-drug-discovery.template][cf-template-url]: Use this template to launch the solution and all associated components.
The default configuration deploys [AWS SageMaker Notebook](https://docs.aws.amazon.com/sagemaker/latest/dg/nbi.html), [Amazon Braket](https://aws.amazon.com/braket/), [AWS Identity and Access Management(IAM)](https://aws.amazon.com/iam/), [Amazon EventBridge](https://aws.amazon.com/eventbridge/), [AWS SNS](https://aws.amazon.com/lambda/), but you can customize the template to meet your specific needs.

[cf-template-url]: {{ cf_template.url }}
