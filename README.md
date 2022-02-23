# Quantum Ready Solution For Drug Discovery (beta)

## Overview

AWS Quantum-Ready Solution for Drug Discovery (abbrev. QRSDDSolution), an open-sourced solution that helps customers study drug discovery problems using quantum computing (Amazon Braket), like molecular docking and protein folding. With QRSDD, customers use job management service (AWS Batch) and workflow service (AWS Step Functions) to orchestrate different kinds of computing resources. To be at the forefront of innovations in drug discovery, customers can tailor sample codes to reuse the pipeline for different problems.

The overall architecture is shown as below:

![architecture](./docs/en/images/architecture.png)

This solution deploys the Amazon CloudFormation template in your 
AWS Cloud account and provides three URLs. One for **Visualization**.
The others provide user with two approaches to study drug discovery 
problems: **Notebook Experiment** and **Batch Evaluation**:

* Notebook Experiment

The solution deploys the notebook for user to study different drug discovery 
problems. 
These problems will be studied using classical computing or quantum 
computing.

* Batch Evaluation

The solution provides user the way to evaluate a particular problem based 
on different computing resources , classical computing or quantum computing. 
For example, for the problem of molecular unfolding, the performance difference 
between quantum annealer and simulated annealer can be compared.

* Visualization

The solution provides user the way to visualize the comparing results of 
batch evaluation (e.g. performance, time)

For detailed description of architecture, please refer to the 
[Architecture Page](https://awslabs.github.io/quantum-ready-solution-for-drug-discovery/en/architecture/)

## Drug Discovery Problems
<table border='1' style="text-align: center">
    <tr>
        <td><B>Problem Name</B></td>
        <td><B>Methods</td>
        <td colspan='2'><B>Function</td>
        <td><B>Dataset</td>
        <td><B>Reference</td>
    <tr>
    <tr>
        <td rowspan='4'>Molecular Unfolding </td>
        <td rowspan='4'>QUBO</td>
        <td><span>single solver</span></td>
        <td><span>&#10004;</span></td>
        <td rowspan='4'><a href="https://www.rcsb.org/ligand/117">117 mol2</a></td>
        <td rowspan='4'><a href="https://arxiv.org/abs/2107.13607">Quantum Molecular Unfolding(2021)</a></td>
    <tr>
    <tr>
        <td><span>hybrid solver</span></td>
        <td><span><span></td>
</table>
All the data in the solution follow the CC0 License



## License

This project is licensed under the Apache-2.0 License.
