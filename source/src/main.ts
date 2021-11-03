import {
  App,
} from '@aws-cdk/core';
import {
  BootstraplessStackSynthesizer
} from 'cdk-bootstrapless-synthesizer';
import {
  QCLifeScienceStack,
} from './ligand-unfolding/stack-main';

import {
  QCDashboradStack
} from './ligand-unfolding/stack-dashboard';


const app = new App();

new QCLifeScienceStack(app, "QCStack-main", {
  synthesizer: newSynthesizer()
});

new QCDashboradStack(app, "QCStack-dashboard", {
  synthesizer: newSynthesizer()
});

app.synth();

function newSynthesizer() {
  return process.env.USE_BSS ? new BootstraplessStackSynthesizer() : undefined;
}