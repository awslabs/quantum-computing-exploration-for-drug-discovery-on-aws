
We are trying to implement the work from the publication [Quantum Molecular Unfolding](https://arxiv.org/abs/2107.13607)
and video [Molecular Unfolding with Quantum Annealing](https://www.youtube.com/watch?v=1NmAXIHAF2Y) in Amazon Braket.

## Molecular Docking 

Molecular Docking (MD) is an important step of the drug discovery process which aims at calculating the preferred position and shape of one molecule to a second when they are bound to each other. This step focuses on computationally simulating the molecular recognition process. It aims to achieve an optimized conformation for both the protein and ligand and relative orientation between protein and ligand such that the free energy of the overall system is minimized. 

In this work, the protein or the pocket is considered as a rigid structure, and the ligand is considered as a 
flexible set of atoms.

![Molecular Docking](../../images/molecule-docking.png)

Figure 1: Molecular docking[<sup>1</sup>](#wiki-docking)

According to the publication [Quantum Molecular Unfolding](https://arxiv.org/abs/2107.13607), there are usually three main phases in MD: 

* Ligand expansion
    * Identification of the rotatable bonds
    * Internal distances maximization
    * Remove tool related bias (e.g. smile-to-3D)
* Initial Placement
    * Ligand main fragments decomposition
    * Ligand initial poses identification
    * Placement of the ligand into the pocket with rigid roto-translations
* Shape Refinement
    * Use of the rotatable bonds to modify the ligand shape and to match the protein pocket
    * Docking score maximization

In this work, actually the first phase, ligand expansion or the molecular unfolding (MU), is focused and implemented using quantum annealer. This phase is important for improving docking. In fact, an initial pose of the ligand that is set a priori may introduce shape bias affecting the final quality of the docking. MU is the technology used for removing such initial bias.

# Notebook Overview

1. Access the deployment output page in your cloudformation and open the link for your notebook.

    ![deployment output](../../images/deploy_output_notebook.png)

    Figure 2: The notebook link in the output of cloudformation


2. Open the notebook (**source/src/molecular-folding/molecular_unfolding.ipynb**) and make sure that the kernel for this notebook is **qcenv**.

3. Navigate through the notebook, which consists of four Steps:


    |Steps|Contents|
    |:--|:--|
    |Step1: Prepare Data|prepare molecular data for experiments|
    |Step2: Build Model|build model for molecular unfolding|
    |Step3: Optimize Configuration|run optimization to find the configuration|
    |Step4: PostProcess Results |post process the results for evaluation and visualization|



# References
<div id='wiki-docking'></div>
- 1.[Wiki: Molecular Docking](https://en.wikipedia.org/wiki/Docking_(molecular))
