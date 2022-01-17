# Quantum Ready Solution For Drug Discovery

## Overview 

AWS Solution Quantum-Ready Solution for Drug Discovery (abbrev. QRSDDSolution), an open-sourced solution that helps customers study drug discovery problems using quantum computing (Amazon Braket), like molecular docking and protein folding. With QRSDD, customers use job management service (AWS Batch) and workflow service (AWS Step Functions) to orchestrate different kinds of computing resources. To be at the forefront of innovations in drug discovery, customers can tailor sample codes to reuse the pipeline for different problems.

The overall architecture is shown as below:

![architecture](./docs/en/images/architecture.png)

There are two types of Experiments of this solution: Batch test experiment and Notebook experiment.

### Batch Test Experiment:

1. User triggers the batch test execution through AWS Step Functions from AWS console.

1. The Step Functions parallel runs HPC tasks and QC tasks.

   - HPC tasks
      1. Step Functions synchronous parallel launches various HPC tasks through AWS batch jobs based on different resources (vcpu and memory) and different parameters of the algorithm.
      1. Batch jobs save result to S3.
      1. Step Functions continues to next step.
  
   - QC tasks
     1. Step Functions parallel launches various QC tasks through AWS lambda based on different QC devices (DW_2000Q_6/Advantage_system4) and different parameters of the algorithm.
     1. Each lambda asynchronous submits the QC task as AWS Braket job/task to AWS Braket service. 
     1. Step Functions waits for completion callback to continue.
     1. When a Braket job/task completed, it saves its result to S3.
     1. An event from AWS EventBridge triggers the listener lambda.
     1. The listener lambda sends a callback token to Step Functions.
     1. When Step Functions gets all callback tokens, it moves forward to next step.

1. An Athena table is created based on metrics data in S3.

1. A SNS notification is sent out when all HPC and QC tasks completed.

1. User views the batch test result through AWS Quicksight dashboard.

### Notebook Experiment:

This solution also deploys SageMaker notebooks, user can run and study backend algorithms for drug discovery in notebook. The code is step-by-step guide user to build models, run them by HPC and Braket service and post process the result. 

## Dataset

We use molecule data for this solution (source/src/molecule-unfolding/molecule-data/117_ideal.mol2). These data comes from the PDB protein data bank which is under [CC0 license](https://www.rcsb.org/pages/usage-policy). Please refer to the link for [117 mol file](https://www.rcsb.org/ligand/117)

## Quick start

### Sign up for QuickSight
   - Go to [quicksight](https://quicksight.aws.amazon.com/sn/start)
   - Click "Sign uup for QuickSight"
   - Choose `Enterprise`, click continue
   - In the `Create your QuickSight account` page, fill the necessary information:
   
   ![create quicksight](./docs/en/images/create_quicksight.png) 
   
   - Go to [quicksight admin](https://us-east-1.quicksight.aws.amazon.com/sn/admin), record your QuickSight username
   
   ![quicksight username](./docs/en/images/quicksight_username.png)    

### Update `cdk.context.json`

```shell
cd source

# edit cdk.context.json
# fill `quicksight_user` in previous step

```

### Deploy 

```shell
cd source

npm install
npm run deploy

```

### Deployment output

 After deployment, go to [cloudformation](https://console.aws.amazon.com/cloudformation/home), find the stack `QCStack`, from the output, you will get links for Notebook, Step Functions to run batch test tasks, and QuickSight dashboard URL

![cloudformation output](./docs/en/images/deploy_output.png)   


### Update QuickSight permissions

 - Go to [quicksight admin](https://us-east-1.quicksight.aws.amazon.com/sn/admin#aws) 
 - In `QuickSight access to AWS services`, click 'Manage' button, select the S3 bucket create in step `deployment output`

![quicksight permissions](./docs/en/images/quicksight_perm.png) 

 - Save the change 


### Run batch test through Step Functions

 -  open Step Functions link in `deployment output`
 -  click the **Start Execution** button, click **Start Execution** to execute the Step Functions workflow
 -  wait the execution of Step Functions to complete

### View batch test dashboard

 - open the QuickSight dashboard link in step `deployment output`

### Notebook experiment 

 - open the Notebook link in step `deployment output`



### More 
 - [Batch Test Experiment](./docs/en/workshop/a-molecule-unfolding/batch-test.md) 
 - [Notebook Experiment](./docs/en/notebook.md) 
 - [Workshop](./docs/en/workshop) 



## License
This project is licensed under the Apache-2.0 License.
