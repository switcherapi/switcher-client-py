import threading
import time

from util import monitor_run
from switcher_client.lib.globals.global_context import DEFAULT_ENVIRONMENT
from switcher_client.lib.globals.global_snapshot import LoadSnapshotOptions
from switcher_client import Client, ContextOptions

SWITCHER_KEY = 'CLIENT_PYTHON_FEATURE'
LOOP = True

def setup_context(options: ContextOptions = ContextOptions(), environment = DEFAULT_ENVIRONMENT):
    Client.build_context(
        domain='Switcher API',
        url='https://api.switcherapi.com',
        api_key='[API_KEY]',
        component='switcher-client-python',
        environment=environment,
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

def simple_api_call_with_throttle():
    """ Use case: Check Switcher using remote API with throttle """
    setup_context(ContextOptions(
        local=False
    ))

    switcher = Client.get_switcher(SWITCHER_KEY)
    switcher.throttle(period=5000)  # 5 seconds

    monitor_thread = threading.Thread(target=monitor_run, args=(switcher,True), daemon=True)
    monitor_thread.start()

def load_snapshot_from_remote():
    """ Use case: Load snapshot from remote API """
    global LOOP
    LOOP = False

    setup_context(ContextOptions(
        local=True,
        snapshot_location='tests/playground/snapshots/temp'
    ))

    Client.load_snapshot(LoadSnapshotOptions(
        fetch_remote=True
    ))

    print(f"Snapshot version: {Client.snapshot_version()}")

def auto_update_snapshot():
    """ Use case: Auto update snapshot """
    setup_context(ContextOptions(
        local=True,
        snapshot_location='tests/playground/snapshots/temp',
        snapshot_auto_update_interval=10
    ))

    Client.load_snapshot(LoadSnapshotOptions(
        fetch_remote=True
    ))

    print(f"Initial snapshot version: {Client.snapshot_version()}")
    Client.schedule_snapshot_auto_update(
        callback=lambda _, updated: (
            print(f"Snapshot updated to version: {Client.snapshot_version()}") if updated else None
        )
    )

try:
    # Replace with use case
    simple_api_call()
    while LOOP:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nStopping...")