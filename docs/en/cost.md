You are responsible for the cost of AWS services used when running this solution. The actual cost depends on the tasks run and their complexity. As of April 2022, the cost factors mainly consist of five types:

 * Notebook
 * Computing 
 * Storage
 * Analysis
 * Orchestration

## Example 

This example uses the molecular unfolding function for the prepared sample, which is a ligand 117_idel.mol2 downloaded from [Protein Data Bank (PDB)](https://www.rcsb.org/downloads/ligands). Assuming a customer continues using the notebook to study sample code, and adopts the solution to run one complete batch evaluation both on quantum computing resource and classical computing resource in order to visualize the results in Amazon QuickSight, the cost for running this solution in US East (N. Virginia) Region is $28.21 per day.

!!! Notice "Note"
    
    If the customer uses the solution only to study the sample code, the cost factors mainly involve the Notebook and the Computing from Amazon Braket.


<!-- | Cost Type| Service | Resource Size | Operating Condition | Cost |
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
| Total | xxx to do| -->

<table border='1' style="text-align: center">
    <tr>
        <td><B>Type</B></td>
        <td><B>Service</td>
        <td><B>Resource</td>
        <td><B>Dimensions</td>
        <td><B>Cost</td>
    <tr>
    <tr>
        <td>Notebook</td>
        <td>Amazon Sagemaker</td>
        <td>ml.c5.xlarge</td>
        <td>long run instance</td>
        <td>$4.90 per day</td>
    <tr>
    <tr>
        <td rowspan="9">Computing</td>
        <td>Amazon Braket</td>
        <td>D-Wave - DW_2000Q_6</td>
        <td>4 tasks for different parameters, 10000 shots/task</td>
        <td>$8.80</td>
    <tr>
    <tr>
        <td>Amazon Braket</td>
        <td>D-Wave - Advantage_system4.1</td>
        <td>4 tasks for different parameters, 10000 shots/task</td>
        <td>$8.80</td>
    <tr>
    <tr>
        <td>Amazon Batch (Fargate) </td>
        <td>2 VCPU 4G MEM</td>
        <td>Build model task, 8 minutes (< 20 minutes)</td>
        <td>$1.02</td>
    <tr>
    <tr>
        <td>Amazon Batch (EC2) </td>
        <td>4 VCPU 8G MEM</td>
        <td>4 tasks for different parameters, 25 minutes(< 60 minutes)</td>
        <td>$0.17</td>
    <tr>
    <tr>
        <td>AWS Lambda </td>
        <td>-</td>
        <td>< 100 queries</td>
        <td>$0</td>
    <tr>
    <tr>
        <td>Storage</td>
        <td>Amazon S3</td>
        <td>-</td>
        <td>< 1G</td>
        <td>$0.02</td>
    <tr>
    <tr>
        <td rowspan='4'>Analysis</td>
        <td>Amazon Athena</td>
        <td>-</td>
        <td>< 20 queries, 100M data</td>
        <td>$0.029</td>
    <tr>
    <tr>
        <td>Amazon QuickSight</td>
        <td>1 reader</td>
        <td>long run service</td>
        <td>$8.00 per month</td>
    <tr>
    <tr>
        <td>Orchestration</td>
        <td>AWS Step Functions</td>
        <td>-</td>
        <td>< 100 transitions</td>
        <td>$0</td>
    <tr>
    <tr>
        <td rowspan='4'>Network</td>
        <td>Amazon VPC</td>
        <td>Amazon S3</br>Amazon ECR</br>Amazon Athena</br>Amazon Braket</br>endpoints</td>
        <td>long run service</td>
        <td>$58.41 per month</td>
    <tr>
    <tr>
        <td>Amazon VPC</td>
        <td>NAT Gateway</td>
        <td>long run service</td>
        <td>$65.78 per month</td>
    <tr> 
    <tr>
        <td colspan='4'>Total Cost</td>
        <td>$28.21 per day</td>
    <tr>
</table>
