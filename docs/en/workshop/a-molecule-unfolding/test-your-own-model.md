## Batch Test Your Own Model

You have two options to batch test your own model

- Batch test your own mol2 file with out code changes
- Fully customize the test code

## Batch test your own mol2 file with out code changes

If you have your own mol2 file, you want to batch test it, you can follow below steps:

1. Upload your mol2 file to a S3 bucket, bucket name must be `braket-*` or `amazon-braket-*`.

1. Specify S3 uri of your mol2 file as the value of `molFile` in the Step Functions input json 

    ```json
    {
        "molFile" : "<s3 uri of your mol2 file>"
    }   
    ```
    The full input parameters and schema, please refer to [batch test](./batch-test.md)
    
1. Then **Start Execution** the Step functions.


## Fully customize the test code


This solution is an open source project under Apache License Version 2.0. You can leverage it as your base code, make changes on it.

If you want to fully customize the test code, follow below steps to re-deploy the whole stack from CDK.

1. Fork the github repository of this solution to your own git repository.

1. Clone the project to your own workspace, make changes to the source code.

1. Update `quicksight_user` and `default_code_repository` in file `source/cdk.context.json`.

1. Check CloudFormation in your AWS account, make sure you do not have a stack named `QCStack` in your deployment region.

1. Make sure you have AWS CDK install in your workspace. 

    You can follow this doc [cdk getting_started](https://docs.aws.amazon.com/cdk/v2/guide/getting_started.html) to install and bootstrap CDK.

1. Make sure you have docker running in your workspace.

    You can follow this doc [docker install](https://docs.docker.com/engine/install/) to install docker.


1. Deploy changes to your AWS account via CDK.

   ```sh
   cd source

   npm run deploy

   ```
1. Wait for the deployment to complete.

1. Get output links from CloudFormation output, the links include:
   - Step Functions URL
   - QuickSight Dashboard link
   - Notebook URL

1. Run Step Functions via your custom parameters.

1. View result through QuickSight dashboard.





                           