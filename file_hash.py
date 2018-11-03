""" Hash your files for easy identification """
from __future__ import unicode_literals, division, absolute_import

import hashlib
import logging
import os
from builtins import *  # noqa pylint: disable=unused-import, redefined-builtin

from flexget import plugin
from flexget.event import event

from cunit import IECUnit

PLUGIN_ID = 'file_hash'

log = logging.getLogger(PLUGIN_ID)


class FileHashPlugin(object):
    """ Task class that does the hashing

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
                 'size': {'type': 'integer', 'default': 25},
                 'start': {'type': 'integer', 'default': 50},
                 'stop': {'type': 'integer'},
                 'time': {'type': 'boolean', 'default': 'boolean'}}}
        ]
    }

    plugin_fields = {'file_hash_type', 'file_hash_hash', 'file_hash_modified', 'file_hash_bytes'}

    @staticmethod
    def __strict_boolean(check):
        if isinstance(check, bool) and check:
            return True
        return False

    def __get_algo(self, config):
        return self.__default_algo() if self.__strict_boolean(config) else config

    def on_task_metainfo(self, task, config):
        """ basically main() """
        log.info('Starting file_hash')
        algorithm = self.__get_algo(config)
        hasher = hashlib.new(algorithm)
        log.verbose('Hasing with algorithm: %s', algorithm)
        # todo: add conditions to adapt to users' configuration
        if self.__strict_boolean(config):
            config = {True}
        hash_portion_size = IECUnit.MiB * (config['size'] if 'size' in config else 25)
        log.debug('Hashing %s MiB of each file.', hash_portion_size)
        hash_portion_start = IECUnit.MiB * (config['start'] if 'start' in config else 50)
        log.debug('Hashing starting %s MiB into file.', hash_portion_start)
        hash_portion_stop = IECUnit.MiB * (config['stop'] if 'stop' in config else -1)
        log.debug('Hashing ending at %s MiB.', hash_portion_stop)
        for entry in task.entries:
            file_size = os.path.getsize(entry['location'])
            if all(field in entry for field in self.plugin_fields):
                if entry['file_hash_type'] == algorithm:
                    if entry['file_hash_modified'] == os.path.getmtime(entry['location']):
                        if entry['file_hash_bytes'] == file_size:
                            log.verbose('This file seems to be unmodified, skipping')
                            continue
            log.verbose('Hasing %s', entry['location'])
            current_hasher = hasher.copy()
            with open(entry['location'], 'rb') as to_hash:
                tmp_hash_portion_start = hash_portion_start
                if file_size < tmp_hash_portion_start:
                    log.debug('The file is only %s MiB, adjusting start location.', float(file_size / IECUnit.MiB))
                    if file_size < hash_portion_size:
                        log.debug('The file is less than the set size to to hash, setting start position to 0')
                        tmp_hash_portion_start = 0
                    else:
                        tmp_hash_portion_start = file_size - hash_portion_size
                        log.debug('The size of the file is greater than the set size to hash, \
                                   setting start position to %s MiB', tmp_hash_portion_start)
                to_hash.seek(tmp_hash_portion_start)
                piece = to_hash.read(hash_portion_size)
                current_hasher.update(piece)
                entry['file_hash_type'] = algorithm
                entry['file_hash_hash'] = current_hasher.hexdigest()
                entry['file_hash_modified'] = os.path.getmtime(entry['location'])
                entry['file_hash_bytes'] = os.path.getsize(entry['location'])
                log.debug('%s|%s|%s|%s',
                          entry['title'], entry['file_hash_hash'],
                          entry['file_hash_modified'], entry['file_hash_bytes'])
                to_hash.close()


@event('plugin.register')
def register_plugin():
    plugin.register(FileHashPlugin, PLUGIN_ID, api_ver=2, interfaces=['task', 'series_metainfo', 'movie_metainfo'])
