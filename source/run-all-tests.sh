#!/bin/bash
#
# This script runs all tests for the root CDK project and Lambda functions.
# These include unit tests, integration tests, and snapshot tests.

[ "$DEBUG" == 'true' ] && set -x
set -e

source_dir="$PWD"


cd $source_dir

npm install 

echo "------------------------------------------------------------------------------"
echo "Starting Unit Test"
echo "------------------------------------------------------------------------------"
npm run test

echo "------------------------------------------------------------------------------"
echo "Unit tests complete"
echo "------------------------------------------------------------------------------"