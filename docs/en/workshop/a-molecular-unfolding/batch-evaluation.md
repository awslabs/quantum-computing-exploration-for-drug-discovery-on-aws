# Run Default Batch Evaluation

We will run batch default evaluation through AWS Step Functions workflow and view the result via Amazon QuickSight dashboard.

1. Obtain Step Functions link from the CloudFormation output, and click the Step Functions link to navigate to AWS Step Functions console.

2. Click the **Start execution** button.

3. (Optional) Complete the evaluation input.

     - It will use default input if you do not enter anything.
     - If you want to customize the batch evaluation, please refer to the [Input specification](#input-specification) in this section.

4. Choose **Start execution** to start batch evaluation. The default batch evaluation will take about 15 minutes.

5. When the batch evaluation is completed, you can view the result in AWS QuickSight dashboard. Before that, you need to get the Dashboard link from the CloudFormation output.

6. You can choose to view the batch evaluation result **by Experiment**. 
    
    - **Experiments history**: displays all experiments history or displays the history by each experiment when you click each row.
    - **Task count**: shows the task count of all experiments or each experiment if you select an experiment in **Experiments hist** table.
    - **QC vs. CC average**: compares the average execution time (Y-axis) of QC (Quantum Computing) and CC (Classical Computing) tasks by different model parameters (X-axis).
    - **QC vs. CC by resource**: compares the execution time (Y-axis) of QC and CC tasks by different model parameters (X-axis) using different resources(for QC that is different QPU devices, for CC that is different memory-vCPU)
    - **QC by devices**: compares execution time (Y-axis) of different QPU devices by different model parameters (X-axis)
    - **CC by resources**: compares execution time (Y-axis) of different CC resources (memory and vCPU) by different model parameters (X-axis)
    - **Records**: lists the detailed information of each task in the selected experiment (if no experiment is selected, all will be listed)

        | Field  | Description  |
        |---|---|
        | compute_type  | Compute type, which can be CC or QC  |
        | resource  | Resource name. For QC, it refers to different QPU devices; for CC, it refers to different memory-vCPU  |
        | param  | Model parameters. </br>**M**: number of torsions; </br>**D**: angle precision of rotation; </br>**HQ**: hubo-qubo value, energy penalty; </br>**A**: penalty scalar |
        | opt_params  | Optimizer parameters  |
        | task_duration  | Task execution time in seconds  |
        | time_info | For QC, it refers to different dimensions of QC task time, and`total_time` is the **task_duration**; for CC, `local_time` is the **task_duration**  |
        | execution_id  | Step Functions execution ID |
        | experiment_name  | Experiment name. If `experimentName` input is not empty, it is `execution start time + input experimentName`. Otherwise, it is `execution start time + execution_id`  |
        | task_id  | For QC, it is Braket task id; for CC, it is empty |
        | result_detail  | Volume size of molecule before and after unfolding  |
        | result_location | Molecule mol2 file after unfolding  |
   

7. You can also switch the tab to view result **by Resource**.

    In this sheet, you can view batch evaluation result by each resource and QPU device.

    * Compute type and resource
    
        It lists all resources in batch evaluation. For QC, resources are QPU devices; for CC, resources are memory and vCPU. You can click each row to display the corresponding metrics. If no item is selected, it displays average metrics.

    * Experiment history
        
        It shows execution time (Y-axis) for selected resource by experiment name (X-axis, ordered by time) using different model parameters.

    * Records
    
        This table is the same as the table shown in the **by Experiment** tab.


### Input specification

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

  * **version**: version of input schema. Currently, it only supports value: '1'
  * **runMode**:  running mode. It has values `ALL`, `CC` or `QC`, and defaults to `ALL`. `CC` - only run CC tasks, `QC` only run QC tasks, `ALL` - run both tasks
  * **molFile**: S3 URL of the mol2 file
  * **modelVersion**: model version. By default, it is: 'latest'
  * **experimentName**: name of the batch evaluation
  * **optParams**: optimizer parameters, which is used to set shots for QC(qa) and CC(sa) tasks respectively
  * **modelParams**: model parameters, M: number of torsions, D: angle precision of rotation. Please refer to [Notebook Experiment](./notebook-experiment.md) for details.  Valid values: 

         M: [1, 2, 3, 4, 5, 6, 7]
         D: [4] or [8]

!!! Caution "Caution"

    The maximum value of M depends on the value of D, QPU device and input molFile. We set max M to 100 in input validation. If the value exceeds the device capacity in actual running, the execution will fail.
    
    If you use your own molFile, the input validation will be skipped; if the value exceeds the device capacity, the execution will fail. 
   
  * **devicesArns**: QPU device arn. Valid values:
  
        arn:aws:braket:::device/qpu/d-wave/DW_2000Q_6
        arn:aws:braket:::device/qpu/d-wave/Advantage_system4
      
  * **ccResources**: memory (first element) in GiB and vCPU (second element), for example, 4GiB memory and 2 vCPU is: `[4, 2]`


A typical (the default) input:

```json
{
    "version": "1",
    "runMode": "ALL",
    "optParams": {
        "qa": {
            "shots": 1000
        },
        "sa": {
            "shots": 1000
        }
    },
    "modelParams": {
        "M": [1, 2, 3, 4],
        "D": [4]
    },
    "devicesArns": [
        "arn:aws:braket:::device/qpu/d-wave/DW_2000Q_6",
        "arn:aws:braket:::device/qpu/d-wave/Advantage_system4"
    ],
    "ccResources": [
        [2, 2],
        [4, 4],
        [8, 8],
        [16, 16]
    ]
}
```
