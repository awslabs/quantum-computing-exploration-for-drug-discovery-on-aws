# Quantum Ready Architecture For Drug Discovery

## Overview

AWS Quantum Ready Architecture for Drug Discovery (abbrev. QRADD), an open-sourced solution customers can launch to design and run computational studies in the area of drug discovery, e.g. molecular docking and protein folding. With this solution, customers can design and load new, or existing algorithms, into Jupyter notebooks, then orchestrate the classical and quantum compute resources using AWS Batch and AWS Step Functions. Due to its design, customers are free to scale their classical simulations by launching a performant HPC resource instead of  a single EC2 instance. At the same time customer’s quantum experiments benefit from the growing number of quantum resources available through the Amazon Braket service.

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

## Pre-built Examples for Drug Discovery[<sup>1,</sup>](#more-example)[<sup>2</sup>](#data)
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
        <td><span>qbsolv</span></td>
        <td><span><span></td>
</table>

<div id='more-example'></div>
1.More examples to be added with continuous update
<div id='data'></div>
2.All the data in the solution follow the CC0 License



## License

This project is licensed under the Apache-2.0 License.
