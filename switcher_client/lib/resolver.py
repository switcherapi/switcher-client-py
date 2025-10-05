from switcher_client.errors import LocalCriteriaError
from switcher_client.lib.types import Config, Domain, Group, ResultDetail, Snapshot
from switcher_client.switcher_data import SwitcherData

class Resolver:

    @staticmethod
    def check_criteria(snapshot: Snapshot | None, switcher: SwitcherData) -> ResultDetail:
        if not snapshot:
            raise LocalCriteriaError("Snapshot not loaded. Try to use 'Client.load_snapshot()'")

        return Resolver.__check_domain(snapshot.domain, switcher)
    
    @staticmethod
    def __check_domain(domain: Domain, switcher: SwitcherData) -> ResultDetail:
        if domain.activated is False:
            return ResultDetail.disabled("Domain is disabled")

        return Resolver.__check_group(domain.group, switcher)
    
    @staticmethod
    def __check_group(groups: list[Group], switcher: SwitcherData) -> ResultDetail:
        key = switcher._key

        for group in groups:
            config_found = next((c for c in group.config if c.key == key), None)

            if config_found is not None:
                if group.activated is False:
                    return ResultDetail.disabled("Group disabled")
                
                return Resolver.__check_config(config_found, switcher)
        
        raise LocalCriteriaError(f"Config with key '{key}' not found in the snapshot")
    
    @staticmethod
    def __check_config(config: Config, switcher: SwitcherData) -> ResultDetail:
        if config.activated is False:
            return ResultDetail.disabled("Config disabled")
        
        return ResultDetail.success()