import threading
import time

from util import monitor_run
from switcher_client import Client, ContextOptions

SWITCHER_KEY = 'CLIENT_PYTHON_FEATURE'

def setup_context(options: ContextOptions = ContextOptions()):
    Client.build_context(
        domain='Switcher API',
        url='https://api.switcherapi.com',
        api_key='[API_KEY]',
        component='switcher-client-python',
        environment='default',
        options=options
    )

def simple_api_call():
    """ Use case: Check Switcher using remote API """
    setup_context(ContextOptions(
        local=False
    ))

    switcher = Client.get_switcher(SWITCHER_KEY)
    
    monitor_thread = threading.Thread(target=monitor_run, args=(switcher,), daemon=True)
    monitor_thread.start()

try:
    # Replace with use case
    simple_api_call()
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nStopping...")