import json
import os

from switcher_client.lib.types import Snapshot, SnapshotData, Domain, Group, Config, StrategyConfig, Relay

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

    snapshot = Snapshot()
    snapshot.data = SnapshotData()
    snapshot.data.domain = _parse_domain(json_data['data']['domain'])
    
    return snapshot

def _parse_domain(domain_data: dict) -> Domain:
    """ Parse domain data from JSON """

    domain = Domain()
    domain.name = domain_data.get('name')
    domain.activated = domain_data.get('activated')
    domain.version = domain_data.get('version', 0)
    
    if 'group' in domain_data and domain_data['group']:
        domain.group = []
        for group_data in domain_data['group']:
            domain.group.append(_parse_group(group_data))
    
    return domain

def _parse_group(group_data: dict) -> Group:
    """ Parse group data from JSON """

    group = Group()
    group.name = group_data.get('name')
    group.activated = group_data.get('activated')
    
    if 'config' in group_data and group_data['config']:
        group.config = []
        for config_data in group_data['config']:
            group.config.append(_parse_config(config_data))
    
    return group

def _parse_config(config_data: dict) -> Config:
    """ Parse config data from JSON """

    config = Config()
    config.key = config_data.get('key')
    config.activated = config_data.get('activated')
    
    if 'strategies' in config_data and config_data['strategies']:
        config.strategies = []
        for strategy_data in config_data['strategies']:
            config.strategies.append(_parse_strategy(strategy_data))
    
    if 'relay' in config_data and config_data['relay']:
        config.relay = _parse_relay(config_data['relay'])
    
    return config

def _parse_strategy(strategy_data: dict) -> StrategyConfig:
    """ Parse strategy data from JSON """

    strategy = StrategyConfig()
    strategy.strategy = strategy_data.get('strategy')
    strategy.activated = strategy_data.get('activated')
    strategy.operation = strategy_data.get('operation')
    strategy.values = strategy_data.get('values')
    
    return strategy

def _parse_relay(relay_data: dict) -> Relay:
    """ Parse relay data from JSON """

    relay = Relay()
    relay.type = relay_data.get('type')
    relay.activated = relay_data.get('activated')
    
    return relay