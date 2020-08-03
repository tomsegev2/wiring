
import asyncio
from uuid import uuid4

from botocore.exceptions import ClientError
import aiobotocore
from aiohttp.client_exceptions import ClientConnectorError


class SQSClient:

    def __init__(self, loop=None, endpoint=None):
        loop = loop if loop else asyncio.get_event_loop()
        session = aiobotocore.get_session(loop=loop)
        self._client = session.create_client('sqs', endpoint_url=endpoint)
        self._queue_urls = {}
        self._unfinished_messages = []
        self._sigterm_recieved = None

    async def _create_queue(self, queue_name):
        sleep_inc = 5
        upper_boundry = sleep_inc * (2 ** 7)

        while True:
            try:
                result = await self._client.create_queue(
                    QueueName=queue_name,
                    Attributes=dict(
                        ContentBasedDeduplication='false',
                        FifoQueue='true',
                        DelaySeconds='1',
                        MessageRetentionPeriod='86400',
                        ReceiveMessageWaitTimeSeconds='1',
                        VisibilityTimeout=str(60 * 60),
                    )
                )

                self._queue_urls[queue_name] = result['QueueUrl']
                break
            except ClientConnectorError:
                await asyncio.sleep(sleep_inc)
                sleep_inc = sleep_inc * 2
                if sleep_inc > upper_boundry:
                    break
            except ClientError as err:
                if 'Queue already exists' in err.response['Error']['Code']:
                    queue_url_request = await self._client.get_queue_url(
                        QueueName=queue_name
                    )
                    self._queue_urls[queue_name] =\
                        queue_url_request['QueueUrl']
                else:
                    raise

    async def send_message(self, queue_name, message):
        if queue_name not in self._queue_urls:
            await self._create_queue(queue_name)

        url = self._queue_urls[queue_name]
        await self._client.send_message(
            QueueUrl=url,
            MessageBody=message,
            MessageGroupId=str(uuid4()),
            MessageDeduplicationId=str(uuid4()),
        )

    async def subscribe(self, queue_name, callback, logger):
        if queue_name not in self._queue_urls:
            await self._create_queue(queue_name)

        url = self._queue_urls[queue_name]
        while True:
            await asyncio.sleep(1)

            if self._sigterm_recieved:
                break

            result = await self._client.receive_message(QueueUrl=url)
            if 'Messages' not in result:
                await asyncio.sleep(1)
                continue

            for message in result['Messages']:
                self._unfinished_messages.append({
                    'ReceiptHandle': message['ReceiptHandle'],
                    "QueueUrl": url,
                })

            for message in result['Messages']:
                await callback(message['Body'])

                self.remove_message_by_reciept_handle(message['ReceiptHandle'])

                try:
                    await self._client.delete_message(
                        QueueUrl=url,
                        ReceiptHandle=message['ReceiptHandle']
                    )
                except ClientError as e:
                    logger.error(f'failed to delete message: {str(e)}')

    async def change_visibility_timeout(self, visibility_timeout):
        for (_, value) in self._unfinished_messages:

            self._client.change_message_visibility(
                QueueUrl=value['QueueUrl'],
                ReceiptHandle=value['ReceiptHandle'],
                VisibilityTimeout=visibility_timeout
            )

    def remove_message_by_reciept_handle(self, reciept_handle):
        i = 0
        index = -1

        while i < len(self._unfinished_messages):
            if self._unfinished_messages[i]['ReceiptHandle'] == reciept_handle:
                index = i
            i += 1

        if index > -1:
            del self._unfinished_messages[index]

    async def close(self):
        self._sigterm_recieved = True
        await asyncio.sleep(2)
        await self.change_visibility_timeout(0)
        await self._client.close()
