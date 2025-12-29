from typing import Optional

from ..lib.types import Config, Domain, Entry, Group, ResultDetail, Snapshot, StrategyConfig
from ..lib.snapshot import process_operation
from ..lib.utils import get, get_entry
from ..errors import LocalCriteriaError
from ..switcher_data import SwitcherData

class Resolver:

    @staticmethod
    def check_criteria(snapshot: Snapshot | None, switcher: SwitcherData) -> ResultDetail:
        """ Resolves the criteria for a given switcher request against the snapshot domain. """
        if not snapshot:
            raise LocalCriteriaError("Snapshot not loaded. Try to use 'Client.load_snapshot()'")

        return Resolver._check_domain(snapshot.domain, switcher)
    
    @staticmethod
    def _check_domain(domain: Domain, switcher: SwitcherData) -> ResultDetail:
        """ Checks if the domain is activated and proceeds to check groups. """
        if domain.activated is False:
            return ResultDetail.disabled("Domain is disabled")

        return Resolver._check_group(domain.group, switcher)
    
    @staticmethod
    def _check_group(groups: list[Group], switcher: SwitcherData) -> ResultDetail:
        """ Finds the correct config in the groups and checks it. """
        key = switcher._key

        for group in groups:
            config_found = next((c for c in group.config if c.key == key), None)

            if config_found is not None:
                if group.activated is False:
                    return ResultDetail.disabled("Group disabled")
                
                return Resolver._check_config(config_found, switcher)
        
        raise LocalCriteriaError(f"Config with key '{key}' not found in the snapshot")
    
    @staticmethod
    def _check_config(config: Config, switcher: SwitcherData) -> ResultDetail:
        """ Checks if the config is activated and proceeds to check strategies. """
        if config.activated is False:
            return ResultDetail.disabled("Config disabled")
        
        if config.strategies is not None and len(config.strategies) > 0:
            return Resolver._check_strategy(config.strategies, switcher._input)

        return ResultDetail.success()
    
    @staticmethod
    def _check_strategy(strategy_configs: list[StrategyConfig], inputs: list[list[str]]) -> ResultDetail:
        """ Checks each strategy configuration against the provided inputs. """
        entry = get_entry(get(inputs, []))

        for strategy_config in strategy_configs:
            if not strategy_config.activated:
                continue

            strategy_result = Resolver._check_strategy_config(strategy_config, entry)
            if strategy_result is not None:
                return strategy_result

        return ResultDetail.success()
    
    @staticmethod
    def _check_strategy_config(strategy_config: StrategyConfig, entry: list[Entry]) -> Optional[ResultDetail]:
        """ Checks a single strategy configuration against the provided entries. """
        if len(entry) == 0:
            return ResultDetail.disabled(f"Strategy '{strategy_config.strategy}' did not receive any input")
        
        strategy_entry = [e for e in entry if e.strategy == strategy_config.strategy]
        if not Resolver._is_strategy_fulfilled(strategy_entry, strategy_config):
            return ResultDetail.disabled(f"Strategy '{strategy_config.strategy}' does not agree")
        
        return None
    
    @staticmethod
    def _is_strategy_fulfilled(strategy_entry: list[Entry], strategy_config: StrategyConfig) -> bool:
        """ Determines if the strategy conditions are fulfilled based on the entries and configuration. """
        return len(strategy_entry) > 0 and process_operation(strategy_config, strategy_entry[0].input) is True