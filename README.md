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

</div>

---

## Table of Contents

- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage Examples](#-usage-examples)
- [Advanced Features](#-advanced-features)
- [Snapshot Management](#-snapshot-management)
- [Testing & Development](#-testing--development)
- [Contributing](#-contributing)

---

## About

The **Switcher Client SDK for Python** provides seamless integration with [Switcher-API](https://github.com/switcherapi/switcher-api), enabling powerful feature flag management in your Python applications.

### Key Features

- **Clean & Maintainable**: Flexible and robust functions that keep your code organized
- **Local Mode**: Work offline using snapshot files from your Switcher-API Domain
- **Silent Mode**: Hybrid configuration with automatic fallback for connectivity issues
- **Built-in Mocking**: Easy implementation of automated testing with mock support
- **Zero Latency**: Local snapshot execution for high-performance scenarios
- **Secure**: Built-in protection against ReDoS attacks with regex safety features
- **Monitoring**: Comprehensive logging and error handling capabilities

## Quick Start

Get up and running in just a few lines of code:

```python
from switcher_client import Client

# Initialize the client
Client.build_context(
    domain='My Domain',
    url='https://api.switcherapi.com',
    api_key='[YOUR_API_KEY]',
    component='MyApp',
    environment='default'
)

# Use feature flags
switcher = Client.get_switcher()
if switcher.is_on('FEATURE_TOGGLE'):
    print("Feature is enabled!")
```

## Installation

Install the Switcher Client SDK using pip:

```bash
pip install switcher-client
```

### System Requirements
- **Python**: 3.9+ (supports 3.9, 3.10, 3.11, 3.12, 3.13, 3.14)
- **Operating System**: Cross-platform (Windows, macOS, Linux)

## Configuration

### Basic Setup

Initialize the Switcher Client with your domain configuration:

```python
from switcher_client import Client

Client.build_context(
    domain='My Domain',                 # Your Switcher domain name
    url='https://api.switcherapi.com',  # Switcher-API endpoint (optional)
    api_key='[YOUR_API_KEY]',           # Your component's API key (optional)
    component='MyApp',                  # Your application name (optional)
    environment='default'               # Environment ('default' for production)
)

switcher = Client.get_switcher()
```

#### Configuration Parameters

| Parameter | Required | Description | Default |
|-----------|----------|-------------|---------|
| `domain` | ✅ | Your Switcher domain name | - |
| `url` |  | Switcher-API endpoint | `https://api.switcherapi.com` |
| `api_key` |  | API key for your component | - |
| `component` |  | Your application identifier | - |
| `environment` |  | Target environment | `default` |

### Advanced Configuration

Enable additional features like local mode, silent mode, and security options:

```python
from switcher_client import Client, ContextOptions

Client.build_context(
    domain='My Domain',
    url='https://api.switcherapi.com',
    api_key='[YOUR_API_KEY]',
    component='MyApp',
    environment='default',
    options=ContextOptions(
        local=True,
        logger=True,
        freeze=True,
        snapshot_location='./snapshot/',
        snapshot_auto_update_interval=3,
        silent_mode='5m',
        throttle_max_workers=2,
        regex_max_black_list=10,
        regex_max_time_limit=100,
        cert_path='./certs/ca.pem'
    )
)

switcher = Client.get_switcher()
```

#### Advanced Options Reference

| Option | Type | Description | Default |
|--------|------|-------------|---------|
| `local` | `bool` | Use local snapshot files only (zero latency) | `False` |
| `logger` | `bool` | Enable logging/caching of feature flag evaluations | `False` |
| `freeze` | `bool` | Enable cache-immutability responses for consistent results | `False` |
| `snapshot_location` | `str` | Directory for snapshot files | `'./snapshot/'` |
| `snapshot_auto_update_interval` | `int` | Auto-update interval in seconds (0 = disabled) | `0` |
| `silent_mode` | `str` | Silent mode retry time (e.g., '5m' for 5 minutes) | `None` |
| `throttle_max_workers` | `int` | Max workers for throttling feature checks | `None` |
| `regex_max_black_list` | `int` | Max cached entries for failed regex | `100` |
| `regex_max_time_limit` | `int` | Regex execution time limit (ms) | `3000` |
| `cert_path` | `str` | 🚧 TODO - Path to custom certificate for API connections | `None` |

#### Security Features

- **ReDoS Protection**: Built-in ReDoS attack prevention with regex safety features
- **Time Limits**: Configurable timeouts prevent long-running regex operations
- **Certificate Support**: Use custom certificates for secure API connections  

## Usage Examples

### Basic Feature Flag Checking

The simplest way to check if a feature is enabled:

```python
switcher = Client.get_switcher()

# Simple boolean check
if switcher.is_on('FEATURE_LOGIN_V2'):
    # Use new login system
    new_login()
else:
    # Use legacy login
    legacy_login()
```

### Detailed Response Information

Get comprehensive information about the feature flag evaluation:

```python
response = switcher.is_on_with_details('FEATURE_LOGIN_V2')

print(f"Feature enabled: {response.result}")     # True or False
print(f"Reason: {response.reason}")              # Evaluation reason
print(f"Metadata: {response.metadata}")          # Additional context
```

### Strategy-Based Feature Flags

#### Method 1: Prepare and Execute

Load validation data separately, useful for complex applications:

```python
# Prepare the validation context
switcher.check_value('USER_123').prepare('USER_FEATURE')

# Execute when ready
if switcher.is_on():
    enable_user_feature()
```

#### Method 2: All-in-One Execution

Chain multiple validation strategies for comprehensive feature control:

```python
is_enabled = switcher \
                    # VALUE strategy
                    .check_value('premium_user') \
                    # NETWORK strategy
                    .check_network('192.168.1.0/24') \
                    # Fallback value if API fails
                    .default_result(True) \
                    # Cache result for 1 second
                    .throttle(1000) \
                    .is_on('PREMIUM_FEATURES')

if is_enabled:
    show_premium_dashboard()
```

### Error Handling

Subscribe to error notifications for robust error management:

```python
# Set up error handling
Client.subscribe_notify_error(lambda error: print(f"Switcher Error: {error}"))
```

## Advanced Features

### Planned Features

The following features are currently in development:

#### Throttling
```python
# Zero-latency async execution
switcher.throttle(1000).is_on('FEATURE01')
```

#### Hybrid Mode
```python
# Force remote resolution for specific features
switcher.remote().is_on('FEATURE01')
```

## Snapshot Management

### Loading Snapshots

Load configuration snapshots from the API for local/offline usage:

```python
# Download and save snapshot from API
Client.load_snapshot()
```

### Version Management

Check your current snapshot version:

```python
# Verify snapshot version
version_info = Client.check_snapshot()
print(f"Current snapshot version: {Client.snapshot_version()}")
```

### Automated Updates

Schedule automatic snapshot updates for zero-latency local mode:

```python
Client.schedule_snapshot_auto_update(
    interval=60,
    callback=lambda error, updated: (
        print(f"Snapshot updated to version: {Client.snapshot_version()}") if updated else None
    )
)
```

### Snapshot Monitoring (Coming Soon)

```python
# 🚧 TODO: Watch for snapshot file changes
Client.watch_snapshot({
    'success': lambda: print('In-memory snapshot updated'),
    'reject': lambda err: print(f'Update failed: {err}')
})
```

## Testing & Development

### Built-in Mocking (Coming Soon)

> 🚧 **Note**: The mocking features are currently under development

The SDK will include powerful mocking capabilities for testing:

```python
# 🚧 TODO: Mock feature states for testing
Client.assume('FEATURE01').true()
assert switcher.is_on('FEATURE01') == True

Client.forget('FEATURE01')  # Reset to normal behavior

# 🚧 TODO: Mock with metadata
Client.assume('FEATURE01').false().with_metadata({
    'message': 'Feature is disabled'
})
response = switcher.is_on_with_details('FEATURE01')
assert response.result == False
assert response.metadata['message'] == 'Feature is disabled'
```

### Test Mode Configuration

```python
# 🚧 TODO: Enable test mode to prevent file locking
Client.enable_test_mode()
```

### Configuration Validation

Validate your feature flag configuration before deployment:

```python
# Verify that all required switchers are configured
try:
    Client.check_switchers(['FEATURE_LOGIN', 'FEATURE_DASHBOARD', 'FEATURE_PAYMENTS'])
    print("✅ All switchers are properly configured")
except Exception as e:
    print(f"❌ Configuration error: {e}")
```

This validation helps prevent deployment issues by ensuring all required feature flags are properly set up in your Switcher domain.

## Contributing
We welcome contributions to the Switcher Client SDK for Python! If you have suggestions, improvements, or bug fixes, please follow these steps:

1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Make your changes and commit them with clear messages.
4. Submit a pull request detailing your changes and the problem they solve.

Thank you for helping us improve the Switcher Client SDK!

### Requirements
- Python 3.9 or higher
- Virtualenv - `pip install virtualenv`
- Create a virtual environment - `python3 -m venv .venv`
- Install Pipenv - `pip install pipenv`
- Check Makefile for all available commands