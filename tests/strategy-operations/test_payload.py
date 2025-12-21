import json
import pytest
from typing import Dict, List, Any

from switcher_client.lib.snapshot import OperationsType, StrategiesType, process_operation

class TestPayloadStrategy:
    """Test suite for Strategy [PAYLOAD] tests."""
    
    @pytest.fixture
    def fixture_1(self) -> str:
        """Simple JSON payload fixture."""
        return json.dumps({
            'id': '1',
            'login': 'petruki'
        })
    
    @pytest.fixture  
    def fixture_values2(self) -> str:
        """Complex nested JSON payload fixture."""
        return json.dumps({
            'product': 'product-1',
            'order': {
                'qty': 1,
                'deliver': {
                    'expect': '2019-12-10',
                    'tracking': [
                        {
                            'date': '2019-12-09',
                            'status': 'sent'
                        },
                        {
                            'date': '2019-12-10',
                            'status': 'delivered',
                            'comments': 'comments'
                        }
                    ]
                }
            }
        })
    
    @pytest.fixture  
    def fixture_values3(self) -> str:
        """Configuration-style JSON payload fixture."""
        return json.dumps({
            'description': 'Allowed IP address',
            'strategy': 'NETWORK_VALIDATION',
            'values': ['10.0.0.3/24'],
            'operation': 'EXIST',
            'env': 'default'
        })
    
    def given_strategy_config(self, operation: str, values: List[str]) -> Dict[str, Any]:
        return {
            'strategy': StrategiesType.PAYLOAD.value,
            'operation': operation,
            'values': values,
            'activated': True
        }
    
    # Note: These tests will need payloadReader implementation
    @pytest.mark.skip(reason="payloadReader not yet implemented")
    def test_should_read_keys_from_payload_1(self, fixture_values2):
        """Should read keys from payload #1."""

        from switcher_client.lib.utils.payload_reader import payload_reader
        
        keys = payload_reader(json.loads(fixture_values2))
        expected_keys = [
            'product',
            'order',
            'order.qty',
            'order.deliver',
            'order.deliver.expect',
            'order.deliver.tracking',
            'order.deliver.tracking.date',
            'order.deliver.tracking.status',
            'order.deliver.tracking.comments'
        ]
        assert all(key in keys for key in expected_keys)
    
    @pytest.mark.skip(reason="payloadReader not yet implemented")
    def test_should_read_keys_from_payload_2(self, fixture_values3):
        """Should read keys from payload #2."""

        from switcher_client.lib.utils.payload_reader import payload_reader
        
        keys = payload_reader(json.loads(fixture_values3))
        expected_keys = [
            'description',
            'strategy',
            'values',
            'operation',
            'env'
        ]
        assert all(key in keys for key in expected_keys)
    
    @pytest.mark.skip(reason="payloadReader not yet implemented")
    def test_should_read_keys_from_payload_with_array_values(self):
        """Should read keys from payload with array values."""

        from switcher_client.lib.utils.payload_reader import payload_reader
        
        test_payload = {
            'order': {
                'items': ['item_1', 'item_2']
            }
        }
        keys = payload_reader(test_payload)
        expected_keys = [
            'order',
            'order.items'
        ]
        assert all(key in keys for key in expected_keys)
    
    def test_should_return_true_when_payload_has_field(self, fixture_1):
        """Should return TRUE when payload has field."""

        strategy_config = self.given_strategy_config(OperationsType.HAS_ONE.value, ['login'])
        result = process_operation(strategy_config, fixture_1)
        assert result is True
    
    def test_should_return_false_when_payload_does_not_have_field(self, fixture_1):
        """Should return FALSE when payload does not have field."""

        strategy_config = self.given_strategy_config(OperationsType.HAS_ONE.value, ['user'])
        result = process_operation(strategy_config, fixture_1)
        assert result is False
    
    def test_should_return_true_when_payload_has_nested_field(self, fixture_values2):
        """Should return TRUE when payload has nested field."""

        strategy_config = self.given_strategy_config(OperationsType.HAS_ONE.value, [
            'order.qty', 'order.total'
        ])
        result = process_operation(strategy_config, fixture_values2)
        assert result is True
    
    def test_should_return_true_when_payload_has_nested_field_with_arrays(self, fixture_values2):
        """Should return TRUE when payload has nested field with arrays."""

        strategy_config = self.given_strategy_config(OperationsType.HAS_ONE.value, [
            'order.deliver.tracking.status'
        ])
        result = process_operation(strategy_config, fixture_values2)
        assert result is True
    
    def test_should_return_true_when_payload_has_all(self, fixture_values2):
        """Should return TRUE when payload has all."""

        strategy_config = self.given_strategy_config(OperationsType.HAS_ALL.value, [
            'product',
            'order',
            'order.qty',
            'order.deliver',
            'order.deliver.expect',
            'order.deliver.tracking',
            'order.deliver.tracking.date',
            'order.deliver.tracking.status'
        ])
        result = process_operation(strategy_config, fixture_values2)
        assert result is True
    
    def test_should_return_false_when_payload_does_not_have_all(self, fixture_values2):
        """Should return FALSE when payload does not have all."""

        strategy_config = self.given_strategy_config(OperationsType.HAS_ALL.value, [
            'product',
            'order',
            'order.NOT_EXIST_KEY'
        ])
        result = process_operation(strategy_config, fixture_values2)
        assert result is False
    
    def test_should_return_false_when_payload_is_not_json_string(self):
        """Should return FALSE when payload is not a JSON string."""
        
        strategy_config = self.given_strategy_config(OperationsType.HAS_ALL.value, [])
        result = process_operation(strategy_config, 'NOT_JSON')
        assert result is False
