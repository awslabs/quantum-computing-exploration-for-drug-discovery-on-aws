#!/usr/bin/env bash
set -e

AWS_CMD='aws '

if [[ -n $PROFILE ]];then
   AWS_CMD="aws --profile $PROFILE"
fi 

rm -rf ../code/ > /dev/null 2>&1
rm -rf ../code.zip > /dev/null 2>&1

mkdir ../code/

cp -r * ../code/

cd ../code/
rm -rf cdk.out  > /dev/null 2>&1 || true
rm -rf node_modules > /dev/null 2>&1 || true 

zip -r ../code.zip .
cd ..
rm -rf ./code/

latest_ver=$(git tag | tail -1)

s3_paths=(
    s3://amazon-braket-gcr-qc-sol-common/qc/${latest_ver}/code.zip
    s3://amazon-braket-gcr-qc-sol-common/qc/latest/code.zip
)

for s3_path in ${s3_paths[@]};do 

    echo "$AWS_CMD s3 cp ./code.zip $s3_path --acl public-read"

    $AWS_CMD s3 cp ./code.zip $s3_path --acl public-read

    echo $s3_path
done
rm ./code.zip

