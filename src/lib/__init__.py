
import traceback
import json
import sys
import os
import pathlib


ROOT_PATH = str(
    pathlib.Path(
        os.path.dirname(os.path.realpath(__file__))
    ).parent.parent
)


async def read_mq_msg(
        mq_client, logger, response_queue, msg, env
):
    try:
        return json.loads(msg)
    except json.decoder.JSONDecodeError as e:
        log = dict(
            env=env,
            error=str(e),
            traceback='\n'.join(
                traceback.format_tb(sys.exc_info()[2])
            )
        )
        logger.error(
            f'{log["error"]}\n{log["traceback"]}',
            extra=log
        )
        await mq_client.send_message(
            response_queue,
            json.dumps(dict(
                status='failed',
                error=str(e)
            ))
        )


async def parse_mq_fields(
        mq_client, logger, response_queue, data, expected_keys, env
):
    values = []
    missing_keys = set()
    for key in expected_keys:
        try:
            values.append(data[key])
        except KeyError:
            missing_keys.add(key)

    if missing_keys:
        error = f'missing keys in message: {missing_keys}'
        log = dict(
            env=env,
            error=error
        )
        logger.error(
            error,
            extra=log
        )
        await mq_client.send_message(
            response_queue,
            json.dumps(dict(
                status='failed',
                error=error
            ))
        )
        return (None,) * len(expected_keys)

    return values
