#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib';
import { SesBlogSolutionStack } from '../lib/ses-blog-solution-stack';


const app = new cdk.App();
new SesBlogSolutionStack(app, 'SesBlogSolutionStack', {
    //env: {account: '', region: 'eu-west-1'}
});