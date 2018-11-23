# file_hash
File hasing plugin for Flexget

## Notes
-   Currently, in interest of supporting Python 2.7 this plugin operates linearlly.
-   I have plans to add support for [asyncio](https://docs.python.org/3/library/asyncio.html) for those Python versions that do support it
-   **HEY, LISTEN:** Even though `stop` and `time` are in the schema, they are not implemented yet.

## Usage
- The default hashing method depends on your python installation:
  - If you have Python 3.6+, it will use [BLAKE2b](https://en.wikipedia.org/wiki/BLAKE_%28hash_function%29#BLAKE2)
  - Otherwise, it will use [MD5](https://en.wikipedia.org/wiki/MD5)
- The list of usable methods is determined by `hashlib.algorithms_available`
- To use the default hashing method:
  - `file_hash: yes`
- To use a custom hashing method (for example sha1):
  - `file_hash: sha1`
- You may choose ***MAX*** 2 of the following options: `size`, `start`, `stop`.
  - Using all three of these together sets up a chance that the difference between `start` and `stop` could be either smaller or larger than `size`.
- If the `start` position is larger than size of the file, one of two things will happen:
  1. If the size of the file is smaller than `size`, `start` is set to 0, ***OR***
  1. If the size of the file is larger than `size` (but still smaller than `start`), `start` will be set to the size of the file minus `size`
- To use advanced options, see below

## Example
```yml
templates:
  
  file_hash_basic:
    <<: *any-file-input-plugin
    file_hash: yes
    
  file_hash_basic_extended: # These are the settings when you use "file_hash: yes"
    <<: *any-file-input-plugin
    file_hash:
      algorithm: blake2b # Or if your system doesn't have blake2b, this will be md5
      size: 25
      start: 50
    
  file_hash_algorithm:
    <<: *any-file-input-plugin
    file_hash: sha1
    
  file_hash_advanced:
    <<: *any-file-input-plugin
    file_hash:
      algorithm: sha256 # Optional, default will be chosen if this is not set
      size: 1 # Will hash 1MiB of the given file
      start: 25 # Will start at 25MiB into the file, see usage for how this applies to files smaller than this value
```
