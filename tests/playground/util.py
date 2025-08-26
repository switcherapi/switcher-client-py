import json
import time

from switcher_client import Switcher

def monitor_run(switcher: Switcher):
    while True:
        start_time = time.time() * 1000
        result = switcher.is_on()
        end_time = time.time() * 1000

        elapsed_time = int(end_time - start_time)
        print(f"- {elapsed_time} ms - {json.dumps(result)}")
        time.sleep(1.0)