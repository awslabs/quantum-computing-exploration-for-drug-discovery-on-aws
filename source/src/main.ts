import {
  App,
} from '@aws-cdk/core';
import {
  BootstraplessStackSynthesizer
} from 'cdk-bootstrapless-synthesizer';
import {
  MoleculeUnfoldingStack,
} from './molecule-unfolding/cdk/stack-main';

import {
  MoleculeUnfoldingDashboardStack
} from './molecule-unfolding/cdk/stack-dashboard';


const app = new App();

new MoleculeUnfoldingStack(app, "QCStack-main", {
  synthesizer: newSynthesizer()
});

new MoleculeUnfoldingDashboardStack(app, "QCStack-dashboard", {
  synthesizer: newSynthesizer()
});

app.synth();

function newSynthesizer() {
  return process.env.USE_BSS ? new BootstraplessStackSynthesizer() : undefined;
}