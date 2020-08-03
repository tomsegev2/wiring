
import asyncio
import os

import aiobotocore


class S3Client:

    def __init__(self, loop=None, endpoint=None):
        loop = loop if loop else asyncio.get_event_loop()
        session = aiobotocore.get_session(loop=loop)
        self._client = session.create_client('s3', endpoint_url=endpoint)
        self._queue_urls = {}

    async def close(self):
        await self._client.close()

    async def create_bucket(self, bucket_name, **kwargs):
        region = kwargs.pop(
            'LocationConstraint',
            os.environ.get('AWS_DEFAULT_REGION')
        )

        bucket_config = dict(kwargs)
        if region and region != 'us-east-1':
            # https://github.com/heptio/velero/pull/285/
            bucket_config['LocationConstraint'] = region

        config = dict(Bucket=bucket_name)
        if bucket_config:
            config['CreateBucketConfiguration'] = bucket_config

        response = await self._client.create_bucket(**config)
        S3Client._assert_status(response, 200)

    async def delete_bucket(self, bucket_name):
        response = await self._client.delete_bucket(
            Bucket=bucket_name
        )
        S3Client._assert_status(response, 204)

    async def put(self, bucket_name, key, data):
        response = await self._client.put_object(
            Bucket=bucket_name, Key=key, Body=data
        )
        S3Client._assert_status(response, 200)

    async def get(self, bucket_name, key):
        response = await self._client.get_object(
            Bucket=bucket_name, Key=key
        )
        S3Client._assert_status(response, 200)

        buffer = b''
        async for data in response['Body'].iter_chunks(1024 * 80):
            if not data:
                break
            buffer += data
        return buffer

    async def delete(self, bucket_name, key):
        response = await self._client.delete_object(
            Bucket=bucket_name, Key=key
        )
        S3Client._assert_status(response, 204)

    @staticmethod
    def _assert_status(response, code):
        assert response['ResponseMetadata']['HTTPStatusCode'] == code
