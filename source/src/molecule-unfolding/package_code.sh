#!/usr/bin/env bash
set -e

AWS_CMD='aws '

if [[ -n $PROFILE ]];then
   AWS_CMD="aws --profile $PROFILE"
fi 

rm -rf ./molecule-unfolding-code/ > /dev/null 2>&1
rm -rf molecule-unfolding-code.zip > /dev/null 2>&1

mkdir ./molecule-unfolding-code/

cp -r ./batch-images ./molecule-unfolding-code/
cp -r ./cdk ./molecule-unfolding-code/
cp -r ./lambda ./molecule-unfolding-code/
cp -r ./molecule-data ./molecule-unfolding-code/
cp -r ./utility ./molecule-unfolding-code/
cp -r ./build.sh ./molecule-unfolding-code/
cp -r ./*.ipynb ./molecule-unfolding-code/
cp -r ./sync_code.sh ./molecule-unfolding-code/

cd ./molecule-unfolding-code/

zip -r ../molecule-unfolding-code.zip .
cd ..
rm -rf ./molecule-unfolding-code/

latest_ver=$(git tag | tail -1)

s3_paths=(
    s3://amazon-braket-gcr-qc-sol-common/molecule-unfolding-code/${latest_ver}/molecule-unfolding-code.zip
    s3://amazon-braket-gcr-qc-sol-common/molecule-unfolding-code/latest/molecule-unfolding-code.zip
)

for s3_path in ${s3_paths[@]};do 

    echo "$AWS_CMD s3 cp ./molecule-unfolding-code.zip $s3_path --acl public-read"

    $AWS_CMD s3 cp ./molecule-unfolding-code.zip $s3_path --acl public-read

    echo $s3_path
done
rm ./molecule-unfolding-code.zip





