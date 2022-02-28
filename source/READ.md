
# How to deploy the solution

## Regions

| Region Name | Region ID |
|----------|--------|
| US East (N. Virginia) | us-east-1
| US West (Oregon) | us-west-2

## Deploy from source

Deploy solution to your AWS account by [AWS CDK](https://docs.aws.amazon.com/cdk/v2/guide/home.html).
### Prerequisites

- An AWS account
- Configure [credential of aws cli](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-quickstart.html)
- Install Node.js LTS version, such as 12.x
- Install Docker Engine
- Install the dependencies of solution via executing command `npm install`
- Initialize the CDK toolkit stack into AWS environment(only for deploying via AWS CDK first time, [doc](https://docs.aws.amazon.com/cdk/v2/guide/getting_started.html#getting_started_install))
- Enable Amazon Quicksight account in your AWS account([doc](https://docs.aws.amazon.com/quicksight/latest/user/signing-in.html))

### Deploy solution by AWS CDK
   
   * Get your Amazon Quicksight [user name](https://us-east-1.quicksight.aws.amazon.com/sn/admin#)

   * Run below command to deploy the solution.

```sh
    cd source
    cdk deploy QCStack --parameters quickSightUser=<your QuickSight user>
```

The output messages show status of the deployment, it takes approximately 10 minutes for the whole process.

## How to test

```sh
    cd source
    npm run test
```
