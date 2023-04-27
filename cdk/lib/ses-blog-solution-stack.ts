import { Stack, StackProps, Duration } from 'aws-cdk-lib';
import { aws_s3 as s3 } from 'aws-cdk-lib';
import { aws_iam as iam } from 'aws-cdk-lib';
import { aws_ses as ses } from 'aws-cdk-lib';
import { S3EventSource } from 'aws-cdk-lib/aws-lambda-event-sources';
import { Construct } from 'constructs';
import { Function, Runtime, Code } from 'aws-cdk-lib/aws-lambda';
import { NagSuppressions } from 'cdk-nag';
import { CfnDataset} from 'aws-cdk-lib/aws-databrew';
import { CfnCrawler, CfnDatabase } from 'aws-cdk-lib/aws-glue';
import { DeliveryStream, StreamEncryption, LambdaFunctionProcessor } from '@aws-cdk/aws-kinesisfirehose-alpha';
import { S3Bucket, Compression } from '@aws-cdk/aws-kinesisfirehose-destinations-alpha';
import { aws_athena as athena } from 'aws-cdk-lib';
import * as fs from 'fs';
import * as path from 'path';


export class SesBlogSolutionStack extends Stack {
  constructor(scope: Construct, id: string, props?: StackProps) {
    super(scope, id, props);

    // Create the S3 bucket that will receive the event destination data from Kinesis Firehose
    const destinationBucket = new s3.Bucket(this, 'ses-events-destination', {
      bucketName: `${this.account}-${this.region}-ses-events-destination`,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      encryption: s3.BucketEncryption.KMS_MANAGED,
      objectOwnership: s3.ObjectOwnership.BUCKET_OWNER_ENFORCED,
      enforceSSL: true,
    });

    const replicationLambdaCode = fs.readFileSync('src/replication_lambda/index.js', 'utf8');

    // Create the S3 bucket that will contain a copy of the objected from the /partitioned
    // prefix in the destinationBucket
    const aggregatedBucket = new s3.Bucket(this, 'ses-events-destination-aggregated', {
      bucketName: `${this.account}-${this.region}-ses-events-destination-aggregated`,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      encryption: s3.BucketEncryption.KMS_MANAGED,
      objectOwnership: s3.ObjectOwnership.BUCKET_OWNER_ENFORCED,
      enforceSSL: true,
    });

    // Create a Lambda function that copies objects from destinationBucket to aggregatedBucket
    const lambdaCopyFunction = new Function(this, 'SESPartitionedObjectReplicationFunction', {
      runtime: Runtime.NODEJS_12_X,
      handler: 'index.handler',
      functionName: 'SESPartitionedObjectReplicationFunction',
      code: Code.fromInline(replicationLambdaCode.toString()),
      environment: {
        SRC_PREFIX: 'partitioned/',
        DEST_BUCKET: aggregatedBucket.bucketName
      }
    });

    // Add S3 event source to the Lambda function
    lambdaCopyFunction.addEventSource(new S3EventSource(destinationBucket, {
      events: [ s3.EventType.OBJECT_CREATED ],
      filters: [ { prefix: 'partitioned/' } ]
    }));

    destinationBucket.grantRead(lambdaCopyFunction);
    aggregatedBucket.grantWrite(lambdaCopyFunction);

    NagSuppressions.addResourceSuppressions(destinationBucket, [
      {id: 'AwsSolutions-S1', reason: 'Access logs disabled'},
    ]);

     // Create a Lambda function that transforms data in Kinesis Firehose
     const lambdaTransformFunction = new Function(this, 'SESEventsTransformationFunction', {
      runtime: Runtime.PYTHON_3_9,
      handler: 'index.lambda_handler',
      functionName: 'SESEventsTransformationFunction',
      code: Code.fromAsset(path.join(__dirname, '../src/transformation_lambda')),
      timeout: Duration.minutes(1),
    });

    const lambdaProcessor = new LambdaFunctionProcessor(lambdaTransformFunction, {
    });

    const s3Destination = new S3Bucket(destinationBucket, {
      dataOutputPrefix: 'raw/',
      compression: Compression.GZIP,
      bufferingInterval: Duration.seconds(60),
      processor: lambdaProcessor,
    });

    const kinesisfirehoseDeliveryStream = new DeliveryStream(this, 'KinesisFirehoseStream', {
      destinations: [s3Destination],
      encryption: StreamEncryption.AWS_OWNED,
    });

    NagSuppressions.addResourceSuppressionsByPath(this,
      '/SesBlogSolutionStack/KinesisFirehoseStream/S3 Destination Role/DefaultPolicy/Resource', [
      {id: 'AwsSolutions-IAM5', reason: 'IAM entity contains wildcard permissions'},
    ]);
    
    const cfnConfigurationSet = new ses.CfnConfigurationSet(this, 'cfnConfigurationSet', {
      name: `SESConfigurationSet`
    });

    const policyDocument = {
      "Version": "2012-10-17",
      "Statement": [
        {
          "Sid": "",
          "Effect": "Allow",
          "Action": [
            "firehose:PutRecordBatch"
          ],
          "Resource": [
            kinesisfirehoseDeliveryStream.deliveryStreamArn
          ]
        }
      ]
    };

    const customPolicyDocument = iam.PolicyDocument.fromJson(policyDocument);
    const kinesisPutRecordBatchPolicy = new iam.ManagedPolicy(this, 'KinesisPutRecordBatchPolicy', {
      description: 'AllowsFirehosePutRecordBatch',
      document: customPolicyDocument
    });

    const sesRole = new iam.Role(this, 'SESRole', {
      assumedBy: new iam.PrincipalWithConditions(new iam.ServicePrincipal('ses.amazonaws.com'), {
        StringEquals: {
          'AWS:SourceAccount': this.account,
          'AWS:SourceArn': `arn:aws:ses:${this.region}:${this.account}:configuration-set/${cfnConfigurationSet.name}`
        }
      }),
      managedPolicies: [kinesisPutRecordBatchPolicy]
    });

    new ses.CfnConfigurationSetEventDestination(this, 'cfnConfigurationSetEventDestination', {
      configurationSetName: String(cfnConfigurationSet.name),
      eventDestination: {
        matchingEventTypes: ['send', 'reject', 'bounce', 'complaint',
          'delivery', 'open', 'click', 'renderingFailure', 'subscription', 'deliveryDelay'],
        enabled: true,
        kinesisFirehoseDestination: {
          deliveryStreamArn: kinesisfirehoseDeliveryStream.deliveryStreamArn,
          iamRoleArn: sesRole.roleArn
        },
        name: `${this.stackName}-ConfigurationSetDestination`,
      },
    });


    // Create a glue databrew dataset based on the catalog table create above
    new CfnDataset(this, 'dataBrewDataset', {
      input: {
        s3InputDefinition: {
          bucket: destinationBucket.bucketName,
          key: 'raw/{year}/{month}/{day}/{hour}/',
        }
      },
      pathOptions: {
        lastModifiedDateCondition: {
          expression: 'relative_after :timeframe',
          valuesMap: [{
            value: '-1H',
            valueReference: ':timeframe'
          }]
        },
        parameters: [{
          datasetParameter: {
            name: 'year',
            type: 'Number',
            createColumn: true,
          },
          pathParameterName: 'year',
        },{
          datasetParameter: {
            name: 'month',
            type: 'Number',
            createColumn: true,
          },
          pathParameterName: 'month',
        },{
          datasetParameter: {
            name: 'day',
            type: 'Number',
            createColumn: true,
          },
          pathParameterName: 'day',
        },{
          datasetParameter: {
            name: 'hour',
            type: 'Number',
            createColumn: true,
          },
          pathParameterName: 'hour',
        }
      ],
      },
      name: 'SESDataBrewDataset',
      format: 'JSON'
    });

    const glueDatabase = new CfnDatabase(this, 'SESEventDataDatabase', {
      catalogId: this.account,
      databaseInput: {
        name: 'ses_event_data_database'
      }
    })

    // Create the glue crawler service role
    const crawlerServiceRole: iam.Role = new iam.Role(this, 'crawlerServiceRole', {
      assumedBy: new iam.ServicePrincipal('glue.amazonaws.com'),
      managedPolicies: [iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSGlueServiceRole')],
      description: 'A role used by Glue Crawler for data processing'
    });

    // Allow role to get access to the s3 bucket where logs are stored
    aggregatedBucket.grantReadWrite(crawlerServiceRole);

    new CfnCrawler(this, 'SESEventDataCrawler', {
      role: crawlerServiceRole.roleArn,
      targets: {
        s3Targets: [{
          path: `s3://${aggregatedBucket.bucketName}/partitioned/`
        }],
      },
      databaseName: (<CfnDatabase.DatabaseInputProperty>glueDatabase.databaseInput).name,
      name: 'SESEventDataCrawler',
      recrawlPolicy: {
        recrawlBehavior: 'CRAWL_EVERYTHING',
      },
      schedule: {
        scheduleExpression: 'cron(30 0/1 * * ? *)'
      },
      schemaChangePolicy: {
        updateBehavior: 'UPDATE_IN_DATABASE',
      },

    });

    // S3 bucket for Athena Workgroup
    const athenaResultsBucket = new s3.Bucket(this, 'AthenaResultsBucket', {
      bucketName: `${this.account}-${this.region}-athena-results-location`,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      encryption: s3.BucketEncryption.KMS_MANAGED,
      objectOwnership: s3.ObjectOwnership.BUCKET_OWNER_ENFORCED,
      enforceSSL: true,
    });

    // Athena workgroup
    new athena.CfnWorkGroup(this, 'SesAthenaWorkgroup', {
      name: 'SesAthenaWorkgroup',

      workGroupConfiguration: {
        resultConfiguration: {
          outputLocation: "s3://" + athenaResultsBucket.bucketName,
        },
      },
    }); 
  }
}