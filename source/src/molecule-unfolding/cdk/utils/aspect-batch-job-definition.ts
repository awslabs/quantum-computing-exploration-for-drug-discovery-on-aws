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
    private _executionRole ? : iam.Role
    private _executionRoleArn ? : string
    private _allRolesMap: Map < string, iam.Role >

        constructor(props: ECRRepositoryAspectProps = {}) {
            super(props);
            this._repoNames = [];
            this._allRolesMap = new Map();
        }

    public visit(construct: IConstruct): void {
        if (construct instanceof batch.JobDefinition) {
            const stack = construct.stack
            this._executionRoleArn = ((construct.node.defaultChild as batch_lib.CfnJobDefinition).containerProperties as batch_lib.CfnJobDefinition.ContainerPropertiesProperty).executionRoleArn
            if (this._executionRoleArn && this._allRolesMap.get(this._executionRoleArn)) {
                this._executionRole = this._allRolesMap.get(this._executionRoleArn)
            }
            const image = ((construct.node.defaultChild as batch_lib.CfnJobDefinition).containerProperties as batch_lib.CfnJobDefinition.ContainerPropertiesProperty).image
            const image_resolved = stack.resolve(image)
            if (FN_SUB in image_resolved) {
                const repoName = this.getRepoName(image_resolved[FN_SUB]);
                if (repoName) {
                    if (this._executionRole) {
                        this._executionRole.attachInlinePolicy(this.crossAccountECRPolicy(stack, repoName));
                    } else {
                        if (this._repoNames.indexOf(repoName) < 0) {
                            this._repoNames.push(repoName)
                        }
                    }
                }
            }
        }
        if (construct instanceof iam.Role) {
            this._allRolesMap.set(construct.roleArn, construct)
            if (construct.roleArn == this._executionRoleArn) {
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
}