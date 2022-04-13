# Batch Evaluate Your Own Model

You have two options to batch evaluate your own model:

- Batch evaluate your own mol2 file without code changes
- Fully customize evaluation code

## Batch evaluate your own mol2 file without code changes

If you have your own mol2 file, follow below steps to batch evaluate it:

1. Upload your mol2 file to the S3 bucket in CloudFormation output, or your own S3 bucket. If you want to use your own S3 bucket, the bucket name must be in the format of:  `braket-*` or `amazon-braket-*`.
    
2. Specify S3 uri of your mol2 file as the value of `molFile` in the Step Functions input:

     
        {
            "molFile" : "<s3 uri of your mol2 file>"
        }
   

       For example,
    
        {
           "molFile": "s3://amazon-braket-gcr-qc-sol-common/qc/raw_model/117_ideal.mol2"
        }

    
    For the complete input parameters and schema, please refer to [input specification](../batch-evaluation/#input-specification).

3. Follow the steps in [Batch Evaluation](../batch-evaluation/#start-execution) to run the Step Functions.

## Fully customize evaluation code

This solution is an open source project under Apache License Version 2.0. You can leverage it as your base code, and make changes on it.

If you want to fully customize the evaluation code, follow below steps to make changes and re-deploy the whole stack from CDK.

### Prerequisites

1. Make sure you have AWS CLI and AWS CDK installed in your workspace. Refer to [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) to install AWS CLI. Follow this document [CDK Getting Started](https://docs.aws.amazon.com/cdk/v2/guide/getting_started.html#getting_started_prerequisites) to install and bootstrap CDK.

2. The user or IAM role to perform the deployment must have at least [permissions](./permissions.json).

3. Check the [preparations](../../deployment.md) made in the deployment.

4. Make sure you have docker running in your workspace. You can follow this document [Docker Install](https://docs.docker.com/engine/install/) to install docker.

### Customize evaluation code

1. Fork the github repository of this solution to your own git repository.

2. Clone the project to your own workspace.

3. Make changes to source code.

    !!! caution "Caution"
        
        The `githubRepo` in file `source/src/molecular-unfolding/cdk/construct-notebook.ts` should be changed to your repository.

### Deploy stack to your AWS account from CDK

1. Check CloudFormation in your AWS account, and make sure you do not have a stack named `QCStack` in your deployment region.

2. Check your S3 bucket, and make sure no bucket is named `amazon-braket-qcstack-<your aws account>-<deployment region>`.

3. Deploy changes to your AWS account from CDK.


        cd source
        npm install
        npx cdk deploy QCStack \
            --parameters QuickSightUser=<your QuickSight user> \
            --parameters QuickSightRoleName=<your QuickSight service role name>
             
 
4. Wait for the deployment to complete. Deployment will take about 10 minutes. 

5. Get output links from CloudFormation output, which include:
    - Step Functions URL
    - QuickSight Dashboard link
    - Notebook URL
    - S3 Bucket name

6. Follow steps in [Batch Evaluation](../batch-evaluation/) to run your own code with appropriate input.

7. [View result](../batch-evaluation/#view-dashboard) through QuickSight dashboard.
