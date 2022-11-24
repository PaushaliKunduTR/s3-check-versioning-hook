import logging
from typing import Any, MutableMapping, Optional
import botocore

from cloudformation_cli_python_lib import (
    BaseHookHandlerRequest,
    HandlerErrorCode,
    Hook,
    HookInvocationPoint,
    OperationStatus,
    ProgressEvent,
    SessionProxy,
    exceptions,
)

from .models import HookHandlerRequest, TypeConfigurationModel

# Use this logger to forward log messages to CloudWatch Logs.
LOG = logging.getLogger(__name__)
LOG.setLevel(logging.INFO)
TYPE_NAME = "paushalisb::guardraildemo::hook"

hook = Hook(TYPE_NAME, TypeConfigurationModel)
test_entrypoint = hook.test_entrypoint


def _isBucketExcluded(bucketName: str, excludedBuckets: str):
    LOG.info(f'{excludedBuckets}')
    LOG.info(f'bucketName: {bucketName}')
    bucketsToExclude = [bucket.strip() for bucket in excludedBuckets.split(',')]
    for ExcludedBucket in bucketsToExclude:
        LOG.info(f'{ExcludedBucket} in Excluded List')
        LOG.info(f'**Checking if bucket name {bucketName} is in Excluded List...')
        if bucketName in ExcludedBucket:
            LOG.info(f'{ExcludedBucket} = {bucketName}')
            return True
    return False


def _validate_bucket_versioning(targetTypeName: str, s3Bucket: MutableMapping[str, Any], excludedBuckets: str) -> ProgressEvent:
    status = None
    message = ""
    error_code = None

    status = OperationStatus.FAILED

    if s3Bucket:

        s3BucketName = s3Bucket.get("BucketName")
        
        if not s3BucketName:
            LOG.info('**Bucket Name not specified on template.')
        else:
            LOG.info(f"**Bucket name: {s3BucketName}")

        if _isBucketExcluded(s3BucketName, excludedBuckets):
            status = OperationStatus.SUCCESS
            message = f"Versioning is not required for bucket named: {s3BucketName}."
        else:
            LOG.info(f"**The bucket name {s3BucketName} is not excluded from the versioning check.")

            VersioningConfiguration = s3Bucket.get("VersioningConfiguration")
            LOG.info(f"{VersioningConfiguration}")
            if VersioningConfiguration:
                status = VersioningConfiguration.get('Status')
                LOG.info(f"{status}")
                if status in 'Enabled':
                    status = OperationStatus.SUCCESS
                    message = f"S3 Versioning enabled for bucket named {s3BucketName}"
                else:
                    status = OperationStatus.FAILED
                    message = f"S3 Versioning is not enabled correctly for bucket named {s3BucketName}"
            else:
                status = OperationStatus.FAILED
                message = f"S3 Versioning is not specified for bucket named {s3BucketName}"
    else:
        message = "Resource properties for the S3 Bucket target model are empty"

    LOG.info(f"Results Message: {message}")
    LOG.debug(f"DEBUG Results Message: {message}")

    if status == OperationStatus.FAILED:
        error_code = HandlerErrorCode.NonCompliant

    return ProgressEvent(
        status=status,
        message=message,
        errorCode=error_code
    )


@hook.handler(HookInvocationPoint.CREATE_PRE_PROVISION)
def pre_create_handler(
        session: Optional[SessionProxy],
        request: HookHandlerRequest,
        callback_context: MutableMapping[str, Any],
        type_configuration: TypeConfigurationModel
) -> ProgressEvent:

    progress: ProgressEvent = ProgressEvent(
        status=OperationStatus.IN_PROGRESS
    )
    
    target_name = request.hookContext.targetName

    try:

        LOG.debug("Hook context:")
        LOG.debug(request.hookContext)

        if "AWS::S3::Bucket" == target_name:
            progress = _validate_bucket_versioning(target_name, 
                request.hookContext.targetModel.get("resourceProperties"), 
                type_configuration.excludedBuckets)
        else:
            raise exceptions.InvalidRequest(f"Unknown target type: {target_name}")

    except exceptions.InvalidRequest as e:
        progress.status = OperationStatus.FAILED
        progress.message = "Unknown target type: {target_name}"
    except BaseException as e:
        progress = ProgressEvent.failed(HandlerErrorCode.InternalFailure, f"Unexpected error {e}")

    return progress


@hook.handler(HookInvocationPoint.UPDATE_PRE_PROVISION)
def pre_update_handler(
        session: Optional[SessionProxy],
        request: BaseHookHandlerRequest,
        callback_context: MutableMapping[str, Any],
        type_configuration: TypeConfigurationModel
) -> ProgressEvent:
    target_model = request.hookContext.targetModel
    progress: ProgressEvent = ProgressEvent(
        status=OperationStatus.IN_PROGRESS
    )
    target_name = request.hookContext.targetName

    try:

        LOG.debug("Hook context:")
        LOG.debug(request.hookContext)

        # Reading the Resource Hook's target new properties
        resource_properties = target_model.get("resourceProperties")

        # Only need to check if the new resource properties match the required TypeConfiguration.
        # This will block automatically if they are trying to remove a permission boundary.
        if "AWS::S3::Bucket" == target_name:
            progress = _validate_bucket_versioning(target_name, 
                        resource_properties,
                        type_configuration.excludedBuckets)
        else:
            raise exceptions.InvalidRequest(f"Unknown target type: {target_name}")

    except exceptions.InvalidRequest as e:
        progress.status = OperationStatus.FAILED
        progress.message = "Unknown target type: {target_name}"
    except BaseException as e:
        progress = ProgressEvent.failed(HandlerErrorCode.InternalFailure, f"Unexpected error {e}")

    return progress


@hook.handler(HookInvocationPoint.DELETE_PRE_PROVISION)
def pre_delete_handler(
        session: Optional[SessionProxy],
        request: BaseHookHandlerRequest,
        callback_context: MutableMapping[str, Any],
        type_configuration: TypeConfigurationModel
) -> ProgressEvent:
    
    # If deleting a bucket - no additional checks are needed.
    return ProgressEvent(
        status=OperationStatus.SUCCESS
    )

