import pytest
from typing import List

from switcher_client.lib.snapshot import OperationsType, StrategiesType, process_operation
from switcher_client.lib.types import StrategyConfig

class TestNetworkStrategy:
    """Test suite for Strategy [NETWORK] tests."""
    
    @pytest.fixture
    def mock_values1(self) -> List[str]:
        """Single CIDR range mock data."""
        return ['10.0.0.0/30']
    
    @pytest.fixture  
    def mock_values2(self) -> List[str]:
        """Multiple CIDR ranges mock data."""
        return ['10.0.0.0/30', '192.168.0.0/30']
    
    @pytest.fixture
    def mock_values3(self) -> List[str]:
        """Multiple IP addresses mock data."""
        return ['192.168.56.56', '192.168.56.57', '192.168.56.58']
    
    def given_strategy_config(self, operation: str, values: List[str]) -> StrategyConfig:
        """Create a strategy configuration for NETWORK strategy."""
        strategy_config = StrategyConfig()
        strategy_config.strategy = StrategiesType.NETWORK.value
        strategy_config.operation = operation
        strategy_config.values = values
        strategy_config.activated = True
        return strategy_config
    
    def test_should_agree_when_input_range_exist(self, mock_values1):
        """Should agree when input range EXIST."""

        strategy_config = self.given_strategy_config(OperationsType.EXIST.value, mock_values1)
        result = process_operation(strategy_config, '10.0.0.3')
        assert result is True
    
    def test_should_agree_when_input_range_exist_irregular_cidr(self):
        """Should agree when input range EXIST - Irregular CIDR."""

        strategy_config = self.given_strategy_config(OperationsType.EXIST.value, ['10.0.0.3/24'])
        result = process_operation(strategy_config, '10.0.0.3')
        assert result is True
    
    def test_should_not_agree_when_input_range_does_not_exist(self, mock_values1):
        """Should NOT agree when input range DOES NOT EXIST."""

        strategy_config = self.given_strategy_config(OperationsType.EXIST.value, mock_values1)
        result = process_operation(strategy_config, '10.0.0.4')
        assert result is False
    
    def test_should_agree_when_input_does_not_exist(self, mock_values1):
        """Should agree when input DOES NOT EXIST."""

        strategy_config = self.given_strategy_config(OperationsType.NOT_EXIST.value, mock_values1)
        result = process_operation(strategy_config, '10.0.0.4')
        assert result is True
    
    def test_should_not_agree_when_input_exist_but_assumed_not_exist(self, mock_values1):
        """Should NOT agree when input EXIST but assumed that it DOES NOT EXIST."""

        strategy_config = self.given_strategy_config(OperationsType.NOT_EXIST.value, mock_values1)
        result = process_operation(strategy_config, '10.0.0.3')
        assert result is False
    
    def test_should_agree_when_input_ip_exist(self, mock_values3):
        """Should agree when input IP EXIST."""

        strategy_config = self.given_strategy_config(OperationsType.EXIST.value, mock_values3)
        result = process_operation(strategy_config, '192.168.56.58')
        assert result is True
    
    def test_should_agree_when_input_ip_does_not_exist(self, mock_values3):
        """Should agree when input IP DOES NOT EXIST."""

        strategy_config = self.given_strategy_config(OperationsType.NOT_EXIST.value, mock_values3)
        result = process_operation(strategy_config, '192.168.56.50')
        assert result is True

    def test_should_not_agree_when_input_ip_does_exist_in_values(self, mock_values3):
        """Should NOT agree when input IP DOES EXIST."""

        strategy_config = self.given_strategy_config(OperationsType.NOT_EXIST.value, mock_values3)
        result = process_operation(strategy_config, '192.168.56.58')
        assert result is False
    
    def test_should_agree_when_input_range_exist_for_multiple_ranges(self, mock_values2):
        """Should agree when input range EXIST for multiple ranges."""

        strategy_config = self.given_strategy_config(OperationsType.EXIST.value, mock_values2)
        result = process_operation(strategy_config, '192.168.0.3')
        assert result is True
    
    def test_should_agree_when_input_range_does_not_exist_for_multiple_ranges(self, mock_values2):
        """Should NOT agree when input range DOES NOT EXIST for multiple ranges."""

        strategy_config = self.given_strategy_config(OperationsType.NOT_EXIST.value, mock_values2)
        result = process_operation(strategy_config, '127.0.0.0')
        assert result is True

    def test_should_not_agree_when_operation_is_unknown(self, mock_values1):
        """Should NOT agree when operation is unknown."""

        strategy_config = self.given_strategy_config('UNKNOWN_OPERATION', mock_values1)
        result = process_operation(strategy_config, '10.0.0.3')
        assert result is False