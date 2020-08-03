
import json
import traceback
import sys
import logging

from src.lib import read_mq_msg
from src.lib import parse_mq_fields


logger = logging.getLogger('video-exporter')


class VideoExporter:

    def __init__(self, env, s3_client, sqs_client, response_queue):
        self._env = env
        self._s3_client = s3_client
        self._sqs_client = sqs_client
        self._response_queue = response_queue

    async def on_msg(self, msg):
        log = dict(env=self._env)
        logger.info(
            f'received msg: {msg}',
            extra=log
        )

        data = await read_mq_msg(
            self._sqs_client,
            logger,
            self._response_queue,
            msg,
            self._env
        )
        if not data:
            return

        (
            bucket_key,
            level_id,
            results_bucket_path,
            selected_room_results
        ) = await parse_mq_fields(
            self._sqs_client,
            logger,
            self._response_queue,
            data,
            (
                'bucketKey', 'levelId',
                'resultsBucketPath', 'selectedRoomResults'),
            self._env
        )
        if not bucket_key:
            return

        log.update(data)

        try:
            logger.debug(f'fetching video results from {results_bucket_path}')
            video_results = await self._s3_client.get(
                bucket_key, results_bucket_path
            )
            video_results = json.loads(video_results)

            logger.debug('exporting video results...')
            exported_video_data = VideoExporter.export_video_data(
                video_results, level_id, selected_room_results
            )

            logger.debug(
                (
                    f'done. Found {len(exported_video_data)} cameras.'
                    f'Sending message'
                    )
                )
            data.update(exportedData=exported_video_data)
            await self._sqs_client.send_message(
                self._response_queue,
                json.dumps(data)
            )
        # pylint: disable=broad-except
        except Exception as e:
            log['error'] = str(e)
            log['traceback'] = '\n'.join(
                traceback.format_tb(sys.exc_info()[2])
            )
            logger.error(
                f'{log["error"]}\n{log["traceback"]}',
                extra=log
            )
            await self._sqs_client.send_message(
                self._response_queue,
                json.dumps(
                    dict(
                        status='failed',
                        error=str(e)
                    )
                )
            )

    @staticmethod
    def export_video_data(video_results, level_id, selected_room_results):
        devices = []
        for result_key_str, result in video_results.items():
            result_key = json.loads(result_key_str)
            if result_key['level'] != level_id:
                continue
            if not result:
                logger.debug(f'no results for room guid {result_key["room"]}')
                continue
            selected_id = selected_room_results.get(result_key['room'])
            specific_result =\
                result[selected_id]['simulationResult']['specificResult']
            for device in specific_result['devices']:
                position = device['top']['position']
                horizontal_rotation = device['horizontalRotation']
                devices.append(
                    dict(
                        x=position['x'],
                        y=position['y'],
                        z=position['z'],
                        horRotation=horizontal_rotation
                    )
                )
        return devices
