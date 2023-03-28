## Protein Folding using Variational Quantum Eigensolver (VQE)

Protein folding has been one of the most interesting areas of study since 1960 and is one of the hardest problem to solve in biochemistry. Proteins are made of long chains of amino acids that are present in all living organism. They have varying range of functions from providing physical structures to allow muscles to grow and bend. Protein folds distinctively, and with varying chains of amino acids it becomes more difficult and complex to find protein's stable structure. 

Researchers at IBM have developed a quantum algorithm to demonstrate how quantum computing can help improve these computations to find protein structures more efficiently. In this notebook, we will demonstrate how to use Variational Quantum Eigensolver (VQE) algorithm using Qiskit Nature to predict protein structures. We will demonstrate how we can run this algorithm on Amazon Braket using Amazon Braket's hybrid jobs. 

## How to run:
Use provided `vqe_protein_folding.ipynb` notebook to run protein folding solution either locally or as an Amazon Braket job.

1. Using notebook, build docker image and register docker image into an ECR repository. 
2. Update cell with hyperparameters to update amino acid chain, optimizer, penalty parameters, etc. 
3. Run job either locally or on Amazon Braket. To run on a quantum hardware, update ARN for `q_device` variable to a quantum hardware ARN. 


### Citations

```
Qiskit: An Open-source Framework for Quantum Computing. (2021). doi:10.5281/zenodo.2573505
```