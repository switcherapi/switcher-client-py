import pytest
from typing import Dict, List, Any

from switcher_client.lib.snapshot import OperationsType, StrategiesType, process_operation

class TestValueStrategy:
    """Test suite for Strategy [VALUE] tests."""
    
    @pytest.fixture
    def mock_values1(self) -> List[str]:
        """Single user mock data."""
        return ['USER_1']
    
    @pytest.fixture  
    def mock_values2(self) -> List[str]:
        """Multiple users mock data."""
        return ['USER_1', 'USER_2']
    
    def given_strategy_config(self, operation: str, values: List[str]) -> Dict[str, Any]:
        return {
            'strategy': StrategiesType.VALUE.value,
            'operation': operation,
            'values': values,
            'activated': True
        }
    
    def test_should_agree_when_input_exist(self, mock_values1):
        """Should agree when input EXIST."""
        strategy_config = self.given_strategy_config(OperationsType.EXIST.value, mock_values1)
        result = process_operation(strategy_config, 'USER_1')
        assert result is True
    
    def test_should_not_agree_when_input_does_not_exist(self, mock_values1):
        """Should NOT agree when input DOES NOT EXIST."""
        strategy_config = self.given_strategy_config(OperationsType.EXIST.value, mock_values1)
        result = process_operation(strategy_config, 'USER_123')
        assert result is False
    
    def test_should_agree_when_input_does_not_exist_with_not_exist_operation(self, mock_values1):
        """Should agree when input DOES NOT EXIST with NOT_EXIST operation."""
        strategy_config = self.given_strategy_config(OperationsType.NOT_EXIST.value, mock_values1)
        result = process_operation(strategy_config, 'USER_123')
        assert result is True
    
    def test_should_agree_when_input_is_equal(self, mock_values1):
        """Should agree when input is EQUAL."""
        strategy_config = self.given_strategy_config(OperationsType.EQUAL.value, mock_values1)
        result = process_operation(strategy_config, 'USER_1')
        assert result is True
    
    def test_should_not_agree_when_input_is_not_equal(self, mock_values1):
        """Should NOT agree when input is NOT EQUAL."""
        strategy_config = self.given_strategy_config(OperationsType.EQUAL.value, mock_values1)
        result = process_operation(strategy_config, 'USER_2')
        assert result is False
    
    def test_should_agree_when_input_is_not_equal_with_not_equal_operation(self, mock_values2):
        """Should agree when input is NOT EQUAL with NOT_EQUAL operation."""
        strategy_config = self.given_strategy_config(OperationsType.NOT_EQUAL.value, mock_values2)
        result = process_operation(strategy_config, 'USER_123')
        assert result is True
    
    def test_should_not_agree_when_input_is_not_equal_but_value_exists(self, mock_values2):
        """Should NOT agree when input is NOT EQUAL but value exists in list."""
        strategy_config = self.given_strategy_config(OperationsType.NOT_EQUAL.value, mock_values2)
        result = process_operation(strategy_config, 'USER_2')
        assert result is False
