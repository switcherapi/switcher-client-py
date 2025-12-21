import pytest
from typing import Dict, List, Any

from switcher_client.lib.snapshot import OperationsType, StrategiesType, process_operation

class TestTimeStrategy:
    """Test suite for Strategy [TIME] tests."""
    
    @pytest.fixture
    def mock_values1(self) -> List[str]:
        """Single time value mock data."""
        return ['08:00']
    
    @pytest.fixture  
    def mock_values2(self) -> List[str]:
        """Multiple time values for BETWEEN operations."""
        return ['08:00', '10:00']
    
    def given_strategy_config(self, operation: str, values: List[str]) -> Dict[str, Any]:
        return {
            'strategy': StrategiesType.TIME.value,
            'operation': operation,
            'values': values,
            'activated': True
        }
    
    def test_should_agree_when_input_is_lower(self, mock_values1):
        """Should agree when input is LOWER."""

        strategy_config = self.given_strategy_config(OperationsType.LOWER.value, mock_values1)
        result = process_operation(strategy_config, '06:00')
        assert result is True
    
    def test_should_agree_when_input_is_lower_or_same(self, mock_values1):
        """Should agree when input is LOWER or SAME."""

        strategy_config = self.given_strategy_config(OperationsType.LOWER.value, mock_values1)
        result = process_operation(strategy_config, '08:00')
        assert result is True
    
    def test_should_not_agree_when_input_is_not_lower(self, mock_values1):
        """Should NOT agree when input is NOT LOWER."""

        strategy_config = self.given_strategy_config(OperationsType.LOWER.value, mock_values1)
        result = process_operation(strategy_config, '10:00')
        assert result is False
    
    def test_should_agree_when_input_is_greater(self, mock_values1):
        """Should agree when input is GREATER."""

        strategy_config = self.given_strategy_config(OperationsType.GREATER.value, mock_values1)
        result = process_operation(strategy_config, '10:00')
        assert result is True
    
    def test_should_agree_when_input_is_greater_or_same(self, mock_values1):
        """Should agree when input is GREATER or SAME."""

        strategy_config = self.given_strategy_config(OperationsType.GREATER.value, mock_values1)
        result = process_operation(strategy_config, '08:00')
        assert result is True
    
    def test_should_not_agree_when_input_is_not_greater(self, mock_values1):
        """Should NOT agree when input is NOT GREATER."""

        strategy_config = self.given_strategy_config(OperationsType.GREATER.value, mock_values1)
        result = process_operation(strategy_config, '06:00')
        assert result is False
    
    def test_should_agree_when_input_is_in_between(self, mock_values2):
        """Should agree when input is in BETWEEN."""

        strategy_config = self.given_strategy_config(OperationsType.BETWEEN.value, mock_values2)
        result = process_operation(strategy_config, '09:00')
        assert result is True
    
    def test_should_not_agree_when_input_is_not_in_between(self, mock_values2):
        """Should NOT agree when input is NOT in BETWEEN."""

        strategy_config = self.given_strategy_config(OperationsType.BETWEEN.value, mock_values2)
        result = process_operation(strategy_config, '07:00')
        assert result is False

    def test_should_not_agree_when_input_is_invalid_time_format(self, mock_values1):
        """Should NOT agree when input is in INVALID time format."""

        strategy_config = self.given_strategy_config(OperationsType.GREATER.value, mock_values1)
        result = process_operation(strategy_config, 'invalid-time')
        assert result is None
