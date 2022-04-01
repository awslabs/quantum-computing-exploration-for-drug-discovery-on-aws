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
  aws_lambda as lambda,
} from 'aws-cdk-lib';

export enum ECRRepoNameEnum {
  Batch_Create_Model,
  Batch_Sa_Optimizer,
  Batch_Qa_Optimizer,
  Lambda_CheckDevice,
  Lambda_ParseBraketResult
};


export class ECRImageUtil {

  public static newInstance() {
    return new this();
  }

  private constructor() {
  }

  public getECRImage(name: ECRRepoNameEnum): ecs.ContainerImage | lambda.DockerImageCode {

    if (name == ECRRepoNameEnum.Batch_Create_Model) {
      return ecs.ContainerImage.fromAsset(
        path.join(__dirname, '../../'), {
          file: 'batch-images/create-model/Dockerfile',
        });
    }

    if (name == ECRRepoNameEnum.Batch_Sa_Optimizer) {
      return ecs.ContainerImage.fromAsset(
        path.join(__dirname, '../../'), {
          file: 'batch-images/sa-optimizer/Dockerfile',
        });
    }

    if (name == ECRRepoNameEnum.Batch_Qa_Optimizer) {
      return ecs.ContainerImage.fromAsset(
        path.join(__dirname, '../../'), {
          file: 'batch-images/qa-optimizer/Dockerfile',
        });
    }

    if (name == ECRRepoNameEnum.Lambda_CheckDevice) {
      return lambda.DockerImageCode.fromImageAsset(
        path.join(__dirname, '../../'), {
          file: 'lambda/DeviceAvailableCheckLambda/Dockerfile',
        });
    }

    if (name == ECRRepoNameEnum.Lambda_ParseBraketResult) {
      return lambda.DockerImageCode.fromImageAsset(
        path.join(__dirname, '../../'), {
          file: 'lambda/ParseBraketResultLambda/Dockerfile',
        });
    }

    throw new Error('Cannot find ecr: ' + name);
  }
}