/*
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/


import * as path from 'path';
import {
  aws_ecs as ecs,
  aws_ecr as ecr,
  aws_lambda as lambda,
  Stack,
} from 'aws-cdk-lib';

import {
  Construct,
} from 'constructs';

export enum ECRRepoNameEnum {
  Batch_Create_Model,
  Batch_Sa_Optimizer,
  Batch_Qa_Optimizer,
  Lambda_CheckDevice,
  Lambda_ParseBraketResult
};


export class ECRImageUtil {
  public static newInstance(scope: Construct) {
    return new this(scope);
  }

  private scope: Construct

  private constructor(scope: Construct) {
    this.scope = scope;
  }

  public getECRImage(name: ECRRepoNameEnum): ecs.ContainerImage | lambda.DockerImageCode {

    const runningGlobalPipeline = process.env.SOLUTIONS_BUILD_ASSETS_BUCKET &&
      process.env.SOLUTIONS_BUILD_ASSETS_BUCKET == 'solutions-build-assets';
    const version = process.env.SOLUTION_VERSION || 'v1.0.0';
    const commitId = process.env.GIT_COMMIT_ID || '';
    const region = Stack.of(this.scope).region;
    const ecrAccount = process.env.SOLUTIONS_ECR_ACCOUNT || '366590864501';
    const repoName = 'aws-gcr-qc-life-science';

    if (name == ECRRepoNameEnum.Batch_Create_Model) {

      if (runningGlobalPipeline) {
        return ecs.ContainerImage.fromEcrRepository(ecr.Repository.fromRepositoryAttributes(this.scope, 'Batch_Create_Model', {
          repositoryName: `${repoName}`,
          repositoryArn: `arn:aws:ecr:${region}:${ecrAccount}:repository/${repoName}`,
        }), `${version}-${commitId}Batch_Create_Model`.toLowerCase());
      } else {
        return ecs.ContainerImage.fromAsset(
          path.join(__dirname, '../../'), {
            file: 'batch-images/create-model/Dockerfile',
          });
      }
    }

    if (name == ECRRepoNameEnum.Batch_Sa_Optimizer) {
      if (runningGlobalPipeline) {
        return ecs.ContainerImage.fromEcrRepository(ecr.Repository.fromRepositoryAttributes(this.scope, 'Batch_Sa_Optimizer', {
          repositoryName: `${repoName}`,
          repositoryArn: `arn:aws:ecr:${region}:${ecrAccount}:repository/${repoName}`,
        }), `${version}-${commitId}Batch_Sa_Optimizer`.toLowerCase());
      } else {

        return ecs.ContainerImage.fromAsset(
          path.join(__dirname, '../../'), {
            file: 'batch-images/sa-optimizer/Dockerfile',
          });

      }
    }

    if (name == ECRRepoNameEnum.Batch_Qa_Optimizer) {
      if (runningGlobalPipeline) {
        return ecs.ContainerImage.fromEcrRepository(ecr.Repository.fromRepositoryAttributes(this.scope, 'Batch_Qa_Optimizer', {
          repositoryName: `${repoName}`,
          repositoryArn: `arn:aws:ecr:${region}:${ecrAccount}:repository/${repoName}`,
        }), `${version}-${commitId}Batch_Qa_Optimizer`.toLowerCase());
      } else {
        return ecs.ContainerImage.fromAsset(
          path.join(__dirname, '../../'), {
            file: 'batch-images/qa-optimizer/Dockerfile',
          });
      }
    }

    if (name == ECRRepoNameEnum.Lambda_CheckDevice) {
      if (runningGlobalPipeline) {
        return lambda.DockerImageCode.fromEcr(ecr.Repository.fromRepositoryAttributes(this.scope, 'Lambda_CheckDevice', {
          repositoryName: `${repoName}`,
          repositoryArn: `arn:aws:ecr:${region}:${ecrAccount}:repository/${repoName}`,
        }), {
          tag: `${version}-${commitId}Lambda_CheckDevice`.toLowerCase(),
        });
      } else {
        return lambda.DockerImageCode.fromImageAsset(
          path.join(__dirname, '../../'), {
            file: 'lambda/DeviceAvailableCheckLambda/Dockerfile',
          });
      }
    }

    if (name == ECRRepoNameEnum.Lambda_ParseBraketResult) {
      if (runningGlobalPipeline) {
        return lambda.DockerImageCode.fromEcr(ecr.Repository.fromRepositoryAttributes(this.scope, 'Lambda_ParseBraketResult', {
          repositoryName: `${repoName}`,
          repositoryArn: `arn:aws:ecr:${region}:${ecrAccount}:repository/${repoName}`,
        }), {
          tag: `${version}-${commitId}Lambda_ParseBraketResult`.toLowerCase(),
        });
      } else {
        return lambda.DockerImageCode.fromImageAsset(
          path.join(__dirname, '../../'), {
            file: 'lambda/ParseBraketResultLambda/Dockerfile',
          });
      }
    }

    throw new Error('Cannot find ecr: ' + name);
  }
}