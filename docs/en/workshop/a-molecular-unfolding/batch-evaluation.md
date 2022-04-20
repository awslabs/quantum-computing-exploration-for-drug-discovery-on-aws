# Run Default Batch Evaluation

The default batch evaluation runs a pre-built Amazon ECR Image that is based on the sample code in notebook experiments.

Run default batch evaluation through AWS Step Functions workflow and view the result via Amazon QuickSight dashboard.

1. Sign in to the [AWS CloudFormation console](https://console.aws.amazon.com/cloudformation/home?). 
2. On the **Stacks** page, select the solution’s root stack. 
3. Choose the **Outputs** tab and select the AWS Step Functions link.
4. Choose the **Start** button.
5. (Optional) Complete the evaluation input.

     - It will use default input if you do not enter anything.
     - If you want to customize the batch evaluation, refer to the [Input specification](#input-specification) in this section.

6. Choose **Start** to start batch evaluation. The default batch evaluation takes about 25 minutes.

7. When the batch evaluation is completed, you can view the result in AWS QuickSight dashboard. Before that, you need to go back to the **Outputs** tab and get the Dashboard link.

8. View the batch evaluation result in the dashboard. 
    
    - **Experiments history**: Displays all experiments history or displays the history by each experiment when select each row.
    - **Comparison of end to end time of the quantum solver with classical solver**: X-axis is complexity of the model, Y-axis is end-to-end time in seconds (if no experiment is selected, the time is average time).
    - **Comparison of running time of the quantum solver with classical solver**: X-axis is complexity of the model, Y-axis is running time in seconds (if no experiment is selected,  the time is average time). 
    - **Experiments data**: Lists the detailed information of each task in the selected experiment (if no experiment is selected, all will be listed).

        | Field  | Description  |
        |---|---|
        | compute_type  | Compute type, which can be CC or QC  |
        | complexity  | Complexity of the model, complexity = M * D  |
        | end_to_end_time  | End-to-end time in seconds |
        | running_time  | Running time in seconds  |
        | resource | Resource name. For QC, it refers to different QPU devices; for CC, it refers to different memory-vCPU  |
        | model_param  | Model parameters.</br> M: number of torsions;</br>D: angle precision of rotation;</br>HQ: hubo-qubo value, energy penalty; </br>A: penalty scalar|
        | opt_param  | Optimizer parameters |
        | time_info  | For QC, it refers to different dimensions of QC task time, and local_time is the end_to_end_time, total_time is the running_time; for CC, local_time is the end_to_end_time and running_time |
        | execution_id  | Step Functions run ID |
        | experiment_name  | Experiment name. If `experimentName` input is not empty, it is `execution start time + input experimentName`. Otherwise, it is `execution start time + execution_id`  |
        | result_detail  | Volume size of molecule before and after unfolding  |
        | result_location | Molecule mol2 file after unfolding  |

## Input specification

You can customize parameters of the evaluation by using a json input.

The input schema:

```json
{
    "version": "string",
    "runMode": "string",
    "molFile": "string",
    "modelVersion": "string",
    "experimentName": "string",
    "optParams": {
        "qa": {
            "shots": "int"
        },
        "sa": {
            "shots": "int"
        }
    },
    "modelParams": {
        "M": "int []",
        "D": "int []"
    },
    "devicesArns": "string []",
    "ccResources": "[int, int] []",
}

```

!!! notice "Note"

    All fields are optional.

Definition:

  * **version**: Version of input schema. Currently, it only supports value '1'.
  * **runMode**: Running mode. It has values `ALL`, `CC` or `QC`, and defaults to `ALL`. `CC` - only run CC tasks, `QC` only run QC tasks, `ALL` - run both tasks.
  * **molFile**: S3 URL of the mol2 file.
  * **modelVersion**: Model version. By default, it is 'latest'.
  * **experimentName**: Name of the batch evaluation.
  * **optParams**: Optimizer parameters, which is used to set shots for QC(qa) and CC(sa) tasks respectively.
  * **modelParams**: Model parameters. M: number of torsions, D: angle precision of rotation. Refer to [Build Model - Technical Details](./build-model-detail.md) for details. Valid values: 

         M: [1, 2, 3, 4, 5, 6, 7]
         D: [4] or [8]

    !!! Caution "Caution"

        The maximum value of M depends on the value of D, QPU device and input molFile. We set max M to 100 in input validation. If the value exceeds the device capacity in actual running, the run fails.
        
        If you use your own molFile, the input validation will be skipped; if the value exceeds the device capacity, the run fails. 
   
  * **devicesArns**: QPU device arn. Valid values:
  
        arn:aws:braket:::device/qpu/d-wave/DW_2000Q_6
        arn:aws:braket:::device/qpu/d-wave/Advantage_system4
      
  * **ccResources**: vCPU (first element) and memory (second element) in GiB, for example, 4 vCPU and 8 GiB memory is: `[4, 8]`


Example input with default mol2 file:

```json
{
    "version": "1",
    "runMode": "ALL",
    "optParams": {
        "qa": {
            "shots": 10000
        },
        "sa": {
            "shots": 10000
        }
    },
    "modelParams": {
        "M": [1, 2, 3, 4, 5],
        "D": [8]
    },
    "devicesArns": [
        "arn:aws:braket:::device/qpu/d-wave/DW_2000Q_6",
        "arn:aws:braket:::device/qpu/d-wave/Advantage_system4"
    ],
    "ccResources": [
        [4, 8],
    ]
}
```
If you have your own mol2 file, do the following:

1.	Upload your mol2 file to the S3 bucket in CloudFormation output, or your own S3 bucket. If you want to use your own S3 bucket, the bucket name must be in the format of: braket-* or amazon-braket-*.

2. Specify S3 uri of your mol2 file as the value of molFile in the Step Functions input:

```
{
    "molFile" : "<s3 uri of your mol2 file>"
}
```

For example:

```
{
   "molFile": "s3://amazon-braket-gcr-qc-sol-common/qc/raw_model/117_ideal.mol2"
}
```
