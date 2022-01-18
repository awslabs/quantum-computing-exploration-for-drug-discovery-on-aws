import {
    aws_ecr as ecr
} from 'aws-cdk-lib'

import {
    aws_ecs as ecs
} from 'aws-cdk-lib'

import {
    aws_lambda as lambda
} from 'aws-cdk-lib'

import {
    Construct
} from 'constructs'

import * as path from 'path'

export enum ECRRepoNameEnum {
    Batch_Create_Model,
    Batch_Sa_Optimizer,
    Batch_Qa_Optimizer,
    Lambda_CheckDevice,
    Lambda_ParseBraketResult
};

interface Props {
    usePreBuildImage: boolean;
    prefix: string;
    region: string;
    account: string;
}

export class ECRImageUtil {
    private props: Props
    private scope: Construct
    private ecr_account_id: string

    private constructor(scope: Construct, props: Props) {
        this.props = props
        this.scope = scope
        this.ecr_account_id = this.props.account
    }
    public static newInstance(scope: Construct, props: Props) {
        return new this(scope, props);
    }

    public getECRImage(name: ECRRepoNameEnum): ecs.ContainerImage | lambda.DockerImageCode {
        const usePreBuildImage = this.props.usePreBuildImage

        if (name == ECRRepoNameEnum.Batch_Create_Model) {
            if (usePreBuildImage) {
                return ecs.ContainerImage.fromEcrRepository(
                    ecr.Repository.fromRepositoryAttributes(this.scope, `create-model`, {
                        repositoryArn: `arn:aws:ecr:${this.props.region}:${this.ecr_account_id}:repository/${this.props.prefix}/create-model`,
                        repositoryName: `${this.props.prefix}/create-model`
                    })
                );
            }
            return ecs.ContainerImage.fromAsset(
                path.join(__dirname, '../../batch-images/create-model'))
        }

        if (name == ECRRepoNameEnum.Batch_Sa_Optimizer) {
            if (usePreBuildImage) {
                return ecs.ContainerImage.fromEcrRepository(
                    ecr.Repository.fromRepositoryAttributes(this.scope, 'sa-optimizer', {
                        repositoryArn: `arn:aws:ecr:${this.props.region}:${this.ecr_account_id}:repository/${this.props.prefix}/sa-optimizer`,
                        repositoryName: `${this.props.prefix}/sa-optimizer`
                    })
                );
            }

            return ecs.ContainerImage.fromAsset(
                path.join(__dirname, '../../batch-images/sa-optimizer'))
        }

        if (name == ECRRepoNameEnum.Batch_Qa_Optimizer) {
            if (usePreBuildImage) {
                return ecs.ContainerImage.fromEcrRepository(
                    ecr.Repository.fromRepositoryAttributes(this.scope, 'qa-optimizer', {
                        repositoryArn: `arn:aws:ecr:${this.props.region}:${this.ecr_account_id}:repository/${this.props.prefix}/qa-optimizer`,
                        repositoryName: `${this.props.prefix}/qa-optimizer`
                    })
                );
            }

            return ecs.ContainerImage.fromAsset(
                path.join(__dirname, '../../batch-images/qa-optimizer'))
        }

        if (name == ECRRepoNameEnum.Lambda_CheckDevice) {
            if (usePreBuildImage) {
                return lambda.DockerImageCode.fromEcr(
                    ecr.Repository.fromRepositoryAttributes(this.scope, 'lambda-device-available-check', {
                        repositoryArn: `arn:aws:ecr:${this.props.region}:${this.ecr_account_id}:repository/${this.props.prefix}/lambda-device-available-check`,
                        repositoryName: `${this.props.prefix}/lambda-device-available-check`
                    })
                );
            }
            return lambda.DockerImageCode.fromImageAsset(path.join(__dirname, '../../lambda/DeviceAvailableCheckLambda/'));
        }


        if (name == ECRRepoNameEnum.Lambda_ParseBraketResult) {
            if (usePreBuildImage) {
                return lambda.DockerImageCode.fromEcr(
                    ecr.Repository.fromRepositoryAttributes(this.scope, 'lambda-parse-braket-result', {
                        repositoryArn: `arn:aws:ecr:${this.props.region}:${this.ecr_account_id}:repository/${this.props.prefix}/lambda-parse-braket-result`,
                        repositoryName: `${this.props.prefix}/lambda-parse-braket-result`
                    })
                );
            }
            return lambda.DockerImageCode.fromImageAsset(path.join(__dirname, '../../lambda/ParseBraketResultLambda/'));
        }
        throw new Error("Cannot find ecr: " + name);
    }
}