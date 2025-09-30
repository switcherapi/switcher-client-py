import os

SNAPSHOT_TEMP_DIR = 'tests/snapshots/temp'

if os.path.exists(SNAPSHOT_TEMP_DIR):
    for f in os.listdir(SNAPSHOT_TEMP_DIR):
        os.remove(os.path.join(SNAPSHOT_TEMP_DIR, f))