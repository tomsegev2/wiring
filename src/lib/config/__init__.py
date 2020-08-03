
import base64
import json
import os

from src.lib import ROOT_PATH
from src.lib.s3.client import S3Client


class ConfigError(Exception):
    pass


class Config:

    def __init__(self, loop=None):
        self._s3_client = S3Client(loop=loop)
        self._config = self._read_config()
        self._validate_config()
        self._kv = {}

    @property
    def s3_client(self):
        return self._s3_client

    def __getitem__(self, key):
        return self._kv[key]

    def get(self, key, default=None):
        return self._kv.get(key, default)

    @staticmethod
    def _read_config():
        try:
            config_name = f'config.{os.environ["BEAMUP_ENV"]}.json'
        except KeyError:
            raise ConfigError('BEAMUP_ENV environment variable is missing.')

        try:
            with open(
                    os.path.join(ROOT_PATH, 'config', config_name),
                    'r'
            ) as f:
                return json.load(f)
        except FileNotFoundError:
            raise ConfigError(f'{config_name} is missing.')

    def _validate_config(self):
        for config in self._config.values():
            if not isinstance(config, dict):
                continue
            if config['secret']:
                assert 'bucket' in config and 'key' in config
            else:
                assert 'value' in config

    async def parse_key(self, key):
        config = self._config[key]
        if config['secret']:
            body_stream = await self._s3_client.get(
                config['bucket'], config['key']
            )
            if isinstance(body_stream, bytes):
                if config.get('bytes'):
                    body = body_stream
                else:
                    body = body_stream.decode().strip()
            else:
                b64_body = await body_stream.read()
                body = base64.b64decode(b64_body).decode()
            self._kv[key] = body
        else:
            self._kv[key] = config['value']

        if len(self._kv) == len(self._config):
            await self._s3_client.close()

    async def parse(self, delayed_keys=()):
        for key, config in self._config.items():
            if not isinstance(config, dict):
                self._kv[key] = config
                if len(self._kv) == len(self._config):
                    await self._s3_client.close()
                continue
            if key in delayed_keys:
                continue
            await self.parse_key(key)
