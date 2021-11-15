import {
  App,
} from '@aws-cdk/core';
import {
  BootstraplessStackSynthesizer
} from 'cdk-bootstrapless-synthesizer';
import {
  MolUnfStack,
} from './molecule-unfolding/cdk/stack-main';

import {
  MolUnfDashboardStack
} from './molecule-unfolding/cdk/stack-dashboard';


const app = new App();

new MolUnfStack(app, "QCStack-main", {
  synthesizer: newSynthesizer()
});

new MolUnfDashboardStack(app, "QCStack-dashboard", {
  synthesizer: newSynthesizer()
});

app.synth();

function newSynthesizer() {
  return process.env.USE_BSS ? new BootstraplessStackSynthesizer() : undefined;
}