# file_hash
File hasing plugin for Flexget

## Notes
- Currently, in interest of supporting Python 2.7 this plugin operates linearlly.
- I have plans to add support for [asyncio](https://docs.python.org/3/library/asyncio.html) for those Python versions that do support it

## Usage
- The default hashing method depends on your python installation:
  - If you have Python 3.6+, it will use [BLAKE2b](https://en.wikipedia.org/wiki/BLAKE_%28hash_function%29#BLAKE2)
  - Otherwise, it will use [MD5](https://en.wikipedia.org/wiki/MD5)
- The list of usable methods is determined by `hashlib.algorithms_available`
- To use the default hashing method:
  - `file_hash: yes`
- To use a custom hashing method (for example sha1):
  - `file_hash: sha1`
