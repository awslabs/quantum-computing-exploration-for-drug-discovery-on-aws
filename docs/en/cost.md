You are responsible for the cost of Amazon cloud technology services used when running this solution. As of November 2021, the estimated cost for the solution 
is 25.12 USD per day.

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
 one complete batch test both on quantum computing resource and classical computing 
 resource in order to visualize the results in Amazon QuickSight. If the 
 customers only used solution to study the sample code, the cost for 
 notebook and the compute from Amazon Braket were considered.

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
        <td><B>Cost Type</B></td>
        <td><B>Service</td>
        <td><B>Resource Size</td>
        <td><B>Operating Condition</td>
        <td><B>Cost</td>
    <tr>
    <tr>
        <td>Notebook</td>
        <td>Amazon Sagemaker Notebook</td>
        <td>ml.c5.xlarge</td>
        <td>long run instance</td>
        <td>4.90 USD/Day</td>
    <tr>
    <tr>
        <td rowspan="16">Compute</td>
        <td>Amazon Braket</td>
        <td>D-Wave - DW_2000Q_6</td>
        <td>4 tasks for different parameters, 10000 shots/task</td>
        <td>8.8 USD</td>
    <tr>
    <tr>
        <td>Amazon Braket</td>
        <td>D-Wave - Advantage_system4.1</td>
        <td>4 tasks for different parameters, 10000 shots/task</td>
        <td>8.8 USD</td>
    <tr>
    <tr>
        <td>Amazon Batch (Fargate) </td>
        <td>2 VCPU 4G MEM</td>
        <td>Tasks like creating models, 8 minutes(< 20 minutes)</td>
        <td>1.02 USD</td>
    <tr>
    <tr>
        <td>Amazon Batch (EC2) </td>
        <td>2 VCPU 2G MEM</td>
        <td>4 tasks for different parameters, 19 minutes(< 60 minutes)</td>
        <td>0.09 USD</td>
    <tr>
    <tr>
        <td>Amazon Batch (EC2) </td>
        <td>4 VCPU 4G MEM</td>
        <td>4 tasks for different parameters, 19 minutes(< 60 minutes)</td>
        <td>0.17 USD</td>
    <tr>
    <tr>
        <td>Amazon Batch (EC2) </td>
        <td>8 VCPU 8G MEM</td>
        <td>4 tasks for different parameters, 19 minutes(< 60 minutes)</td>
        <td>0.34 USD</td>
    <tr>
    <tr>
        <td>Amazon Batch (EC2) </td>
        <td>16 VCPU 16G MEM</td>
        <td>4 tasks for different parameters, 19 minutes(< 60 minutes)</td>
        <td>0.68 USD</td>
    <tr>
    <tr>
        <td>AWS Lambda </td>
        <td>-</td>
        <td>< 100 queries</td>
        <td>0 USD</td>
    <tr>
    <tr>
        <td>Storage</td>
        <td>Amazon S3</td>
        <td>-</td>
        <td>< 1G</td>
        <td>0.02 USD</td>
    <tr>
    <tr>
        <td rowspan='4'>Analysis</td>
        <td>Amazon Athena</td>
        <td>-</td>
        <td>< 20 queries, 100M data</td>
        <td>0.029 USD</td>
    <tr>
    <tr>
        <td>Amazon QuickSight</td>
        <td>1 reader</td>
        <td>long run service</td>
        <td>8.00 USD/Month</td>
    <tr>
    <tr>
        <td>Orchestration</td>
        <td>AWS Step Functions</td>
        <td>-</td>
        <td>< 100 transitions</td>
        <td>0 USD</td>
    <tr>
    <tr>
        <td colspan='4'>Total Cost</td>
        <td>25.12 USD/Day</td>
    <tr>
</table>
