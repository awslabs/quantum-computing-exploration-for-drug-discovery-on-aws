When you build systems on AWS infrastructure, security responsibilities are shared between you and AWS. This [shared model](https://aws.amazon.com/compliance/shared-responsibility-model/) reduces your operational burden because AWS operates, manages, and controls the components including the host operating system, the virtualization layer, and the physical security of the facilities in which the services operate. For more information about AWS security, visit [AWS Cloud Security](http://aws.amazon.com/security/).

## Security best practices

QRADD is designed with security best practices in mind. However, the security of a solution differs based on your specific use case, and sometimes additional security measures will add to the cost of the solution. The following are recommendations to enhance the security posture of QRADD in production environments.

### IAM roles

AWS Identity and Access Management (IAM) roles allow customers to assign granular access policies and permissions to services and users on the AWS Cloud. This solution creates IAM roles that grant the solution’s access between the solution components.

### Security groups

The security groups created in this solution are designed to control and isolate network traffic between the solution components. We recommend that you review the security groups and further restrict access as needed once the deployment is up and running.

### Amazon Braket Security 

Refer to [Security in Amazon Braket](https://docs.aws.amazon.com/braket/latest/developerguide/security.html) to learn how to apply the shared responsibility model when using Amazon Braket.
