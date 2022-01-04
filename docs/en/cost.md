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
| Notebook | Amazon Sagemaker Notebook | ?? | long run instance | ?? |
| Compute | Amazon Braket | D-Wave 2000Q | 1 task, 10000 shots | ?? |
| Compute | Amazon Braket | D-Wave Advantage | 1 task, 10000 shots | ?? |
| Compute | Amazon Batch | ??| ?? minutes | ?? |
| Compute | Amazon Batch | ??| ?? minutes | ?? |
| Compute | Amazon Batch | ??| ?? minutes | ?? |
| Storage | Amazon S3 | ??| ??| ?? |
| Analysis | Amazon Athena | ??| ??| ?? |
| Analysis | Amazon QuickSight | ??| ??| ?? |
| Orchestration| AWS Step Functions | ??| ??| ?? |
| Orchestration| AWS Lambda| ??| ??| ?? |
