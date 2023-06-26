You are responsible for the cost of AWS services used when running this solution. The actual cost depends on the tasks run and their complexity. As of this revision, the cost factors mainly consist of five types:

- Amazon Sagemaker Notebook
- Amazon S3
- Amazon Elastic Container Registry
- Amazon Braket Hybrid Jobs

If the customer only uses the notebook to explore the algorithm, the cost factors mainly involve the notebook and the computing from Amazon Braket task. If the customer evaluates different use cases with different parameters, the cost factors mainly involve the computing from Amazon Braket Hybrid Jobs.

<table border='1' style="text-align: center">
    <tr>
        <td><B>Service</td>
        <td><B>Resource</td>
        <td><B>Dimensions</td>
        <td><B>Cost</td>
    <tr>
    <tr>
        <td>Amazon Sagemaker Notebook</td>
        <td>ml.c5.xlarge</td>
        <td>long run instance</td>
        <td>$4.90 per day</td>
    <tr>
    <tr>
        <td>Amazon S3</td>
        <td>-</td>
        <td>< 1G</td>
        <td>$0.02</td>
    <tr>
    <tr>
        <td>Amazon Elastic Container Registry</td>
        <td>images for different use cases</td>
        <td>< 1G</td>
        <td>$0.02</td>
    <tr>
    <tr>
        <td rowspan="4">Amazon Braket Hybrid Jobs</td>
        <td>ml.m5.large runs and ml.m5.4xlarge (Molecular unfolding)</td>
        <td>one complete experiment consists of 12 jobs for different parameters, ml.m5.large runs for 44 minutes and ml.m5.4xlarge runs for 44 minutes in total</td>
        <td>$0.76 per complete experiment </td>
    <tr>
    <tr>
        <td>ml.m5.large runs and ml.m5.4xlarge (RNA unfolding)</td>
        <td>one complete experiment consists of 2 jobs for different parameters, ml.m5.large runs for 450 minutes and ml.m5.4xlarge runs for 429 minutes in total</td>
        <td>$7.46 per complete experiment </td>
    <tr>
    <tr>
        <td colspan='3'>Total Cost</td>
        <td>$13.16 per day</td>
    <tr>
</table>
