import pytest
from typing import Dict, List, Any

from switcher_client.lib.snapshot import OperationsType, StrategiesType, process_operation

class TestNumericStrategy:
    """Test suite for Strategy [NUMERIC] tests."""
    
    @pytest.fixture
    def mock_values1(self) -> List[str]:
        """Single numeric value mock data."""
        return ['1']
    
    @pytest.fixture  
    def mock_values2(self) -> List[str]:
        """Multiple numeric values mock data."""
        return ['1', '3']
    
    @pytest.fixture  
    def mock_values3(self) -> List[str]:
        """Decimal numeric value mock data."""
        return ['1.5']
    
    def given_strategy_config(self, operation: str, values: List[str]) -> Dict[str, Any]:
        return {
            'strategy': StrategiesType.NUMERIC.value,
            'operation': operation,
            'values': values,
            'activated': True
        }
    
    def test_should_agree_when_input_exist_in_values_string_type(self, mock_values2):
        """Should agree when input EXIST in values - String type."""

        strategy_config = self.given_strategy_config(OperationsType.EXIST.value, mock_values2)
        result = process_operation(strategy_config, '3')
        assert result is True
    
    def test_should_not_agree_when_input_exist_but_test_as_does_not_exist(self, mock_values2):
        """Should NOT agree when input exist but test as DOES NOT EXIST."""

        strategy_config = self.given_strategy_config(OperationsType.NOT_EXIST.value, mock_values2)
        result = process_operation(strategy_config, '1')
        assert result is False
    
    def test_should_agree_when_input_does_not_exist_in_values(self, mock_values2):
        """Should agree when input DOES NOT EXIST in values."""

        strategy_config = self.given_strategy_config(OperationsType.NOT_EXIST.value, mock_values2)
        result = process_operation(strategy_config, '2')
        assert result is True
    
    def test_should_agree_when_input_is_equal_to_value(self, mock_values1):
        """Should agree when input is EQUAL to value."""

        strategy_config = self.given_strategy_config(OperationsType.EQUAL.value, mock_values1)
        result = process_operation(strategy_config, '1')
        assert result is True
    
    def test_should_not_agree_when_input_is_not_equal_but_test_as_equal(self, mock_values1):
        """Should NOT agree when input is not equal but test as EQUAL."""

        strategy_config = self.given_strategy_config(OperationsType.EQUAL.value, mock_values1)
        result = process_operation(strategy_config, '2')
        assert result is False
    
    def test_should_agree_when_input_is_not_equal_to_value(self, mock_values1):
        """Should agree when input is NOT EQUAL to value."""

        strategy_config = self.given_strategy_config(OperationsType.NOT_EQUAL.value, mock_values1)
        result = process_operation(strategy_config, '2')
        assert result is True
    
    def test_should_agree_when_input_is_greater_than_value(self, mock_values1, mock_values3):
        """Should agree when input is GREATER than value."""

        strategy_config = self.given_strategy_config(OperationsType.GREATER.value, mock_values1)
        result = process_operation(strategy_config, '2')
        assert result is True

        # test decimal
        result = process_operation(strategy_config, '1.01')
        assert result is True

        strategy_config = self.given_strategy_config(OperationsType.GREATER.value, mock_values3)
        result = process_operation(strategy_config, '1.55')
        assert result is True
    
    def test_should_not_agree_when_input_is_lower_but_tested_as_greater_than_value(self, mock_values1, mock_values3):
        """Should NOT agree when input is lower but tested as GREATER than value."""

        strategy_config = self.given_strategy_config(OperationsType.GREATER.value, mock_values1)
        result = process_operation(strategy_config, '0')
        assert result is False

        # test decimal
        result = process_operation(strategy_config, '0.99')
        assert result is False

        strategy_config = self.given_strategy_config(OperationsType.GREATER.value, mock_values3)
        result = process_operation(strategy_config, '1.49')
        assert result is False
    
    def test_should_agree_when_input_is_lower_than_value(self, mock_values1, mock_values3):
        """Should agree when input is LOWER than value."""

        strategy_config = self.given_strategy_config(OperationsType.LOWER.value, mock_values1)
        result = process_operation(strategy_config, '0')
        assert result is True

        # test decimal
        result = process_operation(strategy_config, '0.99')
        assert result is True

        strategy_config = self.given_strategy_config(OperationsType.LOWER.value, mock_values3)
        result = process_operation(strategy_config, '1.49')
        assert result is True
    
    def test_should_agree_when_input_is_between_values(self, mock_values2):
        """Should agree when input is BETWEEN values."""

        strategy_config = self.given_strategy_config(OperationsType.BETWEEN.value, mock_values2)
        result = process_operation(strategy_config, '1')
        assert result is True

        # test decimal
        result = process_operation(strategy_config, '2.99')
        assert result is True

        result = process_operation(strategy_config, '1.001')
        assert result is True

    def test_should_not_agree_when_input_is_not_number(self, mock_values2):
        """Should NOT agree when input is NOT A NUMBER."""

        strategy_config = self.given_strategy_config(OperationsType.GREATER.value, mock_values2)
        result = process_operation(strategy_config, 'ABC')
        assert result is None
