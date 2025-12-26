import pytest
from typing import Dict, List, Any

from switcher_client.lib.snapshot import OperationsType, StrategiesType, process_operation
from switcher_client.lib.utils.timed_match import TimedMatch

class TestRegexStrategy:
    """Test suite for Strategy [REGEX Safe] tests."""
    
    @classmethod
    def setup_class(cls):
        """Set up TimedMatch before all tests in this class."""
        TimedMatch.set_max_time_limit(1000)  # 1000ms = 1 second
        TimedMatch.initialize_worker()  # Initialize persistent worker
    
    @classmethod
    def teardown_class(cls):
        """Clean up TimedMatch after all tests in this class."""
        TimedMatch.terminate_worker()  # Terminate any running worker processes
        TimedMatch.clear_blacklist()
    
    @pytest.fixture
    def mock_values1(self) -> List[str]:
        """Single regex pattern with word boundaries."""
        return [r'\bUSER_[0-9]{1,2}\b']
    
    @pytest.fixture  
    def mock_values2(self) -> List[str]:
        """Multiple regex patterns with word boundaries."""
        return [
            r'\bUSER_[0-9]{1,2}\b',
            r'\buser-[0-9]{1,2}\b'
        ]
    
    @pytest.fixture  
    def mock_values3(self) -> List[str]:
        """Simple regex pattern without word boundaries."""
        return ['USER_[0-9]{1,2}']
    
    def given_strategy_config(self, operation: str, values: List[str]) -> Dict[str, Any]:
        return {
            'strategy': StrategiesType.REGEX.value,
            'operation': operation,
            'values': values,
            'activated': True
        }
    
    def test_should_agree_when_expect_to_exist_using_exist_operation(self, mock_values1, mock_values2):
        """Should agree when expect to exist using EXIST operation."""
        
        strategy_config = self.given_strategy_config(OperationsType.EXIST.value, mock_values1)
        result = process_operation(strategy_config, 'USER_1')
        assert result is True

        strategy_config = self.given_strategy_config(OperationsType.EXIST.value, mock_values2)
        result = process_operation(strategy_config, 'user-01')
        assert result is True
    
    def test_should_not_agree_when_expect_to_exist_using_exist_operation(self, mock_values1, mock_values3):
        """Should NOT agree when expect to exist using EXIST operation."""
        
        strategy_config = self.given_strategy_config(OperationsType.EXIST.value, mock_values1)
        result = process_operation(strategy_config, 'USER_123')
        assert result is False

        # mock_values3 does not require exact match
        strategy_config = self.given_strategy_config(OperationsType.EXIST.value, mock_values3)
        result = process_operation(strategy_config, 'USER_123')
        assert result is True
    
    def test_should_agree_when_expect_to_not_exist_using_not_exist_operation(self, mock_values1, mock_values2):
        """Should agree when expect to not exist using NOT_EXIST operation."""
        
        strategy_config = self.given_strategy_config(OperationsType.NOT_EXIST.value, mock_values1)
        result = process_operation(strategy_config, 'USER_123')
        assert result is True

        strategy_config = self.given_strategy_config(OperationsType.NOT_EXIST.value, mock_values2)
        result = process_operation(strategy_config, 'user-123')
        assert result is True
    
    def test_should_not_agree_when_expect_to_not_exist_using_not_exist_operation(self, mock_values1):
        """Should NOT agree when expect to not exist using NOT_EXIST operation."""
        
        strategy_config = self.given_strategy_config(OperationsType.NOT_EXIST.value, mock_values1)
        result = process_operation(strategy_config, 'USER_12')
        assert result is False
    
    def test_should_agree_when_expect_to_be_equal_using_equal_operation(self, mock_values3):
        """Should agree when expect to be equal using EQUAL operation."""
        
        strategy_config = self.given_strategy_config(OperationsType.EQUAL.value, mock_values3)
        result = process_operation(strategy_config, 'USER_11')
        assert result is True
    
    def test_should_not_agree_when_expect_to_be_equal_using_equal_operation(self, mock_values3):
        """Should NOT agree when expect to be equal using EQUAL operation."""
        
        strategy_config = self.given_strategy_config(OperationsType.EQUAL.value, mock_values3)
        result = process_operation(strategy_config, 'user-11')
        assert result is False
    
    def test_should_agree_when_expect_to_not_be_equal_using_not_equal_operation(self, mock_values3):
        """Should agree when expect to not be equal using NOT_EQUAL operation."""
        
        strategy_config = self.given_strategy_config(OperationsType.NOT_EQUAL.value, mock_values3)
        result = process_operation(strategy_config, 'USER_123')
        assert result is True
    
    def test_should_not_agree_when_expect_to_not_be_equal_using_not_equal_operation(self, mock_values3):
        """Should NOT agree when expect to not be equal using NOT_EQUAL operation."""
        
        strategy_config = self.given_strategy_config(OperationsType.NOT_EQUAL.value, mock_values3)
        result = process_operation(strategy_config, 'USER_1')
        assert result is False
    
    def test_should_not_agree_when_match_cannot_finish_redos_attempt(self):
        """Should NOT agree when match cannot finish (reDoS attempt)."""
        
        strategy_config = self.given_strategy_config(
            OperationsType.EQUAL.value, 
            ['^(([a-z])+.)+[A-Z]([a-z])+$']
        )
        result = process_operation(strategy_config, 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')
        assert result is False