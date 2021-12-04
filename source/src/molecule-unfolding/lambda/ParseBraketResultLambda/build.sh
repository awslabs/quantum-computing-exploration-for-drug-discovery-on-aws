#!/usr/bin/env bash
set -e 

repoName='molecule-unfolding/lambda-parse-braket-result'
rm -rf utility

cp -r ../../utility . 

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
  public_access=$3

  echo "create_repo() - name: $name, region: $region, public_access: $public_access"

  $AWS_CMD ecr create-repository  \
  --repository-name $name \
  --image-scanning-configuration scanOnPush=true \
  --region $region >/dev/null 2>&1 || true

  if [[ $public_access -eq '1' ]]; then
       $AWS_CMD ecr set-repository-policy  --repository-name $name --region $region --policy-text \
       '{
         "Version": "2008-10-17",
         "Statement": [
             {
                 "Sid": "AllowPull",
                 "Effect": "Allow",
                 "Principal": "*",
                 "Action": [
                     "ecr:GetDownloadUrlForLayer",
                     "ecr:BatchGetImage"
                 ]
             }
         ]
       }'
  fi
}

create_repo $repoName $REGION 0

account_id=$($AWS_CMD sts get-caller-identity --query Account --output text)

account_ecr_uri=${account_id}.dkr.ecr.${REGION}.amazonaws.com

IMAGEURI=${account_ecr_uri}/$repoName:latest

docker tag $repoName ${IMAGEURI}

echo ${IMAGEURI}

$AWS_CMD ecr get-login-password --region ${REGION} | docker login --username AWS --password-stdin ${account_ecr_uri}

echo ">> push ${IMAGEURI}"

docker push ${IMAGEURI}
