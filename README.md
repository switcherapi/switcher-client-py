***

<div align="center">
<b>Switcher Client SDK</b><br>
A Python SDK for Switcher API
</div>

<div align="center">

[![Master CI](https://github.com/switcherapi/switcher-client-py/actions/workflows/master.yml/badge.svg)](https://github.com/switcherapi/switcher-client-py/actions/workflows/master.yml)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=switcherapi_switcher-client-py&metric=alert_status)](https://sonarcloud.io/dashboard?id=switcherapi_switcher-client-py)
[![Known Vulnerabilities](https://snyk.io/test/github/switcherapi/switcher-client-py/badge.svg)](https://snyk.io/test/github/switcherapi/switcher-client-py)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Slack: Switcher-HQ](https://img.shields.io/badge/slack-@switcher/hq-blue.svg?logo=slack)](https://switcher-hq.slack.com/)

</div>

***

![Switcher API: Python Client: Cloud-based Feature Flag API](https://github.com/switcherapi/switcherapi-assets/blob/master/logo/switcherapi_python_client.png)

# About  
Python SDK for working with Switcher-API.
https://github.com/switcherapi/switcher-api

- Flexible and robust functions that will keep your code clean and maintainable.
- Able to work locally using a snapshot file downloaded from your remote Switcher-API Domain.
- Silent mode is a hybrid configuration that automatically enables a contingent sub-process in case of any connectivity issue.
- Built-in mock implementation for clear and easy implementation of automated testing.
- Easy to setup. Switcher Context is responsible to manage all the complexity between your application and API.

# Usage

## Install  
`pip install switcher-client`

## Module initialization
The context properties stores all information regarding connectivity.

```python
from switcher.client import Client

Client.build_context(
    domain='My Domain',
    url='https://api.switcherapi.com',
    api_key='[API_KEY]',
    component='MyApp',
    environment='default'
)

switcher = Client.get_switcher()
```

- **domain**: Domain name.
- **url**: (optional) Swither-API endpoint.
- **api_key**: (optional) Switcher-API key generated to your component.
- **component**: (optional) Application name.
- **environment**: (optional) Environment name. Production environment is named as 'default'.

## Options
You can also activate features such as local and silent mode:

```python
from switcher.client import Client

Client.build_context(
    domain='My Domain',
    url='https://api.switcherapi.com',
    api_key='[API_KEY]',
    component='MyApp',
    environment='default',
    options={
        'local': True,
        'logger': True,
        'snapshotLocation': './snapshot/',
        'snapshotAutoUpdateInterval': 3,
        'silentMode': '5m',
        'certPath': './certs/ca.pem'
    })

switcher = Client.get_switcher()
```

- **local**: If activated, the client will only fetch the configuration inside your snapshot file. The default value is 'false'
- **logger**: If activated, it is possible to retrieve the last results from a given Switcher key using Client.getLogger('KEY')
- **snapshotLocation**: Location of snapshot files. The default value is './snapshot/'
- **snapshotAutoUpdateInterval**: Enable Snapshot Auto Update given an interval in seconds (default: 0 disabled).
- **silentMode**: Enable contigency given the time for the client to retry - e.g. 5s (s: seconds - m: minutes - h: hours)
- **regexSafe**: Enable REGEX Safe mode - Prevent agaist reDOS attack (default: true).
- **regexMaxBlackList**: Number of entries cached when REGEX Strategy fails to perform (reDOS safe) - default: 50
- **regexMaxTimeLimit**: Time limit (ms) used by REGEX workers (reDOS safe) - default - 3000ms
- **certPath**: Path to the certificate file used to establish a secure connection with the API.

(*) regexSafe is a feature that prevents your application from being exposed to a reDOS attack. It is recommended to keep this feature enabled.<br>

## Executing
There are a few different ways to call the API using the JavaScript module.
Here are some examples:

1. **No parameters**
Invoking the API can be done by instantiating the switcher and calling *is_on* passing its key as a parameter.


```python
switcher = Client.get_switcher()
switcher.is_on('FEATURE01')
# or
response = switcher.is_on_with_details('FEATURE01')
print(response.result)  # True or False
print(response.reason)  # Reason for the result
print(response.metadata)  # Additional metadata if available
```

2. **Strategy validation - preparing input**
Loading information into the switcher can be made by using *prepare*, in case you want to include input from a different place of your code. Otherwise, it is also possible to include everything in the same call.

```python
switcher.check_value('USER_1').prepare('FEATURE01')
switcher.is_on()
```

3. **Strategy validation - all-in-one execution**
All-in-one method is fast and include everything you need to execute a complex call to the API.

```python
switcher.check_value('User 1').check_network('192.168.0.1').is_on('FEATURE01')
```

4. **Throttle**
Throttling is useful when placing Feature Flags at critical code blocks require zero-latency without having to switch to local.
API calls will happen asynchronously and the result returned is based on the last API response.

```python
switcher.throttle(1000).is_on('FEATURE01')
```

In order to capture issues that may occur during the process, it is possible to log the error by subscribing to the error events.

```python
Client.subscribe_notify_error(lambda error: print(error))
```

5. **Hybrid mode**
Forcing Switchers to resolve remotely can help you define exclusive features that cannot be resolved locally.
This feature is ideal if you want to run the SDK in local mode but still want to resolve a specific switcher remotely.

```python
switcher.remote().is_on('FEATURE01')
```

## Built-in mock feature
You can also bypass your switcher configuration by invoking 'Client.assume'. This is perfect for your test code where you want to test both scenarios when the switcher is true and false.

```python
Client.assume('FEATURE01').true()
switcher.is_on('FEATURE01') # True

Client.forget('FEATURE01')
switcher.is_on('FEATURE01') # Now, it's going to return the result retrieved from the API or the Snaopshot file

Client.assume('FEATURE01').false().with_metadata({ 'message': 'Feature is disabled' }) # Include metadata to emulate Relay response
response = switcher.is_on_with_details('FEATURE01') # False
print(response.metadata['message']) # Feature is disabled
```

**Enabling Test Mode**
You may want to enable this feature while using Switcher Client with automated testing.
It prevents the Switcher Client from locking snapshot files even after the test execution.

To enable this feature, it is recommended to place the following on your test setup files:

```python
Client.enable_test_mode()
```

**Smoke Test**
Validate Switcher Keys on your testing pipelines before deploying a change.
Switcher Keys may not be configured correctly and can cause your code to have undesired results.

This feature will validate using the context provided to check if everything is up and running.
In case something is missing, this operation will throw an exception pointing out which Switcher Keys are not configured.

```python
Client.check_switchers(['FEATURE01', 'FEATURE02'])
```

## Loading Snapshot from the API
This step is optional if you want to load a copy of the configuration that can be used to eliminate latency when local mode is activated.<br>
Activate watchSnapshot optionally passing true in the arguments.<br>
Auto load Snapshot from API passing true as second argument.

```python
Client.load_snapshot()
```

## Watch for Snapshot file changes
Activate and monitor snapshot changes using this feature. Optionally, you can implement any action based on the callback response.

```python
Client.watch_snapshot({
    'success': lambda: print('In-memory snapshot updated'),
    'reject': lambda err: print(err)
})
```

## Snapshot version check
For convenience, an implementation of a domain version checker is available if you have external processes that manage snapshot files.

```python
Client.check_snapshot()
```

## Snapshot Update Scheduler
You can also schedule a snapshot update using the method below.<br>
It allows you to run the Client SDK in local mode (zero latency) and still have the snapshot updated automatically.

```python
Client.schedule_snapshot_auto_update(3000, {
    'success': lambda updated: print('Snapshot updated', updated),
    'reject': lambda err: print(err)
})
```