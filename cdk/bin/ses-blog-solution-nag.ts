#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { Aspects } from 'aws-cdk-lib';
import { SesBlogSolutionStack } from '../lib/ses-blog-solution-stack';
import { AwsSolutionsChecks } from 'cdk-nag';

const app = new cdk.App();
// Add the cdk-nag AwsSolutions Pack with extra verbose logging enabled.
Aspects.of(app).add(new AwsSolutionsChecks({ verbose: true }))
new SesBlogSolutionStack(app, 'SesBlogSolutionStack', {
    //env: {account: '', region: 'eu-west-1'}
});