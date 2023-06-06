# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""
This script automates the creation of the Amazon QuickSight data source, dataset and dashboard
in the context of the AWS blog:
https://aws.amazon.com/blogs/messaging-and-targeting/tracking-email-engagement-with-aws-analytics-services/.

This script takes three parameters, in this exact order:
    - the AWS account ID;
    - the AWS region where the resources will be deployed;
    - (optional) an AWS CLI credentials profile. 

This script requires:
    - an Amazon QuickSight Admin user in the same AWS Region where the resources will be created;
    - 'boto3' version 1.26.37 to work. Required Amazon QuickSight APIs might be missing in other boto3 versions.
"""

import json
import boto3
import logging
import uuid
import time
from boto3 import Session
import argparse

logging.basicConfig(level=logging.INFO)

def parse_arguments():
    parser = argparse.ArgumentParser(
                    prog='ses-blog-setup',
                    description='Automates the creation of the Amazon QuickSight data source, dataset and dashboard',
                    epilog='Check the README for more information')

    parser.add_argument('-a', '--account-id', required=True, metavar='', help="AWS Account ID")
    parser.add_argument('-r', '--region', required=True, metavar='', help="AWS Region")
    parser.add_argument('-p', '--profile', metavar='', help="AWS credentials Profile")
    args = parser.parse_args()
    
    return args

def get_quicksight_user(client, account_id, namespace) -> str:
    """
    Gets default Amazon QuickSight user ARN that has permissions to perform
    the required actions in the next steps.

    Parameters
    ----------
    client : botocore.client.QuickSight
        The boto3 client for Amazon QuickSight
    account_id : str
        The AWS account ID where the resources will be created
    namespace : str
        The Amazon QuickSight namespace
        
    Returns
    -------
    str
        The Amazon QuickSight default user ARN
    """
    response = client.list_users(
        AwsAccountId=account_id,
        Namespace=namespace
    )
    logging.info("Getting Amazon QuickSight user ...")
    logging.info(response)
    user_arn = response["UserList"][0]["Arn"]
    return user_arn


def create_data_source(client, account_id, quicksight_user, data_source_id, data_source_name, workgroup_name) -> None:
    """
    Creates an Amazon Athena data source in Amazon QuickSight

    Parameters
    ----------
    client : botocore.client.QuickSight
        The boto3 client for Amazon QuickSight
    account_id : str
        The AWS account ID where the resources will be created
    quicksight_user : str
        The Amazon QuickSight user ARN obtained from the 'get_quicksight_user' method
    data_source_id : str
        Amazon QuickSight data source identifier
    data_source_name : str
        Amazon QuickSight data source name
    """

    logging.info("Creating Amazon QuickSight data source ...")
    data_source = client.create_data_source(
        AwsAccountId=account_id,
        DataSourceId=data_source_id,
        Name=data_source_name,
        Type="ATHENA",
        DataSourceParameters={
            "AthenaParameters": {
                "WorkGroup": workgroup_name
            }},
        Permissions=[
            {
                "Principal": quicksight_user,
                "Actions": [
                    "quicksight:UpdateDataSourcePermissions",
                    "quicksight:DescribeDataSource",
                    "quicksight:DescribeDataSourcePermissions",
                    "quicksight:PassDataSource",
                    "quicksight:UpdateDataSource",
                    "quicksight:DeleteDataSource"
                ]
            }
        ]
    )
    logging.info(data_source)


def create_dataset(client, account_id, region, data_source_id, quicksight_user, dataset_id, dataset_name) -> None:
    """
    Creates an Amazon QuickSight dataset based on an Amazon QuickSight data source
    created by the 'create_data_source' method. 

    Parameters
    ----------
    client : botocore.client.QuickSight
        The boto3 client for Amazon QuickSight
    account_id : str
        The AWS account ID where the resources will be created
    region : str
        AWS Region where the resources will be created
    data_source_id : str
        Amazon QuickSight data source identifier
    quicksight_user : str
        The Amazon QuickSight user ARN obtained from the 'get_quicksight_user' method
    dataset_id : str
        Amazon QuickSight dataset identifier
    dataset_name : str
        Amazon QuickSight dataset name
    """    
    logging.info("Creating Amazon QuickSight dataset ...")
    dataset = client.create_data_set(
        AwsAccountId=account_id,
        DataSetId=dataset_id,
        Name=dataset_name,
        PhysicalTableMap={
            "57daf616-4a5d-4014-8e17-a0324e2c2940": {
                "RelationalTable": {
                    "DataSourceArn": f"arn:aws:quicksight:{region}:{account_id}:datasource/{data_source_id}",
                    "Catalog": "AwsDataCatalog",
                    "Schema": "ses_event_data_database",
                    "Name": "partitioned",
                    "InputColumns": [
                        {
                              "Name": "bouncetype",
                              "Type": "STRING"
                        },
                        {
                            "Name": "link",
                            "Type": "STRING"
                        },
                        {
                            "Name": "complaintfeedbacktype",
                            "Type": "STRING"
                        },
                        {
                            "Name": "delaytype",
                            "Type": "STRING"
                        },
                        {
                            "Name": "errormesage",
                            "Type": "STRING"
                        },
                        {
                            "Name": "expirationtime",
                            "Type": "STRING"
                        },
                        {
                            "Name": "feedbackid",
                            "Type": "STRING"
                        },
                        {
                            "Name": "processingtimemillis",
                            "Type": "INTEGER"
                        },
                        {
                            "Name": "eventtype",
                            "Type": "STRING"
                        },
                        {
                            "Name": "sender",
                            "Type": "STRING"
                        },
                        {
                            "Name": "subject",
                            "Type": "STRING"
                        },
                        {
                            "Name": "recipientmail",
                            "Type": "STRING"
                        },
                        {
                            "Name": "recipientevent",
                            "Type": "STRING"
                        },
                        {
                            "Name": "mailrecipientdomain",
                            "Type": "STRING"
                        },
                        {
                            "Name": "messageid",
                            "Type": "STRING"
                        },
                        {
                            "Name": "timestamp",
                            "Type": "STRING"
                        },
                        {
                            "Name": "ipaddress",
                            "Type": "STRING"
                        },
                        {
                            "Name": "reason",
                            "Type": "STRING"
                        },
                        {
                            "Name": "sesoutgoingip",
                            "Type": "STRING"
                        },
                        {
                            "Name": "sesourceip",
                            "Type": "STRING"
                        },
                        {
                            "Name": "templatename",
                            "Type": "STRING"
                        },
                        {
                            "Name": "useragent",
                            "Type": "STRING"
                        },
                        {
                            "Name": "year",
                            "Type": "STRING"
                        },
                        {
                            "Name": "month",
                            "Type": "STRING"
                        },
                        {
                            "Name": "day",
                            "Type": "STRING"
                        },
                        {
                            "Name": "hour",
                            "Type": "STRING"
                        },

                    ]
                }
            }
        },
        LogicalTableMap={
            "57daf616-4a5d-4014-8e17-a0324e2c2940": {
                "Alias": "partitioned",
                "DataTransforms": [
                    {
                        "CastColumnTypeOperation": {
                            "ColumnName": "expirationtime",
                            "NewColumnType": "DATETIME",
                            "Format": "yyyy-MM-dd'T'HH:mm:ss.SSSSZ"
                        }
                    },
                    {
                        "CastColumnTypeOperation": {
                            "ColumnName": "timestamp",
                            "NewColumnType": "DATETIME",
                            "Format": "yyyy-MM-dd'T'HH:mm:ss.SSSSZ"
                        }
                    },
                    {
                        "ProjectOperation": {
                            "ProjectedColumns": [
                                "bouncetype",
                                "recipientevent",
                                "recipientmail",
                                "delaytype",
                                "mailrecipientdomain",
                                "errormesage",
                                "expirationtime",
                                "feedbackid",
                                "ipaddress",
                                "link",
                                "messageid",
                                "processingtimemillis",
                                "reason",
                                "sesoutgoingip",
                                "sesourceip",
                                "templatename",
                                "timestamp",
                                "useragent",
                                "eventtype",
                                "sender",
                                "subject",
                                "year",
                                "month",
                                "day",
                                "hour"
                            ]
                        }
                    }
                ],
                "Source": {
                    "PhysicalTableId": "57daf616-4a5d-4014-8e17-a0324e2c2940"
                }
            }
        },
        ImportMode="DIRECT_QUERY",
        Permissions=[
            {
                "Principal": quicksight_user,
                "Actions": [
                    "quicksight:UpdateDataSetPermissions",
                    "quicksight:DescribeDataSet",
                    "quicksight:DescribeDataSetPermissions",
                    "quicksight:PassDataSet",
                    "quicksight:DescribeIngestion",
                    "quicksight:ListIngestions",
                    "quicksight:UpdateDataSet",
                    "quicksight:DeleteDataSet",
                    "quicksight:CreateIngestion",
                    "quicksight:CancelIngestion"
                ]
            }
        ]
    )
    logging.info(dataset)

def get_dashboard_definition(region, account_id, dataset_id, template_file) -> dict:
    """
    Reads the JSON file named as the 'template_file' parameter, updates the 
    DataSetArn attribute and returns it. 

    Parameters
    ----------
    client : botocore.client.QuickSight
        The boto3 client for Amazon QuickSight
    account_id : str
        The AWS account ID where the resources will be created
    quicksight_user : str
        The Amazon QuickSight user ARN obtained from the 'get_quicksight_user' method
    data_source_id : str
        Amazon QuickSight data source identifier
    data_source_name : str
        Amazon QuickSight data source name
        
    Returns
    -------
    dict
        Description of the components to create an Amazon QuickSight dashboard
    """
    
    f = open(template_file)
    dd = json.load(f)
    dd['DataSetIdentifierDeclarations'][0][
        'DataSetArn'] = f"arn:aws:quicksight:{region}:{account_id}:dataset/{dataset_id}"
    f.close()
    return dd

def create_dashboard(client, account_id, region, quicksight_user, dataset_id, dashboard_id, dashboard_name, template_file) -> None:
    """
    Creates an Amazon QuickSight dashboard based on the 'template_file' parameter and 
    filled with data coming from the dataset identified by the 'dataset_id' parameter.
    
    Parameters
    ----------
    client : botocore.client.QuickSight
        The boto3 client for Amazon QuickSight
    account_id : str
        The AWS account ID where the resources will be created
    region : str
        AWS Region where the resources will be created
    quicksight_user : str
        The Amazon QuickSight user ARN obtained from the 'get_quicksight_user' method
    dataset_id : str
        Amazon QuickSight dataset identifier
    dashboard_id : str
        Amazon QuickSight dashboard identifier
    dashboard_name : str
        Amazon QuickSight dashboard name
    template_file : str
        The name of an external JSON file that contains the dashboard definition
    """
    
    logging.info("Creating Amazon QuickSight dashboard ...")
    dashboard_definition = get_dashboard_definition(
        region, account_id, dataset_id, template_file)
    dashboard = client.create_dashboard(
        AwsAccountId=account_id,
        DashboardId=dashboard_id,
        Name=dashboard_name,
        Permissions=[
            {
                "Principal": quicksight_user,
                "Actions": [
                    "quicksight:DescribeDashboard",
                    "quicksight:ListDashboardVersions",
                    "quicksight:UpdateDashboardPermissions",
                    "quicksight:QueryDashboard",
                    "quicksight:UpdateDashboard",
                    "quicksight:DeleteDashboard",
                    "quicksight:DescribeDashboardPermissions",
                    "quicksight:UpdateDashboardPublishedVersion"
                ]
            }
        ],
        VersionDescription="1",
        DashboardPublishOptions={
            "AdHocFilteringOption": {
                "AvailabilityStatus": "DISABLED"
            },
            "ExportToCSVOption": {
                "AvailabilityStatus": "ENABLED"
            },
            "SheetControlsOption": {
                "VisibilityState": "EXPANDED"
            }
        },
        ThemeArn="arn:aws:quicksight::aws:theme/MIDNIGHT",
        Definition=dashboard_definition
    )
    
    # wait for Dashboard to reach the "CREATION_SUCCESSFUL" state
    if dashboard['CreationStatus'] == 'CREATION_IN_PROGRESS':
        logging.info("Dashboard creation started. Waiting for the dashboard to be available.")
        
        while(True):
            time.sleep(1)   # wait 1 second 
            response = client.describe_dashboard(
                AwsAccountId=account_id,
                DashboardId=dashboard_id
            )            
            status = response['Dashboard']['Version']['Status']
            if  status == 'CREATION_SUCCESSFUL':
                logging.info("Dashboard successfully created.")
                break
            elif status != 'CREATION_IN_PROGRESS':
                raise Exception("Dashboard couldn't be created.")
            
    logging.info("Dashboard ARN: " + dashboard['Arn'])

def main(args):
    aws_session = Session
    region = args.region
    account_id = args.account_id

    if args.profile:
        profile = args.profile

        aws_session = boto3.Session(profile_name=profile)
        logging.info(
            f"Input parameters: account id {account_id}, region '{region}', profile '{profile}'."
        )

    else:
        aws_session = boto3.Session(region_name=region)
        
        logging.info(
            f"Input parameters: account id {account_id}, region '{region}', profile 'default'."
        )

    namespace = "default"                                   # Amazon QuickSight namespace
    data_source_id = "AthenaDataSource"                     # Amazon QuickSight data source id
    data_source_name = "Athena Data Source"                 # Amazon QuickSight data source name
    athena_workgroup_name = "SesAthenaWorkgroup"            # Amazon Athena workgroup name, defined in the CloudFormation template
    dataset_id = str(uuid.uuid4())                          # Amazon QuickSight dataset id
    dataset_name = "partitioned"                            # Amazon QuickSight dataset name
    dashboard_id = "MySESLogDashboard"                      # Amazon QuickSight dashboard id
    dashboard_name = "MySESLogDashboard"                    # Amazon QuickSight dashboard name
    dashboard_template_file = "dashboard_definition.json"   # Amazon QuickSight dashboard template, stored externally as a JSON file

    try:
        client = aws_session.client('quicksight')
        quicksight_user = get_quicksight_user(
            client, account_id, namespace)
        create_data_source(client, account_id, quicksight_user,
                            data_source_id, data_source_name, athena_workgroup_name)
        create_dataset(client, account_id, region, data_source_id,
                        quicksight_user, dataset_id, dataset_name)
        create_dashboard(client, account_id, region, quicksight_user,
                            dataset_id, dashboard_id, dashboard_name, dashboard_template_file)

    except Exception as e:
        logging.error(e)


if __name__ == "__main__":
    args = parse_arguments()
    main(args)