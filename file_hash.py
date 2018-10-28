""" Hash your files for easy identification """
from __future__ import unicode_literals, division, absolute_import

import hashlib
import logging
import math
import os
from builtins import *  # noqa pylint: disable=unused-import, redefined-builtin

from flexget import plugin
from flexget.event import event

PLUGIN_ID = 'file_hash'

log = logging.getLogger(PLUGIN_ID)

size_units = object
size_units.B = 1
size_units.KB = size_units.B * 1024
size_units.MB = size_units.KB * 1024
size_units.GB = size_units.MB * 1024


class FileHashPlugin(object):
    """ Task class that does the hashing """

    schema = {
        'oneOf': [
            {'type': 'boolean'},
            {'type': 'string',
             'enum': list(hashlib.algorithms_available)}
        ]
    }

    @staticmethod
    def __strict_boolean(check):
        if isinstance(check, bool) and check:
            return True
        return False

    @staticmethod
    def __default_algo():
        return 'blake2b' if 'blake2b' in hashlib.algorithms_available else 'md5'

    def __get_algo(self, config):
        return self.__default_algo() if self.__strict_boolean(config) else config

    def on_task_metainfo(self, task, config):
        """ basically main() """
        log.info('Starting file_hash')
        algorithm = self.__get_algo(config)
        hasher = hashlib.new(algorithm)
        for entry in task.entries:
            log.verbose('Hasing %s', entry['location'])
            log.verbose('Hasing with algorithm: %s', algorithm)
            current_hasher = hasher.copy()
            with open(entry['location'], 'rb') as to_hash:
                to_hash_size = to_hash.tell()
                hundered_meg = size_units.MB * 100
                total_pieces = math.ciel(to_hash_size / hundered_meg)
                i = 0
                while True:
                    i += 1
                    log.debug('Hashing piece: %s/%s', i, total_pieces)
                    piece = to_hash.read(size_units.MB * 100)
                    if not piece:
                        break
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
