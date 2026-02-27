import logging
from main import logging

# Set up logging
logging.basicConfig(filename='script.log', level=logging.INFO)

def test_logging():
    # Log a message
    logging.info('Test message')

    # Assert that log file was created
    assert os.path.exists('script.log')
