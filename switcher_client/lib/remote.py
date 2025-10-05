import json
import httpx

from typing import Optional

from switcher_client.errors import RemoteAuthError, RemoteError
from switcher_client.errors import RemoteCriteriaError
from switcher_client.lib.globals.global_context import DEFAULT_ENVIRONMENT, Context
from switcher_client.lib.types import ResultDetail
from switcher_client.lib.utils import get
from switcher_client.switcher_data import SwitcherData

class Remote:
    _client: Optional[httpx.Client] = None

    @staticmethod
    def auth(context: Context):
        url = f'{context.url}/criteria/auth'
        response = Remote.__do_post(url, {
            'domain': context.domain,
            'component': context.component,
            'environment': context.environment,
        }, {
            'switcher-api-key': context.api_key,
            'Content-Type': 'application/json',
        })
        
        if response.status_code == 200:
            return response.json()['token'], response.json()['exp']

        raise RemoteAuthError('Invalid API key')
    
    @staticmethod
    def check_criteria(token: Optional[str], context: Context, switcher: SwitcherData) -> ResultDetail:
        url = f'{context.url}/criteria?showReason={str(switcher._show_details).lower()}&key={switcher._key}'
        entry = Remote.__get_entry(switcher._input)
        response = Remote.__do_post(url, entry, Remote.__get_header(token))
        
        if response.status_code == 200:
            json_response = response.json()
            return ResultDetail(
                result=json_response['result'],
                reason=json_response.get('reason', None),
                metadata=json_response.get('metadata', {})
            )

        raise RemoteCriteriaError(f'[check_criteria] failed with status: {response.status_code}')
    
    @staticmethod
    def check_snapshot_version(token: Optional[str], context: Context, snapshot_version: int) -> bool:
        url = f'{context.url}/criteria/snapshot_check/{snapshot_version}'
        response = Remote.__do_get(url, Remote.__get_header(token))
        
        if response.status_code == 200:
            return response.json().get('status', False)

        raise RemoteError(f'[check_snapshot_version] failed with status: {response.status_code}')
    
    @staticmethod
    def resolve_snapshot(token: Optional[str], context: Context) -> str | None:
        domain = get(context.domain, '')
        environment = get(context.environment, DEFAULT_ENVIRONMENT)
        component = get(context.component, '')

        data = {
            "query": f"""
                query domain {{
                    domain(name: "{domain}", environment: "{environment}", _component: "{component}") {{
                    name version activated
                    group {{ name activated
                        config {{ key activated
                            strategies {{ strategy activated operation values }}
                            relay {{ type  activated }}
                            components
                        }}
                    }}
                }}
            }}
            """
        }

        response = Remote.__do_post(f'{context.url}/graphql', data, Remote.__get_header(token))

        if response.status_code == 200:
            return json.dumps(response.json().get('data', {}), indent=4)
        
        raise RemoteError(f'[resolve_snapshot] failed with status: {response.status_code}')
    
    @classmethod
    def __get_client(cls) -> httpx.Client:
        if cls._client is None or cls._client.is_closed:
            cls._client = httpx.Client(
                timeout=30.0,
                limits=httpx.Limits(
                    max_keepalive_connections=20,
                    max_connections=100,
                    keepalive_expiry=30.0
                ),
                http2=True
            )
        return cls._client

    @staticmethod
    def __do_post(url, data, headers) -> httpx.Response:
        client = Remote.__get_client()
        return client.post(url, json=data, headers=headers)

    @staticmethod
    def __do_get(url, headers=None) -> httpx.Response:
        client = Remote.__get_client()
        return client.get(url, headers=headers)

    @staticmethod
    def __get_header(token: Optional[str]):
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
        }
    
    @staticmethod
    def __get_entry(input: list):
        entry = []
        for strategy_type, input_value in input:
            entry.append({
                'strategy': strategy_type,
                'input': input_value
            })
            
        if not entry:
            return None
        
        return {'entry': entry}