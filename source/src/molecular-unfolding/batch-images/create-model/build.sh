#!/usr/bin/env bash
set -e 

repoName='molecular-unfolding/create-model'

rm -rf utility
rm -rf molecule-data

cp -r ../../utility . 
cp -r ../../molecule-data . 

docker build -t $repoName .

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

# echo "Press Enter to continue ..."
# read reply

create_repo () {
  name=$1
  region=$2

  echo "create_repo() - name: $name, region: $region"

  $AWS_CMD ecr create-repository  \
  --repository-name $name \
  --image-scanning-configuration scanOnPush=true \
  --region $region >/dev/null 2>&1 || true
}

create_repo $repoName $REGION

account_id=$($AWS_CMD sts get-caller-identity --query Account --output text)

account_ecr_uri=${account_id}.dkr.ecr.${REGION}.amazonaws.com

IMAGEURI=${account_ecr_uri}/$repoName:latest

docker tag $repoName ${IMAGEURI}

echo ${IMAGEURI}

$AWS_CMD ecr get-login-password --region ${REGION} | docker login --username AWS --password-stdin ${account_ecr_uri}

echo ">> push ${IMAGEURI}"

docker push ${IMAGEURI}
