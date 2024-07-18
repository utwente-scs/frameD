# FrameD - Identification of Embedded Frameworks in Firmware Images

This is the official artifact of the CyberICPS 2024 paper `frameD: Toward Automated Identication of Embedded Frameworks in Firmware Images`.

## Preperation
### Option 1 - Docker
```bash
docker build -t framed . && docker run -it --rm framed
```

### Option 2 - Python virtual environment
Setup a Python virtual environment and install the requirements:
```bash
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

## Building Framework string database

Generate a GitHub token to use their API: https://github.com/settings/tokens
Put the token in `configuration.py`.
Build the framework string collections:
```bash
python3 ./build_framework_string_db.py
```
This will query GitHub for relevant project, and will clone them locally.
This can take a couple of hours.

Next, build the library string collections:
```bash
python3 ./build_library_string_db.py
```
This is a bit quicker than the previous step!


## Matching firmware blobs
```bash
python3 ./match_bin.py /path/to/bin/file
```