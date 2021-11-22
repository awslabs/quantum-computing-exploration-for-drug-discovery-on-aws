#!/usr/bin/env bash
set -e

AWS_CMD='aws '

if [[ -n $PROFILE ]];then
   AWS_CMD="aws --profile $PROFILE"
fi 

rm -rf ./notebook/ > /dev/null 2>&1
rm -rf notebook.zip > /dev/null 2>&1

mkdir ./notebook/

cp *.ipynb ./notebook/
cp -r utility ./notebook/

cd ./notebook/
zip -r ../notebook.zip .
cd ..
rm -rf ./notebook/

latest_ver=$(git tag | tail -1)

s3_paths=(
    s3://amazon-braket-gcr-qc-sol-common/notebook/${latest_ver}/notebook.zip
    s3://amazon-braket-gcr-qc-sol-common/notebook/latest/notebook.zip
)

for s3_path in ${s3_paths[@]};do 

    echo "$AWS_CMD s3 cp ./notebook.zip $s3_path --acl public-read"

    $AWS_CMD s3 cp ./notebook.zip $s3_path --acl public-read

    echo $s3_path
done
rm ./notebook.zip





