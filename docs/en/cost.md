You are responsible for the cost of AWS services used when running this solution. The actual cost depends on the tasks run and their complexity. As of May 2022, the cost factors mainly consist of five types:

 * Notebook
 * Computing 
 * Storage
 * Analysis
 * Orchestration

## Example 

This example uses the molecular unfolding function for the prepared sample, which is a ligand 117_idel.mol2 downloaded from [Protein Data Bank (PDB)](https://www.rcsb.org/downloads/ligands). Assuming a customer continues using the notebook to study use cases, and adopts the solution to run one complete batch evaluation both on quantum computing resource and classical computing resource in order to visualize the results in Amazon QuickSight, the cost for running this solution in US East (N. Virginia) Region is $28.21 per day.

!!! Notice "Note"
    
    If the customer uses the solution only to study the use cases, the cost factors mainly involve the Notebook and the Computing from Amazon Braket.

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
        <td>Amazon Braket</td>
        <td>D-Wave - Advantage_system6.1</td>
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
        <td>$37.01 per day</td>
    <tr>
</table>
