from typing import Optional

class ResultDetail:
    def __init__(self, result: bool, reason: Optional[str], metadata: Optional[dict] = None):
        self.result = result
        self.reason = reason
        self.metadata = metadata

    @staticmethod
    def disabled(reason: str, metadata: Optional[dict] = None) -> 'ResultDetail':
        return ResultDetail(result=False, reason=reason, metadata=metadata)

    @staticmethod
    def success(reason: str = "Success", metadata: Optional[dict] = None) -> 'ResultDetail':
        return ResultDetail(result=True, reason=reason, metadata=metadata)

class Domain:
    def __init__(self):
        self.name: str
        self.version: int = 0
        self.activated: bool
        self.group: list[Group]

class Group:
    def __init__(self):
        self.name: str
        self.activated: bool
        self.config: list[Config]

class Config:
    def __init__(self):
        self.key: str
        self.activated: bool
        self.strategies: Optional[list[StrategyConfig]] = None
        self.relay: Optional[Relay] = None

class StrategyConfig:
    def __init__(self):
        self.strategy: str
        self.activated: bool
        self.operation: str
        self.values: list[str]

class Relay:
    def __init__(self):
        self.type: str
        self.activated: bool

class Snapshot:
    def __init__(self, json_data: dict):
        self._original_data = json_data
        self.domain = self._parse_domain(json_data)

    def _parse_domain(self, domain_data: dict) -> Domain:
        """ Parse domain data from JSON """

        domain = Domain()
        domain.name = domain_data.get('name', '')
        domain.activated = domain_data.get('activated', False)
        domain.version = domain_data.get('version', 0)
        
        if 'group' in domain_data and domain_data['group']:
            domain.group = []
            for group_data in domain_data['group']:
                domain.group.append(self._parse_group(group_data))
        
        return domain

    def _parse_group(self, group_data: dict) -> Group:
        """ Parse group data from JSON """

        group = Group()
        group.name = group_data.get('name', '')
        group.activated = group_data.get('activated', False)

        if 'config' in group_data and group_data['config']:
            group.config = []
            for config_data in group_data['config']:
                group.config.append(self._parse_config(config_data))
        
        return group

    def _parse_config(self, config_data: dict) -> Config:
        """ Parse config data from JSON """

        config = Config()
        config.key = config_data.get('key', '')
        config.activated = config_data.get('activated', False)

        if 'strategies' in config_data and config_data['strategies']:
            config.strategies = []
            for strategy_data in config_data['strategies']:
                config.strategies.append(self._parse_strategy(strategy_data))
        
        if 'relay' in config_data and config_data['relay']:
            config.relay = self._parse_relay(config_data['relay'])
        
        return config

    def _parse_strategy(self, strategy_data: dict) -> StrategyConfig:
        """ Parse strategy data from JSON """

        strategy = StrategyConfig()
        strategy.strategy = strategy_data.get('strategy', '')
        strategy.activated = strategy_data.get('activated', False)
        strategy.operation = strategy_data.get('operation', '')
        strategy.values = strategy_data.get('values', [])
        
        return strategy

    def _parse_relay(self, relay_data: dict) -> Relay:
        """ Parse relay data from JSON """

        relay = Relay()
        relay.type = relay_data.get('type', '')
        relay.activated = relay_data.get('activated', False)

        return relay

    def to_dict(self) -> dict:
        """ Convert Snapshot back to dictionary format for JSON serialization """
        
        return {'domain': self._original_data}