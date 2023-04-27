# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""
This script copies the resources needed to deploy the solution into a new S3 bucket.
Related AWS blog:
https://aws.amazon.com/blogs/messaging-and-targeting/tracking-email-engagement-with-aws-analytics-services/.

This script takes three parameters, in this exact order:
    - the AWS account ID;
    - the AWS region where the resources will be deployed;
    - (optional) an AWS CLI credentials profile. 

The resources copied are:
- AWS CloudFormation template;
- AWS Lambda functions code;
- Amazon QuickSight dashboard definition;
- AWS Glue DataBrew recipe;
- Python script to create the Amazon QuickSight resources.
"""

import boto3
import sys
import logging
import shutil
import os
from botocore.exceptions import ClientError


logging.basicConfig(level=logging.INFO)

def create_bucket(s3_client, bucket_name, region):
    """Create an S3 bucket in a specified region

    :param bucket_name: Bucket to create
    :param region: String region to create bucket in, e.g., 'eu-west-1'
    :return: S3 bucket URL if bucket created, else None
    """
    
    # Create bucket
    try:
        location = {'LocationConstraint': region}
        response = s3_client.create_bucket(Bucket=bucket_name,
                                CreateBucketConfiguration=location)
    except ClientError as e:
        logging.error(e)
        
    return response['Location']

def upload_resources(s3_client, folder_name, key, dest_bucket):
    try:
        # zip folder
        output_filename = "temp"
        format = "zip"
        shutil.make_archive(output_filename, format, folder_name)

        # upload zipped folder
        s3_client.upload_file(
            Filename = ".".join([output_filename, format]),
            Bucket = dest_bucket,
            Key = key
        )

        # delete zipped folder
        os.remove(".".join([output_filename, format]))
        
    except Exception as e:
        logging.error(e)

def main():
    # check if the required parameters, in order (1) AWS account ID, (2) AWS Region and (3, optional) 
    # AWS CLI profile are present
    if len(sys.argv) >= 3:
        account_id = sys.argv[1]
        region = sys.argv[2]
        if len(sys.argv) == 4:
            profile = sys.argv[3]
            boto3.setup_default_session(profile_name=profile)
            logging.info(
                f"Input parameters: account id {account_id}, region '{region}', profile '{profile}'.")

        else:
            boto3.setup_default_session(profile_name="default")
            logging.info(
                f"Input parameters: account id {account_id}, region '{region}', profile 'default'.")


    folder_name = "../TransformationLambdaCode"
    key = "TransformationLambdaCode.zip"
    s3_client = boto3.client('s3', region_name=region)

    # create bucket
    dest_bucket = f"{account_id}-{region}-ses-blog-utils-bucket"
    
    destination_bucket = create_bucket(s3_client, dest_bucket, region)
    logging.info("S3 bucket created: " + destination_bucket)
        
    # copy resources to the bucket
    upload_resources(s3_client, folder_name, key, dest_bucket)
    logging.info("Object successflly copied to the new bucket.")

    logging.info("Next step: deploy the CloudFormation template from the AWS console.")

if __name__ == "__main__":
    main()


