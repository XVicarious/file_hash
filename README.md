# file_hash
File hasing plugin for Flexget

## Usage
- The default hashing method depends on your python installation:
  - If you have Python 3.6+, it will use [BLAKE2b](https://en.wikipedia.org/wiki/BLAKE_%28hash_function%29#BLAKE2)
  - Otherwise, it will use [MD5](https://en.wikipedia.org/wiki/MD5)
- The list of usable methods is determined by `hashlib.algorithms_available`
- To use the default hashing method:
  - `file_hash: yes`
- To use a custom hashing method (for example sha1):
  - `file_hash: sha1`
