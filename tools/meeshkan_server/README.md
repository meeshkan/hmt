# API recording proxy

## Installation
The recording proxy is an additional tool provide alongside Meeshkan CLI tool. 
To install it run:
```bash
pip install meeshkan[proxy]
```
## Usage
1. Start it by running:
```bash
python -m meeshkan_proxy record
```
2. Change external API calls from http(s)://host/path?query=value 
to http://localhost:8899/http(s)/host/path?query=value. For example, 
https://api.imgur.com/3/gallery/search/time/all/1?q=Finland should be changed to
http://localhost:8899/https/api.imgur.com/3/gallery/search/time/all/1?q=Finland
3. Run your scripts.
4. Now you should have the logs folder with jsonl files and the __unmock__ folder with ready openapi schemes in your unmock-sniffer folder. 
5. Start unmock-server by running:
```bash
npx unmock-server
```
6. Stop and start Meeshkan Proxy in mocking mode:
```bash
python -m meeshkan_proxy mock
```
7. You don't have to change anything in your client script. It should work with mocks now. You can switch between mocking, recording, accessing real APIs
by switching Meeshkan Proxy modes.

