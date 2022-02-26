When you build systems on AWS infrastructure, security responsibilities are shared between you and AWS. This [shared model](https://aws.amazon.com/compliance/shared-responsibility-model/) reduces your operational burden because AWS operates, manages, and controls the components including the host operating system, the virtualization layer, and the physical security of the facilities in which the services operate. For more information about AWS security, visit [AWS Cloud Security](http://aws.amazon.com/security/).

## Security best practices

AWS QRSDD is designed with security best practices in mind. However, the security of a solution differs based on your specific use case, and sometimes adding additional security measures will add to the cost of the solution. Th following are additional recommendations to enhance the security posture of AWS QRSDD in production environments.

### IAM roles

AWS Identity and Access Management (IAM) roles allow customers to assign granular access policies and permissions to services and users on the AWS Cloud. This solution creates IAM roles that grant the solution’s access between the solution components.

### Security groups

The security groups created in this solution are designed to control and isolate network traffic between the solution components. We recommend that you review the security groups and further restrict access as needed once the deployment is up and running.

### Data protection

For data protection purposes, we recommend that you protect AWS account credentials and set up individual user accounts with AWS Identity and Access Management (IAM). That way, each user is given only the permissions necessary to fulfill their job duties. We also recommend that you secure your data in the following ways:

* Use multi-factor authentication (MFA) with each account.

* Use SSL/TLS to communicate with AWS resources. We recommend TLS 1.2 or later.

* Set up API and user activity logging with AWS CloudTrail.

* Use AWS encryption solutions, along with all default security controls within AWS services.

* Use advanced managed security services such as Amazon Macie, which assists in discovering and securing personal data that is stored in Amazon S3.

If you require FIPS 140-2 validated cryptographic modules when accessing AWS through a command line interface or an API, use a FIPS endpoint. For more information about the available FIPS endpoints, see Federal Information Processing Standard (FIPS) 140-2.

### [Data retention](https://docs.aws.amazon.com/braket/latest/developerguide/security.html)

After 90 days, Amazon Braket automatically removes all task IDs and other metadata associated with your tasks. As a result of this data retention policy, these tasks and results are no longer retrievable by search from the Amazon Braket console, although they remain stored in your S3 bucket.

If you need access to historical tasks and results that are stored in your S3 bucket for longer than 90 days, you must keep a separate record of your task ID and other metadata associated with that data. Be sure to save the information prior to 90 days. You can use that saved information to retrieve the historical data.