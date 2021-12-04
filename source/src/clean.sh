#!/usr/bin/env bash
set -e 

if [[ -z $REGION ]]; then
  REGION='us-east-1'
fi

AWS_CMD="aws"
if [[ -n $PROFILE ]]; then
  AWS_CMD="aws --profile $PROFILE"
fi

echo ""
echo "Please confirm below information:"

echo "    repoName: $repoName"
echo "    REGION: $REGION"
echo "    AWS_CMD: $AWS_CMD"
echo ""

repo_names=(
molecule-unfolding/create-model
molecule-unfolding/lambda-device-available-check
molecule-unfolding/lambda-parse-braket-result
molecule-unfolding/lambda-submit-qc-task
molecule-unfolding/sa-optimizer
)

for name in ${repo_names[@]}; do 
  echo "delete $name ..."
  $AWS_CMD ecr delete-repository  \
  --repository-name $name \
  --force \
  --region $REGION > /dev/null 2>&1 || true 
done 
