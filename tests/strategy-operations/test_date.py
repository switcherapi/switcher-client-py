import pytest
from typing import Dict, List, Any

from switcher_client.lib.snapshot import OperationsType, StrategiesType, process_operation

class TestDateStrategy:
    """Test suite for Strategy [DATE] tests."""
    
    @pytest.fixture
    def mock_values1(self) -> List[str]:
        """Single date value mock data."""
        return ['2019-12-01']
    
    @pytest.fixture  
    def mock_values2(self) -> List[str]:
        """Multiple date values for BETWEEN operations."""
        return ['2019-12-01', '2019-12-05']
    
    @pytest.fixture  
    def mock_values3(self) -> List[str]:
        """Date with time component mock data."""
        return ['2019-12-01T08:30']
    
    def given_strategy_config(self, operation: str, values: List[str]) -> Dict[str, Any]:
        return {
            'strategy': StrategiesType.DATE.value,
            'operation': operation,
            'values': values,
            'activated': True
        }
    
    def test_should_agree_when_input_is_lower(self, mock_values1):
        """Should agree when input is LOWER."""

        strategy_config = self.given_strategy_config(OperationsType.LOWER.value, mock_values1)
        result = process_operation(strategy_config, '2019-11-26')
        assert result is True
    
    def test_should_agree_when_input_is_lower_or_same(self, mock_values1):
        """Should agree when input is LOWER or SAME."""

        strategy_config = self.given_strategy_config(OperationsType.LOWER.value, mock_values1)
        result = process_operation(strategy_config, '2019-12-01')
        assert result is True
    
    def test_should_not_agree_when_input_is_not_lower(self, mock_values1):
        """Should NOT agree when input is NOT LOWER."""

        strategy_config = self.given_strategy_config(OperationsType.LOWER.value, mock_values1)
        result = process_operation(strategy_config, '2019-12-02')
        assert result is False
    
    def test_should_agree_when_input_is_greater(self, mock_values1):
        """Should agree when input is GREATER."""

        strategy_config = self.given_strategy_config(OperationsType.GREATER.value, mock_values1)
        result = process_operation(strategy_config, '2019-12-02')
        assert result is True
    
    def test_should_agree_when_input_is_greater_or_same(self, mock_values1):
        """Should agree when input is GREATER or SAME."""

        strategy_config = self.given_strategy_config(OperationsType.GREATER.value, mock_values1)
        result = process_operation(strategy_config, '2019-12-01')
        assert result is True
    
    def test_should_not_agree_when_input_is_not_greater(self, mock_values1):
        """Should NOT agree when input is NOT GREATER."""

        strategy_config = self.given_strategy_config(OperationsType.GREATER.value, mock_values1)
        result = process_operation(strategy_config, '2019-11-10')
        assert result is False
    
    def test_should_agree_when_input_is_in_between(self, mock_values2):
        """Should agree when input is in BETWEEN."""

        strategy_config = self.given_strategy_config(OperationsType.BETWEEN.value, mock_values2)
        result = process_operation(strategy_config, '2019-12-03')
        assert result is True
    
    def test_should_not_agree_when_input_is_not_in_between(self, mock_values2):
        """Should NOT agree when input is NOT in BETWEEN."""

        strategy_config = self.given_strategy_config(OperationsType.BETWEEN.value, mock_values2)
        result = process_operation(strategy_config, '2019-12-12')
        assert result is False
    
    def test_should_agree_when_input_is_lower_including_time(self, mock_values3):
        """Should agree when input is LOWER including time."""

        strategy_config = self.given_strategy_config(OperationsType.LOWER.value, mock_values3)
        result = process_operation(strategy_config, '2019-12-01T07:00')
        assert result is True
    
    def test_should_not_agree_when_input_is_not_lower_including_time(self, mock_values1):
        """Should NOT agree when input is NOT LOWER including time."""

        strategy_config = self.given_strategy_config(OperationsType.LOWER.value, mock_values1)
        result = process_operation(strategy_config, '2019-12-01T07:00')
        assert result is False
    
    def test_should_agree_when_input_is_greater_including_time(self, mock_values3):
        """Should agree when input is GREATER including time."""

        strategy_config = self.given_strategy_config(OperationsType.GREATER.value, mock_values3)
        result = process_operation(strategy_config, '2019-12-01T08:40')
        assert result is True

    def test_should_not_agree_when_input_is_not_valid_date(self, mock_values1):
        """Should NOT agree when input is NOT a valid date."""

        strategy_config = self.given_strategy_config(OperationsType.LOWER.value, mock_values1)
        result = process_operation(strategy_config, 'invalid-date')
        assert result is None