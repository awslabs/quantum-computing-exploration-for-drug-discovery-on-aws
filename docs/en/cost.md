You are responsible for the cost of AWS services used when running this solution. The actual cost depends on the tasks run and their complexity. As of May 2023, the cost factors mainly consist of five types:

 * Notebook
 * Computing 
 * Storage

## Example 

This example uses the molecular unfolding function for the prepared sample, which is a ligand 117_idel.mol2 downloaded from [Protein Data Bank (PDB)](https://www.rcsb.org/downloads/ligands). Assuming a customer continues using the notebook to study use cases, and adopts the solution to run one complete batch evaluation both on quantum computing resource and classical computing resource in order to visualize the results in Amazon QuickSight, the cost for running this solution in US East (N. Virginia) Region is shown in the table below.

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
        <td rowspan="6">Computing</td>
        <td rowspan="6">Amazon Braket Hybrid Jobs</td>
        <td>ml.m5.large runs and ml.m5.4xlarge (Molecular unfolding)</td>
        <td>12 jobs for different parameters, ml.m5.large runs for 44 minutes and ml.m5.4xlarge runs for 44 minutes in total</td>
        <td>$0.76</td>
    <tr>
    <tr>
        <td>ml.m5.large runs and ml.m5.4xlarge (RNA unfolding)</td>
        <td>2 jobs for different parameters, ml.m5.large runs for 450 minutes and ml.m5.4xlarge runs for 429 minutes in total</td>
        <td>$7.46</td>
    <tr>
    <tr>
        <td>D-Wave - Advantage_system6.1</td>
        <td>4 tasks for different parameters, 10000 shots/task</td>
        <td>$8.80</td>
    <tr>
    <tr>
        <td>Storage</td>
        <td>Amazon S3</td>
        <td>-</td>
        <td>< 1G</td>
        <td>$0.02</td>
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
