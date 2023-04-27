const aws = require("aws-sdk");
const s3 = new aws.S3({ apiVersion: "2006-03-01" });

const sourcePrefix = process.env.SRC_PREFIX;
const destinationBucket = process.env.DEST_BUCKET;

exports.handler = async (event, context) => {
//console.log("Received event:", JSON.stringify(event, null, 2));

// Get the object from the event
const bucket = event.Records[0].s3.bucket.name;
const key = decodeURIComponent(
    event.Records[0].s3.object.key.replace(/\+/g, " ")
);

if (!key.startsWith(`${sourcePrefix}year=`)) {
    //console.log(`Key ${key} does not start with '${sourcePrefix}year='`);
    return;
}

var copyParams = {
    Bucket: destinationBucket,
    CopySource: encodeURI(`/${bucket}/${key}`),
    Key: encodeURI(key),
};

//console.log(`Copying object to ${copyParams.Bucket}/${copyParams.Key}`);

try {
    await s3.copyObject(copyParams, function (err, data) {
    if (err) console.log(err, err.stack); // an error occurred
    //else console.log('Response: ' + JSON.stringify(data, null, 2)); // successful response
    }).promise();
} catch (err) {
    console.log(err);
    throw new Error(err);
}
};