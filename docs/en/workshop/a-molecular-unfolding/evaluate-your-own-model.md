# Batch Evaluate Your Own Model

This solution is an open-source project under Apache License Version 2.0. You can leverage it as your base code, and make changes on it. To fully customize the evaluation code, complete the following steps to make changes and re-deploy the whole stack from CDK.

## Prerequisites

1. Make sure you have AWS CLI and AWS CDK installed in your workspace. Refer to [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) to install AWS CLI. Follow this document [CDK Getting Started](https://docs.aws.amazon.com/cdk/v2/guide/getting_started.html#getting_started_prerequisites) to install and bootstrap CDK.

2. The user or IAM role to perform the deployment must have at least [permissions](./permissions.json).

3. Check the [preparations](../../deployment.md) made in the deployment.

4. Make sure you have docker running in your workspace. You can follow this document [Docker Install](https://docs.docker.com/engine/install/) to install docker.

## Customize evaluation code

1. Fork the GitHub repository of this solution to your own Git repository.

2. Clone the project to your own workspace.

3. Change `githubRepo` path in the source/src/molecular-unfolding/cdk/construct-notebook.ts file to be your Git repository. 

4. Make changes to source code. If you want to make changes for quantum algorithms, you can modify code under this directory **source/src/molecular-unfolding/utility**.

## Deploy stack to your AWS account from CDK

1. Check CloudFormation in your AWS account, and make sure you do not have a stack named `QCEDDStack` in your deployment region.

2. Check your S3 bucket, and make sure no bucket is named `amazon-braket-qceddstack-<your account>-<deployment Region>`.

3. Deploy changes to your AWS account from CDK.


        cd source
        npm install
        npx cdk deploy QCEDDStack  \
         --parameters DeployNotebook=yes \
         --parameters DeployBatchEvaluation=yes \
         --parameters DeployVisualization=yes \
         --parameters QuickSightUser=<your QuickSight user> \
         --parameters QuickSightRoleName=<your QuickSight service role name>
             
 
4. Wait for the deployment to complete. Deployment will take about 10 minutes. 

5. Get output links from CloudFormation output, which include:
    - Step Functions URL
    - QuickSight dashboard link
    - Notebook URL
    - S3 bucket name

6. Follow steps in Batch Evaluation to run your own code with appropriate input.

7. View result through QuickSight dashboard.
