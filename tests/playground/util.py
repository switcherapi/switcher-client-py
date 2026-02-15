import json
import time

from switcher_client import Switcher

def monitor_run(switcher: Switcher, details=False):
    while True:
        start_time = time.time() * 1000
        if details: result = switcher.is_on_with_details()
        else: result = switcher.is_on()
        end_time = time.time() * 1000

        elapsed_time = int(end_time - start_time)
        print(f"- {elapsed_time} ms - {result if isinstance(result, bool) else json.dumps(result.to_dict())}")
        time.sleep(1.0)