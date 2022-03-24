import os

import boto3


# ============================================
#              get_aws_resource
# ============================================
def get_aws_resource(resourceType, protected=True):
    """
    Sets up an AWS resource object.

    Parameters
    ----------
    resourceType : str
        The type of resource to set up (e.g., 's3').

    protected : bool (optional)
        If True, attempts to use the environment variables
        `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` to authenticate
        the download. Otherwise, the object being downloaded is assumed
        to be public.

    Returns
    -------
    resource : boto3.ServiceResource
        Object providing and interface to the desired AWS resource.
    """
    if protected:
        resource = boto3.resource(
            resourceType,
            aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
        )
    else:
        resource = boto3.resource(resourceType)

    return resource
