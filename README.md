# SES Monitoring Dashboard Solution
The SES Monitoring Dashboard provides a cost-effective streamlined solution to track emails sent through Amazon Simple Email Service (SES) and keep reputation metrics under control. 

The solution will capture Amazon SES generated events, prepare them with Amazon DataBrew, and display them in an Amazon Quicksight dashboard with granular graphs. This solution provides you with a starting point that you can customize at your will to meet the requirements of your organization. This solution is set to run on a scheduled basis, every hour, making it easier to perform incremental data processing. You can also leverage Amazon AppFlow (a SaaS integration service) to easily integrate data from third party solutions. 

The solution is built leveraging AWS CDK. If you have experience with CDK you can deploy the resources through it. 

If you prefer to deploy the solution leveraging a standalone CloudFormation template, read the next section.

If you are interested in reading more, check [this AWS Blog](https://aws.amazon.com/blogs/messaging-and-targeting/tracking-email-engagement-with-aws-analytics-services/).

---

## Instructions to deploy the solution

There are two ways to deploy the solution:
- If you want to use AWS CDK to launch the resources, go to [option A](#option-a-using-aws-cdk).
- If you want to deploy the CloudFormation template directly, go to [option B](#option-b-not-using-aws-cdk).

Please note that if you already have an Amazon QuickSight account, the following resources have to be launched in the same Region where the account was created. This Region is defined as “Identity Region” or "Default Region”, and the python script needs to access it to get the user information and automatically create Amazon QuickSight resources. 

You can check what your "Default Region" is following these steps:
- Navigate to the Amazon QuickSight console.
- Select the profile icon on the top right corner and click on `Manage QuickSight`.
- On the left panel, click on `Security & Permissions`.

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
2. Run `python3 ses-blog-setup.py <account-id> <region> <profile?>`.
    - It creates a new S3 bucket named `<account-id>-<region>-ses-blog-utils-bucket` in your account and region and copies the AWS Lambda function code that the CloudFormation needs.
3. Launch the CloudFormation template `cfn.yaml`. Once you have the resources deployed, go to [common steps](#common-steps) below to continue.

### COMMON STEPS
1. Create an identity in Amazon Simple Email Service (SES) and verify it (unless you already have one):
    - Navigate to the Simple Email Service console, on the left panel, under `Configuration`, choose `Verified identities`.
    - In the Verified identities console, on the right click on `Create identity`.
        - Identity type: `Email address`
        - Choose `Create identity`
    - You will receive an email. Click on the verification link to verify the ownership of the email address.
2. From your verified identity, create some test emails assigning the `SESConfigurationSet` created by the CloudFormation template.
    - Navigate to the Simple Email Service console, on the left panel, under `Configuration`, choose `Verified identities`.
    - Under `Identities` select the new identity and click on `Send test email`
        - Fill in `Scenario`, `Subject` and `Body` with data at your preference.
        - Configuration set: `SESConfigurationSet`
        - Choose: `Send test email`
    - You can repeat this process several times to generate dummy data that will fill the final dashboard. Emails sent through the simulator don't count towards your sending quota.
3. Upload the AWS Glue DataBrew recipe:
    - Navigate to the DataBrew console, on the left panel choose `Recipes`.
    - In the Recipes console, on the top left choose `Upload recipe`.
        - Recipe name: `<recipe_name>`.
        - For Upload recipe choose `Upload` and select the file `resources/ses-blog-resources/recipe.json`.
        - Choose `Create and publish recipe`.
4. Wait until you can see some events stored in `s3://<account-id>-<region>-ses-events-destination/raw/`.
5. Create and run an AWS Glue DataBrew job. (It will fail if there isn't any data in the S3 bucket).
    - Job Type: `Create a recipe job`
    - Dataset: `SESDataBrewDataset`
    - Recipe: `<recipe_created_before>`
    - Output: `Amazon S3`
        - Output File Type: `PARQUET`
        - Output Compression: `GZIP`
        - Output S3 Location: `s3://<account-id>-<region>-ses-events-destination/partitioned/`
        - Settings: 
            - File output storage: `Replace output files for each job run` 
            - Custom partition by column values: `enabled`
            - Columns to partition by: `year`, `month`, `day`, `hour`. In this exact order.
    - Schedule: `every hour`, `every day`
    - Role: `Create new IAM role`
6. Wait for the first execution of the job to end.
7. Run glue crawler `SESEventDataCrawler` manually to force detection of the data structure. The crawler is scheduled to run every hour, 30 minutes past the hour.
    - Navigate to the AWS Glue console.
    - On the left tab, under `Data Catalog` select `Crawlers`.
    - Select the crawler `SESEventDataCrawler` and click on `Run`.
8. If you haven't already created a Amazon QuickSight account, create one in the region you launched resources. This will be the default region for your Amazon QuickSight account and should be used for the following steps.
9. Make sure Amazon QuickSight has the following permissions:
    - Navigate to the Amazon QuickSight console.
    - Select the profile icon on the top right corner and click on `Manage QuickSight`.
    - On the left panel, click on `Security & Permissions`.
    - Under `QuickSight access to AWS services` click on `Manage`.
        - Make sure `Amazon S3` and `Amazon Athena` are checked (optionally other services might be checked if you use QuickSight for other projects).
        - Under `Amazon S3`, click on `Select S3 buckets` 
            - Check the `S3 bucket` column for the bucket `<account_id>-<region>-ses-events-destination-aggregated`
            - Check the `S3 bucket` and `Write permission for Athena Workgroup` columns for the bucket `<account_id>-<region>-athena-results-location`
10. Open `resources/ses-blog-resources/` folder in your terminal and run:
    - `python3 -m venv venv` creates a virtual environment.
    - `source venv/bin/activate` activates the virtual environment.
    - `pip3 install -r requirements.txt` installs the required dependencies.
    - `python3 ses-blog-utils.py <account_id> <region_id> <profile?>` creates the Amazon QuickSight dashboard.
    - `deactivate` deactivate the virtual environment.
11. Go to Amazon QuickSight and explore the dashboard.

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