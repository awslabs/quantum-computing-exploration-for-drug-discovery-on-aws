You are responsible for the cost of Amazon cloud technology services used when running this solution. As of [November] 2021, the estimated cost for xx is xx.

The whole cost consists of five types:
 * Notebook
 * Compute 
 * Storage
 * Analysis
 * Orchestration

 The actual cost depends on the tasks performed and the complexity. Take 
 the molecule unfolding function for the prepared sample (117_idel.mol2) as 
 an example. The following calculation is based on that customers use 
 the notebook to study sample code as well as use the solution to run 
 the complete logic both on quantum computing resource and classical computing 
 resource in order to visualize the results in Amazon QuickSight. If the 
 customers only used solution to study the sample code, the cost for 
 notebook and the compute from Amazon Braket were considered.

| Cost Type| Service | Resource Size | Operating Condition | Cost |
| :---: | :---: | :---: | :---: | :---: |
| Notebook | Amazon Sagemaker Notebook | ml.c5.xlarge | long run instance | 4.90 USD/Day |
| Compute | Amazon Braket | D-Wave 2000Q | 4 task, 1000 shots/task | 1.96 USD |
| Compute | Amazon Braket | D-Wave Advantage | 4 task, 1000 shots/task | 1.96 USD |
| Compute | Amazon Batch (Fargate) | 2 vcpu 4G mem | less than 20 minutes | 1.02 USD |
| Compute | Amazon Batch (EC2) | c5.large| less than 60 minutes | 0.09 USD |
| Compute | Amazon Batch (EC2) | c5.xlarge| less than  60 minutes | 0.17 USD|
| Compute | Amazon Batch (EC2) | c5.2xlarge| less than  60 minutes | 0.34 USD |
| Compute | Amazon Batch (EC2) | c5.4xlarge| less than  60 minutes | 0.68 USD |
| Compute| AWS Lambda| - | less than 100 requests | 0 USD |
| Storage | Amazon S3 | - | less than 1G | 0.02 USD |
| Analysis | Amazon Athena | - | less than 20 queres,100M data | 0.29 USD |
| Analysis | Amazon QuickSight | - | 1 reader | 8.00 USD/Month |
| Orchestration| AWS Step Functions | - |  less than 100 transitions | 0 USD  |

