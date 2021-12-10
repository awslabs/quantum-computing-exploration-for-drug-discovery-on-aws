import {
    Stack,
    CfnParameter,
    CfnParameterProps,
} from '@aws-cdk/core';

export class SolutionStack extends Stack {
    private _paramGroup: {
        [grpname: string]: CfnParameter[]
    } = {}

    protected setDescription(description: string) {
        this.templateOptions.description = description;
    }
    protected newParam(id: string, props ? : CfnParameterProps): CfnParameter {
        return new CfnParameter(this, id, props);
    }
    protected addGroupParam(props: {
        [key: string]: CfnParameter[]
    }): void {
        for (const key of Object.keys(props)) {
            const params = props[key];
            this._paramGroup[key] = params.concat(this._paramGroup[key] ? this._paramGroup[key] : []);
        }
        this._setParamGroups();
    }
    private _setParamGroups(): void {
        if (!this.templateOptions.metadata) {
            this.templateOptions.metadata = {};
        }
        const mkgrp = (label: string, params: CfnParameter[]) => {
            return {
                Label: {
                    default: label
                },
                Parameters: params.map(p => {
                    return p ? p.logicalId : '';
                }).filter(id => id),
            };
        };
        this.templateOptions.metadata['AWS::CloudFormation::Interface'] = {
            ParameterGroups: Object.keys(this._paramGroup).map(key => mkgrp(key, this._paramGroup[key])),
        };
    }
}