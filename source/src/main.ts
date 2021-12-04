import {
  App,
} from '@aws-cdk/core';
import {
  BootstraplessStackSynthesizer
} from 'cdk-bootstrapless-synthesizer';
import {
  MolUnfStack,
} from './molecule-unfolding/cdk/stack-main';

const app = new App();

new MolUnfStack(app, "QCStack", {
  synthesizer: newSynthesizer()
});

new MolUnfStack(app, "QCStack-test", {
  synthesizer: newSynthesizer()
});

app.synth();

function newSynthesizer() {
  return process.env.USE_BSS ? new BootstraplessStackSynthesizer() : undefined;
}