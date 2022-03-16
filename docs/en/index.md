Quantum Ready Architecture for Drug Discovery (QRADD) helps customers study drug discovery problems using quantum computing (Amazon Braket), such as molecular docking and protein folding. Customers can easily leverage this solution to orchestrate workflows that run on both classical and quantum as needed.

This solution mainly includes the following features:

- Launch a hybrid solution architecture with just one-click, including quantum computing and classical computing workflow
- Provide fully managed Jupyter Notebook, which is used to design and debug drug discovery algorithms
- Offer workflows based on [AWS Step Functions][step-functions] and [AWS Batch][batch], which is used to batch evaluate algorithm performance
- Display experiment results through BI services [Amazon Quicksight][quicksight]
- Allow customers to customize algorithms for other drug discovery problems and reuse them

Moreover, you can walk through the [workshop] (workshop/background.md) to learn quickly how to apply quantum computing to drug discovery problems. The workshop takes the molecular unfolding as an example to illustrate the background information, how to build model, optimize its configuration, and batch evaluate the experiment results. 

This implementation guide describes architectural considerations and configuration steps for deploying the quantum ready architecture for drug discovery 
in the Amazon Web Services (AWS) cloud. It includes links to [CloudFormation][cloudformation] templates that 
launches and configures the AWS services required to deploy this solution using AWS best practices for security and availability.

The guide is intended for IT architects, developers, DevOps, data scientists, algorithm engineers with architecture hands-on experience in the AWS Cloud, and technicians in the drug discovery field.

[cloudformation]: https://aws.amazon.com/cloudformation/
