import os

import boto3


# ============================================
#                 s3_download
# ============================================
def s3_download(bucketName, objectName, outputFile, protected=False):
    """
    Downloads the file specified by `path` from the S3 bucket with the
    given name.

    Parameters
    ----------
    bucketName : str
        The name of the AWS S3 bucket to download from.

    objectName : str
        The object to download from the bucket.

    outputFile : str
        The name of the file to save the downloaded contents to.

    protected : bool (optional)
        If True, attempts to use the environment variables
        `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` to authenticate
        the download. Otherwise, the object being downloaded is assumed
        to be public.
    """
    if protected:
        s3 = boto3.resource(
            "s3",
            aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"]
        )
    else:
        s3 = boto3.resource("s3")

    s3.Bucket(bucketName).download_file(objectName, outputFile)
