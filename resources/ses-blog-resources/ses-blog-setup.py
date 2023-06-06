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
import logging
import shutil
import os
from botocore.exceptions import ClientError
from boto3 import Session
import zipfile
import argparse

logging.basicConfig(level=logging.INFO)

def parse_arguments():
    parser = argparse.ArgumentParser(
                    prog='ses-blog-setup',
                    description='Copies the resources needed to deploy the solution into a new S3 bucket',
                    epilog='Check the README for more information')

    parser.add_argument('-a', '--account-id', required=True, metavar='', help="AWS Account ID")
    parser.add_argument('-r', '--region', required=True, metavar='', help="AWS Region")
    parser.add_argument('-p', '--profile', metavar='', help="AWS credentials Profile")
    args = parser.parse_args()
    
    return args

def create_bucket(s3_client, bucket_name):
    """Create an S3 bucket in a specified region

    :param bucket_name: Bucket to create
    :param region: String region to create bucket in, e.g., 'eu-west-1'
    :return: S3 bucket URL if bucket created, else None
    """
    
    # Create bucket
    try:
        response = s3_client.create_bucket(Bucket=bucket_name)
    
    except ClientError as e:
        logging.error(e)
        
    return response['Location']

def check_files():
    directory = os.getcwd()  # Get the current directory
    file1 = "schema.json"  # Specify the first file name
    file2 = "index.py"  # Specify the second file name

    files = os.listdir(directory)  # Get all files in the directory

    if file1 in files and file2 in files:
        return True
    else:
        return False

def upload_resources(s3_client, folder_name, key, dest_bucket):

    file1 = "schema.json"  # Specify the first file name
    file2 = "index.py"  # Specify the second file name

    output_filename = "temp"
    file_format = "zip"

    try:
        # zip folder

        file_in_root = check_files()

        if file_in_root:

            with zipfile.ZipFile(f"{output_filename}.{file_format}", 'w') as zipf:
                zipf.write(file1)
                zipf.write(file2)
        else:
            shutil.make_archive(output_filename, file_format, folder_name)

        # upload zipped folder
        s3_client.upload_file(
            Filename = ".".join([output_filename, file_format]),
            Bucket = dest_bucket,
            Key = key
        )

        # delete zipped folder
        os.remove(".".join([output_filename, file_format]))
        
    except Exception as e:
        logging.error(e)



def main(args):
    aws_session = Session
    region = args.region
    account_id = args.account_id

    if args.profile:
        profile = args.profile
        
        aws_session = boto3.Session(profile_name=profile)
        logging.info(
            f"Input parameters: account id {account_id}, region '{region}', profile '{profile}'.")

    else:
        aws_session = boto3.Session(region_name=region)
        logging.info(
            f"Input parameters: account id {account_id}, region '{region}', profile 'default'.")


    folder_name = "../TransformationLambdaCode"
    key = "TransformationLambdaCode.zip"
    s3_client = aws_session.client('s3', region_name=region)

    # create bucket
    dest_bucket = f"{account_id}-{region}-ses-blog-utils-bucket"
    
    response = create_bucket(s3_client, dest_bucket)
    logging.info("S3 bucket created: " + response)
        
    # copy resources to the bucket
    upload_resources(s3_client, folder_name, key, dest_bucket)
    logging.info("Object successflly copied to the new bucket.")

    logging.info("Next step: deploy the CloudFormation template from the AWS console.")

if __name__ == "__main__":
    args = parse_arguments()
    main(args)