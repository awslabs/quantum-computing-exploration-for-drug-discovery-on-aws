import {
    aws_ecs as ecs
} from 'aws-cdk-lib'

import {
    aws_lambda as lambda
} from 'aws-cdk-lib'


import * as path from 'path'

export enum ECRRepoNameEnum {
    Batch_Create_Model,
    Batch_Sa_Optimizer,
    Batch_Qa_Optimizer,
    Lambda_CheckDevice,
    Lambda_ParseBraketResult
};


export class ECRImageUtil {

    private constructor() {
    }
    
    public static newInstance() {
        return new this();
    }

    public getECRImage(name: ECRRepoNameEnum): ecs.ContainerImage | lambda.DockerImageCode {

        if (name == ECRRepoNameEnum.Batch_Create_Model) {
            return ecs.ContainerImage.fromAsset(
                path.join(__dirname, '../../'), {
                    file: 'batch-images/create-model/Dockerfile',
                })
        }

        if (name == ECRRepoNameEnum.Batch_Sa_Optimizer) {
            return ecs.ContainerImage.fromAsset(
                path.join(__dirname, '../../'), {
                    file: 'batch-images/sa-optimizer/Dockerfile',
                })
        }

        if (name == ECRRepoNameEnum.Batch_Qa_Optimizer) {
            return ecs.ContainerImage.fromAsset(
                path.join(__dirname, '../../'), {
                    file: 'batch-images/qa-optimizer/Dockerfile',
                })
        }

        if (name == ECRRepoNameEnum.Lambda_CheckDevice) {
            return lambda.DockerImageCode.fromImageAsset(
                path.join(__dirname, '../../'), {
                    file: 'lambda/DeviceAvailableCheckLambda/Dockerfile',
                })
        }

        if (name == ECRRepoNameEnum.Lambda_ParseBraketResult) {
            return lambda.DockerImageCode.fromImageAsset(
                path.join(__dirname, '../../'), {
                    file: 'lambda/ParseBraketResultLambda/Dockerfile',
                });
        }

        throw new Error("Cannot find ecr: " + name);
    }
}