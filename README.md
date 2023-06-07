# SES Monitoring Dashboard Solution
The SES Monitoring Dashboard provides a cost-effective streamlined solution to track emails sent through Amazon Simple Email Service (SES) and keep reputation metrics under control. 

The solution captures Amazon SES generated events, processes them with Amazon Glue DataBrew, and displays them in an Amazon Quicksight dashboard with granular graphs. This solution provides you with a starting point that you can customize at your will to meet the requirements of your organization. This solution is set to run on a scheduled basis, every hour, making it easier to perform incremental data processing. You can also leverage Amazon AppFlow (a SaaS integration service) to easily integrate data from third party products. 
If you are interested in reading more about the topic, check [this AWS Blog](https://aws.amazon.com/blogs/messaging-and-targeting/tracking-email-engagement-with-aws-analytics-services/).

The next sections contain a high level explanation of the architecture and step-by-step deployment instructions to replicate it in your AWS account.

## Solution overview
Figure 1 below describes the architecture diagram for the proposed solution.

![SES Monitoring Dashboard Architectural Diagram](/resources/ses-blog-resources/architecture.png "SES Monitoring Dashboard Architectural Diagram")*Figure 1 - Architecture*

1. Amazon SES [publishes email sending events](https://docs.aws.amazon.com/ses/latest/dg/monitor-using-event-publishing.html) to Amazon Kinesis Data Firehose leveraging a [configuration set](https://docs.aws.amazon.com/ses/latest/dg/using-configuration-sets.html).
2. [Amazon Kinesis Data Firehose](https://docs.aws.amazon.com/firehose/latest/dev/what-is-this-service.html) Delivery Stream processes incoming event data through an AWS Lambda function and stores it in an Amazon Simple Storage Service (S3) bucket, known as the Destination bucket.
3. An [AWS Glue DataBrew job](https://docs.aws.amazon.com/databrew/latest/dg/jobs.recipe.html) processes and transforms event data in the Destination bucket. It applies the transformations defined in a [Glue DataBrew recipe](https://docs.aws.amazon.com/databrew/latest/dg/recipes.html) to the source dataset and stores the output using a different prefix (‘/partitioned’) within the same bucket. Output objects are stored in the Apache Parquet format and partitioned.
4. A Lambda function copies the resulting output objects to the Aggregation bucket. The Lambda function is [invoked asynchronously via Amazon S3 event notifications](https://docs.aws.amazon.com/lambda/latest/dg/with-s3.html) when objects are created in the Destination bucket.
5. An [AWS Glue crawler](https://docs.aws.amazon.com/glue/latest/dg/crawler-running.html) runs periodically over the event data stored in the Aggregation bucket to determine its schema and update the table partitions in the AWS Glue Data Catalog.
6. [Amazon Athena queries](https://docs.aws.amazon.com/athena/latest/ug/querying-athena-tables.html) the event data table registered in the [AWS Glue Data Catalog](https://docs.aws.amazon.com/glue/latest/dg/catalog-and-crawler.html) using standard SQL.
7. [Amazon QuickSight](https://docs.aws.amazon.com/quicksight/latest/user/welcome.html) dashboards allow visualizing event data in an interactive way via its integration with Amazon Athena data sources.

## Instructions to deploy the solution

You can deploy the solution by choosing one of the following paths:
- If you want to use AWS CDK to launch the resources, go to [option A](#option-a-using-aws-cdk).
- If you want to deploy the CloudFormation template directly, go to [option B](#option-b-not-using-aws-cdk).

Please note that if you already have an Amazon QuickSight account, the following resources have to be launched in the same Region where the account was created. This specific Region is defined as “Identity Region” or "Default Region”, and the Python scripts need to access it to get the user information and automatically create Amazon QuickSight resources. 

You can check what your "Default Region" is following these steps:
- Navigate to the Amazon QuickSight console.
- Select the profile icon at the top right corner and click on `Manage QuickSight`.
- On the left panel, click on `Security & Permissions`.

Also, some of the Amazon QuickSight APIs that the scripts use, are available with the QuickSight Enterprise edition only. If you already have a Standard edition Amazon QuickSight account, you can upgrade it to Enterprise edition. 

To upgrade from Standard edition to Enterprise edition, you can follow these steps:
- Check the [documentation](https://docs.aws.amazon.com/quicksight/latest/user/upgrading-subscription.html) for any new changes in the conditions.
- Please notice that as of May 2023, if you upgrade to Enterprise edition, **you cannot downgrade back to the Standard edition**. The upgrade is instantaneous.
- Navigate to the Amazon QuickSight console.
- Open the administrative settings page by clicking on your profile icon at top right.
- At top left, choose Upgrade now.

If you don't have an Amazon QuickSight account yet, you can follow the instructions and you will be asked to create one.

### OPTION A: Using AWS CDK

0. Configure an AWS CLI profile in your terminal:
    - https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html
1. Clone the repository and go to `./cdk`. The folder contains:
    - Entrypoint of CDK application - `/bin/ses-blog-solution.ts`
    - Definition of CDK main stack - `/lib/ses-blog-solution-stack.ts`
    - Code of Transformation Lambda function - `/src/transformation_lambda`
    - Test files - `test/`
    - Definition of how to run the app - `cdk.json`
    - npm module manifest - `package.json`
    - Typescript configuration - `tsconfig.json`
2. Run `npm install` to install dependencies;
3. Update the `/bin/ses-blog-solution.ts` file adding the account ID and Region where you want to deploy the solution.
4. Run `cdk bootstrap --profile <myprofile>` to prepare your AWS environment.
5. Run `cdk deploy --profile <myprofile>` to deploy the resources to your account.
6. Once you have the resources deployed, go to [common steps](#common-steps) below to continue.

### OPTION B: Not using AWS CDK

0. Configure an AWS CLI profile in your terminal:
    - https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html
1. Clone the repository and go to `./resources/ses-blog-resources`. The folder contains:
    - Amazon QuickSight Dashboard definition - `dashboard_definition.json`
    - AWS Glue DataBrew recipe - `recipe.json`
    - Python script to create Amazon QuickSight resources - `ses-blogs-utils.py`
    - Requirements for Python script - `requirements.txt`
    - CloudFormation template - `cfn.yaml`
    - Architecture diagram - `architecture.png`
2. Run:
    - `python3 -m venv venv` to create a virtual environment.
    - `source venv/bin/activate` to activate the virtual environment.
    - `pip3 install -r requirements.txt` to install the required dependencies.
    - `python3 ses-blog-setup.py -a <account-id> -r <region> -p <cli-profile-name>`. Note that `-p` parameter is optional. If not specified, the script will use the default AWS CLI profile.
        - It creates a new S3 bucket named `<account-id>-<region>-ses-blog-utils-bucket` in your account and region and copies the AWS Lambda function code that the CloudFormation needs.
    - `deactivate` to deactivate the virtual environment.

3. Navigate to the AWS CloudFormation console and [create a stack](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/cfn-console-create-stack.html) uploading the template `cfn.yaml`. Once you have the resources deployed, go to [common steps](#common-steps) below to continue.

### COMMON STEPS
1. If you already have a verified Amazon Simple Email Service (SES) identity, you can skip this step. If not, follow these instructions to create an identity and verify it:
    - Navigate to the Simple Email Service console. On the left panel, under `Configuration`, choose `Verified identities`.
    - From the Verified identities console, on the right, click on `Create identity`.
        - Identity type: `Email address`
        - Choose `Create identity`
    - You will receive an email within a few minutes. Click on the verification link to verify the ownership of the email address. 
2. Decide which Configuration Set to use in Amazon SES.
    - If you prefer to use the Configuration Set `SESConfigurationSet` created by the CloudFormation template, move to Step 3.
    - If you prefer to use a custom Amazon SES Configuration Set, follow these steps to assign necessary permissions and link it to Amazon Kinesis Firehose:
        - Navigate to the Identity and Access Management Console.
        - From the left panel, under `Access Management` select `Roles`.
        - Search the role `<your-cfn-stack-name>-SESRole<random-code>` and click on its name. You can search through the keyword `SESRole`.
        - Navigate to the `Trust Relationships` tab and replace the name of the configuration set (by default, the value is `SESConfigurationSet`) in `AWS:SourceArn` to match the name of your configuration set. The result should be similar to this: `"AWS:SourceArn": "arn:aws:ses:<region>:<account-id>:configuration-set/<your-configuration-set-name>"`.
        - Navigate to the Amazon SES console. 
        - From the left panel, under `Configuration`, select `Configuration sets` and then select your configuration set.
        - Select the `Event destinations` tab and click on `Add destination`.
        - Select the Event Types that you want to track. Unless you have a reason to do not consider all the events, click on `Select All` and then `Next`.
        - Fill the `Specify destination` page with the following values:
            - Destination options: `Amazon Kinesis Data Firehose`.
            - Name: `<custom-name>`
            - Delivery stream: `<your-cfn-stack-name>-KinesisFirehoseStream<random-code>`
            - Identity and Access Management (IAM) Role: `<your-cfn-stack-name>-SESRole<random-code>`
        - Click on `Next`, review the information for accuracy and finally click on `Add Destination`.
3. Create some test emails that will serve as dummy data to fill the final Amazon QuickSight dashboard.    
    - Navigate to the Simple Email Service console, on the left panel, under `Configuration`, choose `Verified identities`.
    - Under `Identities` select the verified identity and click on `Send test email`
        - Fill in `Scenario`, `Subject` and `Body` with data at your preference.
        - Configuration set: `SESConfigurationSet` or `YourConfigurationSet` 
        - Click on `Send test email`
    - You can repeat this process several times to generate data that will fill the final dashboard. Emails sent through the simulator don't count towards your sending quota.
4. Upload the AWS Glue DataBrew recipe:
    - Navigate to the DataBrew console, on the left panel choose `Recipes`.
    - In the Recipes console, choose `Upload recipe`.
        - Recipe name: `<recipe_name>`.
        - For Upload recipe choose `Upload` and select the file `resources/ses-blog-resources/recipe.json`.
        - Choose `Create and publish recipe`.
5. Wait until you can see some events stored in `s3://<account-id>-<region>-ses-events-destination/raw/`.
6. Create and run an AWS Glue DataBrew job. (It will fail if there isn't any data in the S3 bucket).
    - Navigate to the DataBrew console, on the left panel choose `Jobs`, then choose `Create job`.
        - Job Type: `Create a recipe job`
        - Dataset: `SESDataBrewDataset`
        - Recipe: `<recipe_name>`, the one create before.
        - Output: `Amazon S3`
            - Output File Type: `PARQUET`
            - Output Compression: `GZIP`
            - Output S3 Location: `s3://<account-id>-<region>-ses-events-destination/partitioned/`. Don't forget the final `/`.
            - Settings: 
                - File output storage: `Replace output files for each job run` 
                - Custom partition by column values: `enabled`
                - Columns to partition by: `year`, `month`, `day`, `hour`. In this exact order.
        - Associated schedules:
            - Select `Create new schedule`.
            - Set run frequency to run every hour, every day.
        - Role: `Create new IAM role`.
        - Choose `Create and run job`.
7. Wait for the first execution of the job to end.
8. Run glue crawler `SESEventDataCrawler` manually to force detection of the data structure. The crawler is scheduled to run every hour, 30 minutes past the hour.
    - Navigate to the AWS Glue console.
    - On the left tab, under `Data Catalog` select `Crawlers`.
    - Select the crawler `SESEventDataCrawler` and click on `Run`.
9. If you haven't already created a Amazon QuickSight account, create one **in the region where you created the other resources**. This will be the default region for your Amazon QuickSight account and must be used for the following steps. To create a new account, navigate to the Amazon QuickSight console and follow the wizard. Please, remember to select the `Enterprise Edition`.
10. Make sure Amazon QuickSight has the following permissions:
    - Navigate to the Amazon QuickSight console.
    - Select the profile icon on the top right corner and click on `Manage QuickSight`.
    - On the left panel, click on `Security & Permissions`.
    - Under `QuickSight access to AWS services` click on `Manage`.
        - Make sure `Amazon S3` and `Amazon Athena` are checked (optionally other services might be checked if you use QuickSight for other projects).
        - Under `Amazon S3`, click on `Select S3 buckets` 
            - Check the `S3 bucket` column for the bucket `<account_id>-<region>-ses-events-destination-aggregated`
            - Check the `S3 bucket` and `Write permission for Athena Workgroup` columns for the bucket `<account_id>-<region>-athena-results-location`
11. Open `resources/ses-blog-resources/` folder in your terminal and, alternatively and depending on the chosen Option, run:
    - Option A - Using AWS CDK
        - `python3 -m venv venv` to create a virtual environment.
        - `source venv/bin/activate` to activate the virtual environment.
        - `pip3 install -r requirements.txt` to install the required dependencies.
        - `python3 ses-blog-utils.py -a <account_id> -r <region_id> -p <profile>` to create the Amazon QuickSight dashboard. Note that `-p` parameter is optional. If not specified, the script will use the default AWS CLI profile.
        - `deactivate` deactivate the virtual environment.
    - Option B - Not using AWS CDK
        - `source venv/bin/activate` activates the virtual environment.
        - `python3 ses-blog-utils.py -a <account_id> -r <region_id> -p <profile>` creates the Amazon QuickSight dashboard. Note that profile is optional.
        - `deactivate` to deactivate the virtual environment.
12. Go to Amazon QuickSight and explore the dashboard.

--- 

## Useful CDK commands

* `npm run build`   compile typescript to js
* `npm run watch`   watch for changes and compile
* `npm run test`    perform the jest unit tests
* `cdk deploy`      deploy this stack to your default AWS account/region
* `cdk diff`        compare deployed stack with current state
* `cdk synth`       emits the synthesized CloudFormation template

### To generate a clean CF template
* `cdk synth --path-metadata false --version-reporting false > template.yaml`
---