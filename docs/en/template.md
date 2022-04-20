This solution uses AWS CloudFormation to automate the deployment of the Quantum Ready Architecture for Drug Discovery with all associated components in the AWS Cloud. It includes the following CloudFormation template, which you can download before deployment:

 [quantum-ready-architecture-for-drug-discovery.template][cf-template-url]: Use this template to launch the solution and all associated components. 
 The default configuration deploys [AWS SageMaker Notebook](https://docs.aws.amazon.com/sagemaker/latest/dg/nbi.html), [Amazon Braket](https://aws.amazon.com/braket/), [AWS Step Functions](https://aws.amazon.com/step-functions/), [AWS Batch](https://aws.amazon.com/batch/), [Amazon EventBridge](https://aws.amazon.com/eventbridge/), [AWS Lambda](https://aws.amazon.com/lambda/), [Amazon Athena](https://aws.amazon.com/athena/) and [Amazon QuickSight](https://aws.amazon.com/quicksight/), but you can customize the template to meet your specific needs.


[cf-template-url]: {{ cf_template.url }}