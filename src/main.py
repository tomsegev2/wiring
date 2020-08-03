# pylint: disable = redefined-outer-name
import asyncio
import os
import sys
from functools import partial
import signal

from aiohttp import web
from prometheus_client import start_http_server

from src.lib.config import Config
from src.lib.logger import setup_logger
from src.lib.sqs.client import SQSClient
from src.lib.s3.client import S3Client
from src.video_exporter import VideoExporter


app = None
site = None
logger = None
env = os.environ.get('BEAMUP_ENV', 'undefined')
VIDEO_EXPORTER = None


def _setup_http():
    global app
    app = web.Application()
    app.add_routes(
        [
            web.get(
                '/healthz',
                lambda request: web.Response(status=200)
            )
        ]
    )
    return app


async def main(loop):
    global logger
    global site
    global VIDEO_EXPORTER

    config = Config()
    await config.parse()

    logger = setup_logger(
        'video-exporter',
        config.get('logzio-token'),
        config['consoleLevel'],
        config.get('externalLevel', 'ERROR')
    )
    logger.debug(f'BEAMUP_ENV: {os.environ.get("BEAMUP_ENV")}')

    sqs_client = SQSClient(loop, config.get('sqs_endpoint'))
    s3_client = S3Client(loop, config.get('s3_endpoint'))

    VIDEO_EXPORTER = VideoExporter(
        env,
        s3_client,
        sqs_client,
        config['video-exporter-response']
    )

    asyncio.ensure_future(
        sqs_client.subscribe(
            config['video-exporter-request'],
            lambda msg: asyncio.ensure_future(
                VIDEO_EXPORTER.on_msg(msg)
            ),
            logger
        )
    )

    try:
        await s3_client.create_bucket(config['user_data_bucket'])
    # pylint: disable = broad-except
    except Exception as e:
        logger.debug(f'failed to create bucket: {e}')

    runner = web.AppRunner(_setup_http())
    await runner.setup()

    site = web.TCPSite(
        runner,
        port=config['port']
    )
    await site.start()
    start_http_server(8888)

    logger.debug('video exporter up')


async def _handle_sigterm():
    logger.debug('caught SIGTERM')
    await site.stop()
    loop = asyncio.get_event_loop()
    loop.stop()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.add_signal_handler(
        signal.SIGTERM,
        partial(
            asyncio.ensure_future,
            _handle_sigterm()
        )
    )

    try:
        asyncio.ensure_future(main(loop))
        loop.run_forever()
    finally:
        async def cleanup():
            await app.shutdown()
            await app.cleanup()
            sys.exit(0)

        loop.run_until_complete(cleanup())
