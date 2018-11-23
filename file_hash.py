"""Hash your files for easy identification."""

import hashlib
import logging
import os
from typing import Dict
from builtins import *  # noqa pylint: disable=unused-import, redefined-builtin

from flexget import plugin
from flexget.event import event

from .cunit import IECUnit

PLUGIN_ID = 'file_hash'

log = logging.getLogger(PLUGIN_ID)


class FileHashPlugin(object):
    """
    Task class that does the hashing.

    By default file_hash will:
    - Use blake2b if it is available, otherwise it will use MD5
    - Start at 50MiB into the file
      - If the file is less than 50MiB, it starts at the beginning
    - Hashes 25MiB of the file after the starting point
      - If the file does not have 25MiB after the starting point, it will hash from the starting point to the end
    - Choose MAX two 'size', 'start', 'stop'

    Examples:

    # Use file_hash with the default settings.
    file_hash: yes

    # Use sha1 with the rest of the default settings
    file_hash: sha1

    # Hash 1MiB, 25MiB into the file with algorithm SHA256
    file_hash:
      algorithm: sha256
      size: 1
      start: 25

    # Hash from 25MiB in to 35MiB in
    file_hash:
      start: 25
      stop: 35
    """

    @staticmethod
    def __default_algo():
        return 'blake2b' if 'blake2b' in hashlib.algorithms_available else 'md5'

    hash_size_default = 25
    hash_start_default = 50

    schema = {
        'oneOf': [
            {'type': 'boolean'},
            {'type': 'string',
             'enum': list(hashlib.algorithms_available)},
            {'type': 'object',
             'properties': {
                 'algorithm': {
                     'type': 'string',
                     'enum': list(hashlib.algorithms_available)},
                 'size': {'type': 'integer', 'default': hash_size_default},
                 'start': {'type': 'integer', 'default': hash_start_default},
                 'stop': {'type': 'integer'},
                 'time': {'type': 'boolean', 'default': 'boolean'}}},
        ],
    }

    plugin_fields = {'file_hash_type', 'file_hash_hash', 'file_hash_modified', 'file_hash_bytes'}

    @staticmethod
    def __strict_boolean(check):
        if isinstance(check, bool) and check:
            return True
        return False

    def __get_algo(self, config):
        return self.__default_algo()

    def compare_entry(self, entry, config):
        if 'file_hash' in entry:
            file_hash = entry['file_hash']
            match_algo = file_hash.algorithm == self.__get_algo(config)
            match_file_size = file_hash.file_size == os.path.getsize(entry['location'])
            match_modified = file_hash.modified == os.path.getmtime(entry['location'])
            match_start = file_hash.start == config.get('start')
            match_stop = file_hash.stop == config.get('stop')
            match_chunk_size = file_hash.chunk_size == config.get('size')
            match_strict = match_file_size and match_start and match_stop and match_chunk_size
            if match_algo and match_strict:
                return True
        return False

    def on_task_metainfo(self, task, config):
        """Call the plugin."""
        log.info('Starting file_hash')
        # todo: add conditions to adapt to users' configuration
        if self.__strict_boolean(config):
            config = {True}
        hash_portion = {
            'algorithm': self.__get_algo(config),
            'size': IECUnit.MiB * (config['size'] if 'size' in config else self.hash_size_default),
            'start': IECUnit.MiB * (config['start'] if 'start' in config else self.hash_start_default),
            'stop': IECUnit.MiB * (config['stop'] if 'stop' in config else -1),
        }
        hasher = hashlib.new(hash_portion['algorithm'])
        log.verbose('Hasing with algorithm: %s', hash_portion['algorithm'])
        log.debug('Hashing %s MiB of each file.', hash_portion['size'])
        log.debug('Hashing starting %s MiB into file.', hash_portion['start'])
        log.debug('Hashing ending at %s MiB.', hash_portion['stop'])
        for entry in task.entries:
            file_size = os.path.getsize(entry['location'])
            if self.compare_entry(entry, config):
                log.verbose('This file seems to be unmodified, skipping')
                continue
            log.verbose('Hasing %s', entry['location'])
            current_hasher = hasher.copy()
            tmp_hash_portion_start = -1
            if file_size < hash_portion['start']:
                log.debug('The file is only %s MiB, adjusting start location.', float(file_size / IECUnit.MiB))
                if file_size < hash_portion['size']:
                    log.debug('The file is less than the set size to to hash, setting start position to 0')
                    tmp_hash_portion_start = 0
                else:
                    tmp_hash_portion_start = file_size - hash_portion['size']
                    log.debug('The size of the file is greater than the set size to hash, \
                               setting start position to %s MiB', tmp_hash_portion_start)
            with open(entry['location'], 'rb') as to_hash:
                to_hash.seek(tmp_hash_portion_start if tmp_hash_portion_start > -1 else hash_portion['start'])
                piece = to_hash.read(hash_portion['size'])
                current_hasher.update(piece)
                file_digest = current_hasher.hexdigest()
                file_modified = os.path.getmtime(entry['location'])
                filehash = FileHash(hash_portion, file_digest, file_modified, file_size)
                entry['file_hash'] = filehash
                log.debug(filehash)
                to_hash.close()


class FileHash(object):
    """Store the information from the hashing."""

    algorithm = None
    file_hash = None
    modified = None
    start = None
    stop = None
    chunk_size = None
    size = None

    def __init__(self, config_settings: Dict, file_hash, modified, size):
        """
        Initialize a FileHash object.

        config_settings -- ends up being the config for the plugin
        file_hash -- the hash of the file
        modified -- last time the file was modified
        size -- size of the file in bytes
        """
        self.algorithm = config_settings['algorithm']
        self.start = config_settings['start']
        self.stop = config_settings['stop']
        self.chunk_size = config_settings['size']
        self.file_hash = file_hash
        self.modified = modified
        self.size = size

    def __repr__(self):
        """Represent a FileHash."""
        return '<FileHash: \
                algorithm = {0}, \
                start = {1}, stop = {2}, \
                chunk_size = {3}, \
                file_hash = {4}, \
                modified = {5}, \
                size = {6}'.format(
                    self.algorithm,
                    self.start, self.stop,
                    self.chunk_size,
                    self.file_hash,
                    self.modified,
                    self.size)



@event('plugin.register')
def register_plugin():
    plugin.register(FileHashPlugin, PLUGIN_ID, api_ver=2, interfaces=['task', 'series_metainfo', 'movie_metainfo'])
