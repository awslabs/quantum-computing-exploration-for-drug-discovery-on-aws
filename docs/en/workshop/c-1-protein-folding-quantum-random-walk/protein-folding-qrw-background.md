## Notebook experimentation

This notebook implements the [QFold: quantum walk and deep learning to solve protein folding](https://iopscience.iop.org/article/10.1088/2058-9565/ac4f2f) in
 Amazon Braket. This is mainly contributed by [Roberto Campos](https://github.com/roberCO) based on his [implementation](https://iopscience.iop.org/article/10.1088/2058-9565/ac4f2f)

## Protein folding using quantum walk

Protein folding is the process by which a protein molecule assumes its three-dimensional shape, which is essential for its proper function. Proteins are made up of a linear chain of amino acids, and their final structure is determined by the sequence of amino acids and the interactions between them.

During protein folding, the linear chain of amino acids folds into a unique three-dimensional structure, which is stabilized by various types of interactions, such as hydrogen bonds, electrostatic forces, and van der Waals forces. The process of protein folding is highly complex and involves multiple stages, including the formation of secondary structures, such as alpha-helices and beta-sheets, and the packing of these structures into a final three-dimensional shape.

![Protein](../../images/protein-folding.png)

Figure 10: Protein before and after folding[<sup>8</sup>](#wiki-protein)

In this work, the quantum walks are applied 
to a Metropolis algorithm in order to predict how proteins fold in 3D.
Quantum walks are quantum analogues of classical random walks. In contrast to the classical random walk, where the walker occupies definite states and the randomness arises due to stochastic transitions between states, in quantum walks randomness arises through: (1) quantum superposition of states, (2) non-random, reversible unitary evolution and (3) collapse of the wave function due to state measurements. This is named as Qfold in the original paper.

![Qfold](../../images/qfold.png)

Figure 11: Scheme of the QFold algorithm[<sup>9</sup>](#qfold)



## Notebook overview

1. Sign in to the [AWS CloudFormation console](https://console.aws.amazon.com/cloudformation/home?). 
2. On the **Stacks** page, select the solution’s root stack. 
3. Choose the **Outputs** tab and open the link for your notebook.

    ![deployment output](../../images/deploy_output_notebook.png)

    Figure 12: Notebook URL on the stack's Output tab

4. Open
**healthcare-and-life-sciences/c-1-protein-folding-quantum-random-walk/protein-folding-qrw.ipynb** and choose the kernel
**qc_hcls_protein_folding_qrw**.

# References
<div id='wiki-protein'></div>

- 8.[Wiki: Protein](https://en.wikipedia.org/wiki/Protein_folding)

- 9.[QFold: Quantum Walks and Deep Learning to Solve Protein Folding](https://iopscience.iop.org/article/10.1088/2058-9565/ac4f2f)