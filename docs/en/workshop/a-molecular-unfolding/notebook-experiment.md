## Notebook experimentation

The workshop implements the work from [Quantum Molecular Unfolding](https://arxiv.org/abs/2107.13607), and the [Molecular Unfolding with Quantum Annealing](https://www.youtube.com/watch?v=1NmAXIHAF2Y) video in Amazon Braket.

## Molecular docking 

Molecular Docking (MD) is an important step of the drug discovery process which aims at calculating the preferred position and shape of one molecule to a second when they are bound to each other. This step focuses on computationally simulating the molecular recognition process. It aims to achieve an optimized conformation for both the protein and ligand and relative orientation between protein and ligand such that the free energy of the overall system is minimized. 

In this work, the protein or the pocket is considered as a rigid structure, and the ligand is considered as a 
flexible set of atoms.

![Molecular Docking](../../images/molecule-docking.png)

Figure 6: Molecular docking[<sup>6</sup>](#wiki-docking)

As described in [Quantum Molecular Unfolding](https://arxiv.org/abs/2107.13607), published by Mato et al, there are usually three main phases in MD: 

1. Expansion of the ligand to an unfolded shape, to reduce bias, that is, molecular unfolding (MU). MU includes:
    * Identification of the rotatable bonds
    * Internal distance maximization
    * Removal of tool related bias (for example, SMILES-to-3D)
2. Initial placement, which includes:
    * Ligand main fragments decomposition
    * Ligand initial poses identification
    * Placement of the ligand into the pocket with rigid roto-translations
3. Shape refinement, which includes:
    * Use of the rotatable bonds to modify the ligand shape and to match the protein pocket
    * Docking score maximization

## Quantum molecular unfolding on the AWS Cloud

Here we focus on the first phase of MD, ligand expansion, which aims to reduce shape bias that may affect the final quality of docking.  In this solution we use the quantum annealing approach to molecular unfolding (MU) as published by Mato et al. Our solution uses AWS Services to execute this problem on quantum computing hardware, available through AWS Braket. The solution also allows the problem to be run on classic computing hardware, on AWS, for comparison.

## Notebook overview

1. Sign in to the [AWS CloudFormation console](https://console.aws.amazon.com/cloudformation/home?). 
2. On the **Stacks** page, select the solution’s root stack. 
3. Choose the **Outputs** tab and open the link for your notebook.

    ![deployment output](../../images/deploy_output_notebook.png)

    Figure 7: Notebook URL on the stack's Output tab

4. Navigate through the notebook, which consists of four Steps:

    - Step 1: Prepare data - Prepare molecular data for experiments.
    - Step 2: Build model - Build model for molecular unfolding.
    - Step 3: Optimize configuration - Run optimization to find the configuration.
    - Step 4: Process results - Process the results for evaluation and visualization.




# References
<div id='wiki-docking'></div>

- [Wiki: Molecular Docking](https://en.wikipedia.org/wiki/Docking_(molecular))
