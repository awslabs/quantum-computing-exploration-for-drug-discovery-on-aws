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

    const usePreBuildImages = process.env.SOLUTION_PRE_BUILD_IMAGES || false;

    if (name == ECRRepoNameEnum.Batch_Create_Model) {
      if (usePreBuildImages) {
        return this.getECRRepository('Batch_Create_Model', 'batch');
      } else {
        return ecs.ContainerImage.fromAsset(
          path.join(__dirname, '../../'), {
            file: 'batch-images/create-model/Dockerfile',
          });
      }
    }

    if (name == ECRRepoNameEnum.Batch_Sa_Optimizer) {
      if (usePreBuildImages) {
        return this.getECRRepository('Batch_Sa_Optimizer', 'batch');
      } else {
        return ecs.ContainerImage.fromAsset(
          path.join(__dirname, '../../'), {
            file: 'batch-images/sa-optimizer/Dockerfile',
          });

      }
    }

    if (name == ECRRepoNameEnum.Batch_Qa_Optimizer) {
      if (usePreBuildImages) {
        return this.getECRRepository('Batch_Qa_Optimizer', 'batch');
      } else {
        return ecs.ContainerImage.fromAsset(
          path.join(__dirname, '../../'), {
            file: 'batch-images/qa-optimizer/Dockerfile',
          });
      }
    }

    if (name == ECRRepoNameEnum.Lambda_CheckDevice) {
      if (usePreBuildImages) {
        return this.getECRRepository('Lambda_CheckDevice', 'lambda');
      } else {
        return lambda.DockerImageCode.fromImageAsset(
          path.join(__dirname, '../../'), {
            file: 'lambda/DeviceAvailableCheckLambda/Dockerfile',
          });
      }
    }

    if (name == ECRRepoNameEnum.Lambda_ParseBraketResult) {
      if (usePreBuildImages) {
        return this.getECRRepository('Lambda_ParseBraketResult', 'lambda');
      } else {
        return lambda.DockerImageCode.fromImageAsset(
          path.join(__dirname, '../../'), {
            file: 'lambda/ParseBraketResultLambda/Dockerfile',
          });
      }
    }
    throw new Error('Cannot find ecr: ' + name);
  }

  private getECRRepository(name: string, type: string): ecs.ContainerImage | lambda.DockerImageCode {

    const ecrAccount = process.env.SOLUTION_ECR_ACCOUNT || '';
    const repoName = process.env.SOLUTION_ECR_REPO_NAME || '';
    const version = process.env.SOLUTION_VERSION || 'v1.0.0';
    const imagePrefix = process.env.IMAGE_PREFIX || '';
    const tag = `${version}-${imagePrefix}${name}`;
    const region = Stack.of(this.scope).region;

    if (type == 'lambda') {
      return lambda.DockerImageCode.fromEcr(ecr.Repository.fromRepositoryAttributes(this.scope, name, {
        repositoryName: `${repoName}`,
        repositoryArn: `arn:aws:ecr:${region}:${ecrAccount}:repository/${repoName}`,
      }), {
        tag,
      });
    } else if (type == 'batch') {
      return ecs.ContainerImage.fromEcrRepository(ecr.Repository.fromRepositoryAttributes(this.scope, name, {
        repositoryName: `${repoName}`,
        repositoryArn: `arn:aws:ecr:${region}:${ecrAccount}:repository/${repoName}`,
      }), tag);
    } else {
      throw new Error('getECRRepository unknown type ' + type);
    }

  }
}