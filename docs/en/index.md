Quantum Computing Exploration for Drug Discovery on AWS (QCEDD) helps you study drug discovery problems using quantum computing (Amazon Braket), such as molecular docking and protein folding. You can use this solution to orchestrate workflows that run on both classical and quantum as needed, thus accelerating iteration and innovation.

This solution includes the following features:

- A hybrid solution architecture that deploys with just one-click, including quantum computing and classical computing workflows.
- A fully managed Jupyter Notebook, which can be used to design and debug drug discovery algorithms.
- Workflows based on [AWS Step Functions][step-functions] and [AWS Batch][batch], which can be used to batch evaluate algorithm performance.
- [Amazon QuickSight][quicksight] to display the evaluation results.
- Ability to customize algorithms for other drug discovery problems and reuse them.

This implementation guide includes a [workshop](workshop/background.md) for you to walk through the solution. The workshop takes molecular unfolding algorithm from Mato, Kevin, et al.[<sup>1</sup>](#original-author) as an example to illustrate the background information, how to build a model, optimize its configuration, and batch evaluate the experiment results.

This implementation guide describes architectural considerations and configuration steps for deploying the Quantum Computing Exploration for Drug Discovery on AWS in the Amazon Web Services (AWS) cloud. It includes links to [CloudFormation][cloudformation] templates that 
launches and configures the AWS services required to deploy this solution using AWS best practices for security and availability.

The guide is intended for researchers, data scientists, algorithm engineers in the drug discovery field and quantum computing advocates with architecture hands-on experience in the AWS Cloud.

# Reference
<div id='original-author'></div>
 
 - 1.Mato, Kevin, et al. "Quantum Molecular Unfolding." arXiv preprint arXiv:2107.13607 (2021).

[braket]: https://aws.amazon.com/braket/
[step-functions]: https://aws.amazon.com/step-functions/
[batch]: https://aws.amazon.com/batch/
[quicksight]: https://aws.amazon.com/quicksight/
[cloudformation]: https://aws.amazon.com/en/cloudformation/
