import time

from typing import Optional
from pytest_httpx import HTTPXMock

from switcher_client.client import Client
from switcher_client.lib.globals.global_context import DEFAULT_ENVIRONMENT, ContextOptions

def given_context(*,
                url='https://api.switcherapi.com',
                api_key='[API_KEY]',
                domain='Switcher API',
                component='switcher-client-python',
                environment=DEFAULT_ENVIRONMENT,
                options=ContextOptions()):
    Client.build_context(
        url=url,
        api_key=api_key,
        domain=domain,
        component=component,
        environment=environment,
        options=options
    )

def given_auth(httpx_mock: HTTPXMock, status=200, token: Optional[str]='[token]', exp=int(round(time.time() * 1000)), is_reusable=False):
    httpx_mock.add_response(
        url='https://api.switcherapi.com/criteria/auth',
        method='POST',
        status_code=status,
        json={'token': token, 'exp': exp},
        is_reusable=is_reusable
    )

def given_check_criteria(httpx_mock: HTTPXMock, status=200, key='MY_SWITCHER', response={}, show_details=False, match=None):
    httpx_mock.add_response(
        is_reusable=True,
        url=f'https://api.switcherapi.com/criteria?showReason={str(show_details).lower()}&key={key}',
        method='POST',
        status_code=status,
        json=response,
        match_json=match
    )

def given_check_switchers(httpx_mock: HTTPXMock, status=200, not_found: Optional[list[str]]=None):
    httpx_mock.add_response(
        url='https://api.switcherapi.com/criteria/switchers_check',
        method='POST',
        status_code=status,
        json={'not_found': not_found or []}
    )

def given_check_health(httpx_mock: HTTPXMock, status=200):
    httpx_mock.add_response(
        is_reusable=False,
        url='https://api.switcherapi.com/check',
        method='GET',
        status_code=status,
    )

def given_check_snapshot_version(httpx_mock: HTTPXMock, status_code=200, version=0, status=False, is_reusable=False):
    httpx_mock.add_response(
        url=f'https://api.switcherapi.com/criteria/snapshot_check/{version}',
        method='GET',
        status_code=status_code,
        json={'status': status},
        is_reusable=is_reusable
    )

def given_resolve_snapshot(httpx_mock: HTTPXMock, status_code=200, data=[], is_reusable=False):
    httpx_mock.add_response(
        url='https://api.switcherapi.com/graphql',
        method='POST',
        status_code=status_code,
        json={'data': { 'domain': data}},
        is_reusable=is_reusable
    )