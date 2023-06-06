## Notebook experimentation

This notebook implements the protein folding
using varionational quantum eigensolver (vqe).

## Protein folding using VQE

Protein folding is the process by which a protein molecule assumes its three-dimensional shape, which is essential for its proper function. Proteins are made up of a linear chain of amino acids, and their final structure is determined by the sequence of amino acids and the interactions between them.

During protein folding, the linear chain of amino acids folds into a unique three-dimensional structure, which is stabilized by various types of interactions, such as hydrogen bonds, electrostatic forces, and van der Waals forces. The process of protein folding is highly complex and involves multiple stages, including the formation of secondary structures, such as alpha-helices and beta-sheets, and the packing of these structures into a final three-dimensional shape.

![Protein](../../images/protein-folding.png)

Figure 16: Protein before and after folding[<sup>10</sup>](#wiki-protein)

VQE is a quantum algorithm that can be used 
to simulate the behavior of molecules, 
including proteins. VQE works by approximating 
the ground state energy of a molecule using 
a quantum computer, which can be used to 
predict the properties of the molecule.

To use VQE for protein folding, one would 
first need to encode the protein structure into a format that can be represented as a 
quantum state. This can be done using a 
technique called the qubitization method, 
which maps the protein structure onto a set of qubits that can be manipulated by the quantum computer.

## Notebook overview

1. Sign in to the [AWS CloudFormation console](https://console.aws.amazon.com/cloudformation/home?). 
2. On the **Stacks** page, select the solution’s root stack. 
3. Choose the **Outputs** tab and open the link for your notebook.

    ![deployment output](../../images/deploy_output_notebook.png)

    Figure 17: Notebook URL on the stack's Output tab

4. Open
**healthcare-and-life-sciences/c-3-protein-folding-variational-quantum-eigensolver/protein-folding-vqe.ipynb** and choose the kernel
**qc_hcls_protein_folding_vqe**.

# References
<div id='wiki-protein'></div>

- 10.[Wiki: Protein](https://en.wikipedia.org/wiki/Protein_folding)
