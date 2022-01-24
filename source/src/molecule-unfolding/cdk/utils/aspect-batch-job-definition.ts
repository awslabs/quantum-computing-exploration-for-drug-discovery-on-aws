import {
    aws_iam as iam
} from 'aws-cdk-lib'

import * as batch from '@aws-cdk/aws-batch-alpha'
import * as batch_lib from 'aws-cdk-lib/aws-batch'

import {
    IConstruct
} from 'constructs';

import {
    ECRRepositoryAspectProps,
    ECRRepositoryAspect,
} from 'cdk-bootstrapless-synthesizer';

const FN_SUB = 'Fn::Sub';

export class BatchJobDefinitionAspect extends ECRRepositoryAspect {
    readonly _repoNames: string[]
    _executionRole ? : iam.Role
    constructor(props: ECRRepositoryAspectProps = {}) {
        super(props);
        this._repoNames = []
    }

    public visit(construct: IConstruct): void {
        if (construct instanceof batch.JobDefinition) {
            const stack = construct.stack
            const image = ((construct.node.defaultChild as batch_lib.CfnJobDefinition).containerProperties as batch_lib.CfnJobDefinition.ContainerPropertiesProperty).image
            const image_resolved = stack.resolve(image)
            console.log("image_resolved: " + image_resolved)
            console.log(image_resolved)
            if (FN_SUB in image_resolved) {
                const repoName = this.getRepoName(image_resolved[FN_SUB]);
                if (repoName) {
                    if (this._executionRole) {
                        this._executionRole.attachInlinePolicy(this.crossAccountECRPolicy(stack, repoName));
                        console.log(this._executionRole.node.path)
                    } else {
                        this._repoNames.push(repoName)
                    }
                }
            }
        }
        if (construct instanceof iam.Role && construct.node.path.endsWith('/batchExecutionRole')) {
            const stack = construct.stack
            this._executionRole = construct
            while (this._repoNames.length > 0) {
                const repoName = this._repoNames.pop()
                if (repoName) {
                    this._executionRole.attachInlinePolicy(this.crossAccountECRPolicy(stack, repoName));
                }
            }
        }
    }
}