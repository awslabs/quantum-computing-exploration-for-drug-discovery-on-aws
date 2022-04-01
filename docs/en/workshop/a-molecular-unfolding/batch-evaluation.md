# Run Default Batch Evaluation

We will run default batch evaluation through AWS Step Functions workflow and view the result via Amazon QuickSight dashboard.

1. Obtain AWS Step Functions link from the CloudFormation output, and click the link to navigate to AWS Step Functions console.

2. Click the **Start execution** button.

3. (Optional) Complete the evaluation input.

     - It will use default input if you do not enter anything.
     - If you want to customize the batch evaluation, please refer to the [Input specification](#input-specification) in this section.

4. Choose **Start execution** to start batch evaluation. The default batch evaluation will take about 25 minutes.

5. When the batch evaluation is completed, you can view the result in AWS QuickSight dashboard. Before that, you need to get the Dashboard link from the CloudFormation output.

6. View the batch evaluation result in the dashboard: 
    
    - **Experiments history**: displays all experiments history or displays the history by each experiment when you click each row.
    - Comparison of **end to end time** of the quantum design algorithm with classical algorithm: X-axis is complexity of the model, Y-axis is end to end time in seconds(if no experiment is selected, the time is average time). 
    - Comparison of **running time** of the quantum design algorithm by D-Wave resolvers: X-axis is complexity of the model, Y-axis is running time in seconds(if no experiment is selected,  the time is average time). 
    - **Experiments data**: lists the detailed information of each task in the selected experiment (if no experiment is selected, all will be listed)
    
        | Field  | Description  |
        |---|---|
        | compute_type  | Compute type, which can be CC or QC  |
        | complexity  | Complexity of the model,  complexity = M * D |
        | end_to_end_time  | End to end time in seconds  |
        | running_time  | Running time in seconds |
        | resource  | Resource name. For QC, it refers to different QPU devices; for CC, it refers to different memory-vCPU  |
        | model_param  | Model parameters. </br>**M**: number of torsions; </br>**D**: angle precision of rotation; </br>**HQ**: hubo-qubo value, energy penalty; </br>**A**: penalty scalar |
        | opt_param  | Optimizer parameters  |
        | time_info | For QC, it refers to different dimensions of QC task time, and `local_time` is the **end_to_end_time**，  `total_time` is the **running_time**; for CC, `local_time` is the **end_to_end_time** and **running_time** |
        | execution_id  | Step Functions execution ID |
        | experiment_name  | Experiment name. If `experimentName` input is not empty, it is `execution start time + input experimentName`. Otherwise, it is `execution start time + execution_id`  |
        | result_detail  | Volume size of molecule before and after unfolding  |
        | result_location | Molecule mol2 file after unfolding  |
   


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
      
  * **ccResources**: vCPU (first element) and memory (second element) in GiB and , for example, 4 vCPU and 8GiB memory is: `[4, 8]`


A typical (the default) input:

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
        [4, 8]
    ]
}
```
