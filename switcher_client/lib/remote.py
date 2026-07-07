from typing import Callable, Optional, Type

import json
import ssl
import httpx

from switcher_client.errors import RemoteAuthError, RemoteError, RemoteCriteriaError, RemoteSwitcherError
from switcher_client.lib.globals.global_context import DEFAULT_ENVIRONMENT, Context
from switcher_client.lib.types import ResultDetail
from switcher_client.lib.utils import get, get_entry
from switcher_client.switcher_data import SwitcherData

class Remote:
    """
    Remote handles all interactions with the remote switcher service,
    including authentication, criteria checks, and snapshot resolution.
    """
    _client: Optional[httpx.Client] = None
    _client_config: Optional[tuple[Optional[str], float, float, float, float, int, int, float]] = None

    @staticmethod
    def auth(context: Context):
        url = f'{context.url}/criteria/auth'
        response = Remote._do_post(
            context=context,
            url=url,
            data={
                'domain': context.domain,
                'component': context.component,
                'environment': context.environment,
            },
            headers={
                'switcher-api-key': context.api_key,
                'Content-Type': 'application/json',
            },
            operation='auth',
            error_cls=RemoteAuthError
        )

        if response.status_code == 200:
            return response.json()['token'], response.json()['exp']

        raise RemoteAuthError('Invalid API key')

    @staticmethod
    def check_api_health(context: Context) -> bool:
        url = f'{context.url}/check'
        try:
            response = Remote._do_get(context=context, url=url, operation='check_api_health')
        except RemoteError:
            return False

        return response.status_code == 200

    @staticmethod
    def check_criteria(token: Optional[str], context: Context, switcher: SwitcherData) -> ResultDetail:
        url = f'{context.url}/criteria?showReason={str(switcher.show_details).lower()}&key={switcher.key}'
        entry = get_entry(switcher.inputs)
        response = Remote._do_post(
            context=context,
            url=url,
            data={ 'entry': [e.to_dict() for e in entry] },
            headers=Remote._get_header(token),
            operation='check_criteria',
            error_cls=RemoteCriteriaError
        )

        if response.status_code == 200:
            json_response = response.json()
            return ResultDetail(
                result=json_response['result'],
                reason=json_response.get('reason', None),
                metadata=json_response.get('metadata', {})
            )

        raise RemoteCriteriaError(f'[check_criteria] failed with status: {response.status_code}')

    @staticmethod
    def check_switchers(token: Optional[str], switcher_keys: list[str], context: Context) -> None:
        url = f'{context.url}/criteria/switchers_check'
        response = Remote._do_post(
            context=context,
            url=url,
            data={ 'switchers': switcher_keys },
            headers=Remote._get_header(token),
            operation='check_switchers'
        )

        if response.status_code != 200:
            raise RemoteError(f'[check_switchers] failed with status: {response.status_code}')

        not_found = response.json().get('not_found', [])
        if len(not_found) > 0:
            raise RemoteSwitcherError(not_found)

    @staticmethod
    def check_snapshot_version(token: Optional[str], context: Context, snapshot_version: int) -> bool:
        url = f'{context.url}/criteria/snapshot_check/{snapshot_version}'
        response = Remote._do_get(
            context=context,
            url=url,
            headers=Remote._get_header(token),
            operation='check_snapshot_version'
        )

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

        response = Remote._do_post(
            context=context,
            url=f'{context.url}/graphql',
            data=data,
            headers=Remote._get_header(token),
            operation='resolve_snapshot'
        )

        if response.status_code == 200:
            return json.dumps(response.json().get('data', {}), indent=4)

        raise RemoteError(f'[resolve_snapshot] failed with status: {response.status_code}')

    @classmethod
    def _get_client(cls, context: Context) -> httpx.Client:
        client_config = cls._get_client_config(context)
        if cls._client is None or cls._client.is_closed or cls._client_config != client_config:
            if cls._client is not None and not cls._client.is_closed:
                cls._client.close()

            cls._client = httpx.Client(
                timeout=httpx.Timeout(
                    connect=context.options.remote.connect_timeout,
                    read=context.options.remote.read_timeout,
                    write=context.options.remote.write_timeout,
                    pool=context.options.remote.pool_timeout
                ),
                limits=httpx.Limits(
                    max_keepalive_connections=context.options.remote.max_keepalive_connections,
                    max_connections=context.options.remote.max_connections,
                    keepalive_expiry=context.options.remote.keepalive_expiry
                ),
                http2=True,
                verify=cls._get_context(context)
            )
            cls._client_config = client_config
        return cls._client

    @staticmethod
    # pylint: disable=too-many-arguments
    def _do_post(*, context: Context, url: str, data: dict, headers: Optional[dict] = None,
        operation: str, error_cls: Type[RemoteError] = RemoteError) -> httpx.Response:
        client = Remote._get_client(context)
        return Remote._request(
            lambda: client.post(url, json=data, headers=headers),
            operation,
            error_cls
        )

    @staticmethod
    def _do_get(*, context: Context, url: str, headers: Optional[dict] = None,
        operation: str, error_cls: Type[RemoteError] = RemoteError) -> httpx.Response:
        client = Remote._get_client(context)
        return Remote._request(
            lambda: client.get(url, headers=headers),
            operation,
            error_cls
        )

    @staticmethod
    def _get_header(token: Optional[str]) -> dict:
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
        }

    @staticmethod
    def _get_context(context: Context) -> bool | ssl.SSLContext:
        cert_path = context.options.remote.cert_path
        if cert_path is None:
            return True

        ctx = ssl.create_default_context()
        ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        ctx.load_cert_chain(certfile=cert_path)
        return ctx

    @staticmethod
    def _get_client_config(context: Context) -> tuple[Optional[str], float, float, float, float, int, int, float]:
        return (
            context.options.remote.cert_path,
            context.options.remote.connect_timeout,
            context.options.remote.read_timeout,
            context.options.remote.write_timeout,
            context.options.remote.pool_timeout,
            context.options.remote.max_keepalive_connections,
            context.options.remote.max_connections,
            context.options.remote.keepalive_expiry
        )

    @staticmethod
    def _request(
        request: Callable[[], httpx.Response],
        operation: str,
        error_cls: Type[RemoteError]
    ) -> httpx.Response:
        try:
            return request()
        except httpx.RequestError as exc:
            raise error_cls(f'[{operation}] remote unavailable') from exc
