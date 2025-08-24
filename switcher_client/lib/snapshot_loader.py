import json
import os

from switcher_client.lib.globals.global_auth import GlobalAuth
from switcher_client.lib.globals.global_context import Context
from switcher_client.lib.remote import Remote
from switcher_client.lib.types import Snapshot

def load_domain(snapshot_location: str, environment: str):
    """ Load Domain from snapshot file """

    snapshot_file = f"{snapshot_location}/{environment}.json"
    json_data = {}

    if not os.path.exists(snapshot_file):
        json_data = {
            'data': {
                'domain': {
                    'version': 0,
                }
            }
        }

        if snapshot_location:
            os.makedirs(snapshot_location, exist_ok=True)
            with open(snapshot_file, 'w') as file:
                json.dump(json_data, file, indent=4)
                
    elif os.path.exists(snapshot_file):
        with open(snapshot_file, 'r') as file:
            json_data = json.load(file)

    snapshot = Snapshot(json_data.get('data', {}))

    return snapshot

def validate_snapshot(
    context: Context,
    snapshot_version: int
) -> Snapshot | None:
    """ Validate the snapshot data """

    status = Remote.check_snapshot_version(
        token=GlobalAuth.get_token(), 
        context=context,
        snapshot_version=snapshot_version)
    
    if not status:
        snapshot_str = Remote.resolve_snapshot(GlobalAuth.get_token(), context)
        graphql_response = json.loads(snapshot_str or '{}')
        return Snapshot(graphql_response.get('data', '{}'))
    
    return None