import json
import os
from main import config

# Set up test configuration file
with open('config.json', 'w') as f:
    json.dump({'dropbox': {'access_token': 'test_token', 'folder': '/test/folder'}, 'aws': {'access_key_id': 'test_key', 'secret_access_key': 'test_secret', 'bucket': 'test_bucket', 'path': '/test/path'}}, f)

def test_config():
    # Load configuration
    global config
    with open('config.json') as f:
        config = json.load(f)

    # Assert that configuration was loaded correctly
    assert config['dropbox']['access_token'] == 'test_token'
    assert config['dropbox']['folder'] == '/test/folder'
    assert config['aws']['access_key_id'] == 'test_key'
    assert config['aws']['secret_access_key'] == 'test_secret'
    assert config['aws']['bucket'] == 'test_bucket'
    assert config['aws']['path'] == '/test/path'