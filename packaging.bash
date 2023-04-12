#!/usr/bin/bash
set -e # if anything throws an error, exit the script immediately instead of continuing.

LAMBDA_BUCKET=$1

# S3 api will output the "Not Found" string to stderr, so '2>&1' to catpure that, too.
bucket_does_not_exist=$(aws s3api head-bucket --bucket $LAMBDA_BUCKET 2>&1 | grep "Not Found" | wc -l)

if [ $bucket_does_not_exist -eq 1 ]; then
  aws s3api create-bucket --bucket $LAMBDA_BUCKET
fi

for lambda_dir in backend/*/; do
    # Skip the common directory
    if [[ $lambda_dir == *"common"* ]]; then
      continue
    fi

    lambda_name=$(basename $lambda_dir)

    # Package the Lambda code
    cd $lambda_dir
    cp -r ../common .
    if [ -f requirements.txt ]; then
        python -m pip install -r requirements.txt -t .
    fi
    zip -r ../../${lambda_name}.zip *
    cd ../..

    # Check to see if the zip exists in the bucket before we copy it.
    zip_exists=$(aws s3 ls s3://${LAMBDA_BUCKET}/${lambda_name}.zip | wc -l)

    # Upload the Lambda code to S3
    aws s3 cp ${lambda_name}.zip s3://${LAMBDA_BUCKET}/${lambda_name}.zip

    # Update the Lambda function's code only if the .zip file already existed.
    # Deployment is such that the first time, we don't execute this call because infra will not have been deployed yet.
    # We will upload the zip, then execute the cfn.
    if [ $zip_exists -eq 1 ]; then
        aws lambda update-function-code --function-name ${lambda_name} --s3-bucket $LAMBDA_BUCKET --s3-key ${lambda_name}.zip
    fi

done
