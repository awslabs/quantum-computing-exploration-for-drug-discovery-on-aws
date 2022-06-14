
# Deploy From Source

## Regions

| Region Name | Region ID |
|----------|--------|
| US East (N. Virginia) | us-east-1 |
| US West (Oregon) | us-west-2 |
| Europe (London) | eu-west-2 |

## Deployment

Deploy solution to your AWS account by [AWS CDK](https://docs.aws.amazon.com/cdk/v2/guide/home.html).
### Prerequisites

- An AWS account
- Configure [credential of aws cli](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-quickstart.html)
- Install Node.js LTS version, such as 12.x
- Install Docker Engine
- Install the dependencies of solution via executing command `npm install`
- Initialize the CDK toolkit stack into AWS environment(only for deploying via AWS CDK first time, [doc](https://docs.aws.amazon.com/cdk/v2/guide/getting_started.html#getting_started_install))
    

### Deploy solution by AWS CDK
   

  * Run below command to deploy the Notebook and BatchEvaluation:

  ```sh
    cd source
    npx cdk deploy QCEDDStack
```

The output messages show status of the deployment, it takes approximately 10 minutes for the whole process.


If you want to deploy Visualization, you need to grant permissions in advance. For more information, see the section Grant permissions for Visualization in this [chapter](../docs/en/deployment.md).


   * Get your Amazon Quicksight [user name](https://us-east-1.quicksight.aws.amazon.com/sn/admin#)

   * Run below command to deploy Notebook, BatchEvaluation and Visualization:

```sh
    cd source
    npx cdk deploy QCEDDStack  \
      --parameters DeployNotebook=yes \
      --parameters DeployBatchEvaluation=yes \
      --parameters DeployVisualization=yes \
      --parameters QuickSightUser=<your QuickSight user>
```


## How to test

```sh
    cd source
    npm run test
```
