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

## File Structure

Upon successfully cloning the repository into your local development environment, you will see the following file structure in your editor:

```
├── CODE_OF_CONDUCT.md
├── CONTRIBUTING.md
├── LICENSE
├── NOTICE
├── README.md
├── docs
│   ├── en
│   ├── index.html
│   ├── mkdocs.base.yml
│   ├── mkdocs.en.yml
│   ├── mkdocs.zh.yml
│   └── zh
└── source
    ├── README.md
    ├── cdk.json
    ├── package-lock.json
    ├── package.json
    ├── src
    │   ├── main.ts
    │   ├── molecular-unfolding
    │   │   ├── batch-images
    │   │   │   ├── create-model
    │   │   │   │   ├── Dockerfile
    │   │   │   │   └── process.py
    │   │   │   ├── qa-optimizer
    │   │   │   │   ├── Dockerfile
    │   │   │   │   └── process.py
    │   │   │   └── sa-optimizer
    │   │   │       ├── Dockerfile
    │   │   │       └── process.py
    │   │   ├── cdk
    │   │   │   ├── construct-batch-evaluation.ts
    │   │   │   ├── construct-dashboard.ts
    │   │   │   ├── construct-listener.ts
    │   │   │   ├── construct-notebook.ts
    │   │   │   ├── resources
    │   │   │   │   └── onStart.template
    │   │   │   ├── stack-main.ts
    │   │   │   └── utils
    │   │   │       ├── custom-resource-lambda
    │   │   │       │   └── create-event-rule
    │   │   │       │       ├── index.ts
    │   │   │       │       └── template.json
    │   │   │       ├── custom-resource.ts
    │   │   │       ├── utils-batch.ts
    │   │   │       ├── utils-images.ts
    │   │   │       ├── utils-lambda.ts
    │   │   │       ├── utils-role.ts
    │   │   │       ├── utils.ts
    │   │   │       └── vpc.ts
    │   │   ├── input-template.json
    │   │   ├── lambda
    │   │   │   ├── AthenaTableLambda
    │   │   │   │   ├── index.js
    │   │   │   ├── DeviceAvailableCheckLambda
    │   │   │   │   ├── Dockerfile
    │   │   │   │   ├── app.py
    │   │   │   │   └── requirements.txt
    │   │   │   ├── ParseBraketResultLambda
    │   │   │   │   ├── Dockerfile
    │   │   │   │   └── app.py
    │   │   │   ├── TaskParametersLambda
    │   │   │   │   ├── app.py
    │   │   │   │   └── test_app.py
    │   │   │   └── WaitForTokenLambda
    │   │   │       └── app.py
    │   │   ├── molecular_unfolding.ipynb
    │   │   ├── molecule-data
    │   │   │   └── 117_ideal.mol2
    │   │   ├── pytest
    │   │   │   └── test_sample.py
    │   │   ├── requirements.txt
    │   │   └── utility
    │   │       ├── AnnealerOptimizer.py
    │   │       ├── GraphModel.py
    │   │       ├── MolGeoCalc.py
    │   │       ├── MoleculeParser.py
    │   │       ├── QMUQUBO.py
    │   │       ├── ResultProcess.py
    │   │       └── __init__.py
    │   └── stack.ts
    ├── test
    │   ├── benchmark.test.ts
    │   ├── dashboard.test.ts
    │   ├── listener.test.ts
    │   ├── main.test.ts
    │   ├── notebook.test.ts
    │   └── use_bss.test.ts
    ├── tsconfig.jest.json
    ├── tsconfig.json
    └── version.json
```
## Deploy From Source

Refer to [prerequisites and deployment](./source/README.md)

## Running Unit Tests

The `/source/run-all-tests.sh` script is the centralized script for running all unit, integration, and snapshot tests for both the CDK project as well as any associated Lambda functions or other source code packages.

```

cd ./source
chmod +x ./run-all-tests.sh
./run-all-tests.sh

```
***


## Collection of Operational Metrics
This solution collects anonymous operational metrics to help AWS improve the quality and features of the solution. For more information, including how to disable this capability, please see the [implementation guide](deep link into the documentation with specific information about the metrics and how to opt-out).

***

Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

Licensed under the Apache License Version 2.0 (the "License"). You may not use this file except in compliance with the License. A copy of the License is located at

    http://www.apache.org/licenses/

or in the "license" file accompanying this file. This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, express or implied. See the License for the specific language governing permissions and limitations under the License.
