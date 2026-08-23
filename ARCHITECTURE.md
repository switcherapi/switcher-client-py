# Architecture

This document describes the design of the **Switcher Client SDK for Python** (`switcher_client`), from the public
API surface down to internal modules and execution flows. It complements [README.md](./README.md), which focuses on
usage, with the *why* and *how* behind the implementation.

## Table of Contents

- [Design Goals](#design-goals)
- [API-First Overview](#api-first-overview)
- [High-Level Architecture](#high-level-architecture)
- [Package Layout](#package-layout)
- [Core Components](#core-components)
  - [Client (Facade)](#client-facade)
  - [Context & Options](#context--options)
  - [Switcher / SwitcherData (Builder)](#switcher--switcherdata-builder)
  - [Resolver (Local Strategy Engine)](#resolver-local-strategy-engine)
  - [Remote & RemoteAuth (Remote Strategy Engine)](#remote--remoteauth-remote-strategy-engine)
  - [Bypasser (Mocking)](#bypasser-mocking)
  - [Snapshot Management](#snapshot-management)
  - [Execution Logger (Throttle Cache)](#execution-logger-throttle-cache)
  - [TimedMatch (ReDoS Protection)](#timedmatch-redos-protection)
  - [Errors](#errors)
  - [Testing Utilities](#testing-utilities)
- [Execution Flow](#execution-flow)
- [Software Patterns Used](#software-patterns-used)
- [Concurrency Model](#concurrency-model)
- [Extensibility Points](#extensibility-points)

---

## Design Goals

- **API-first**: a small, fluent, discoverable surface (`Client`, `Switcher`) hides internal complexity.
- **Local-first performance**: snapshot-based evaluation for zero-latency, offline-capable feature flags.
- **Resilience**: silent mode / circuit breaker automatically falls back to local evaluation when the remote
  API is unreachable.
- **Security by default**: regex (ReDoS) protection isolated in worker processes with timeouts and blacklisting.
- **Testability**: built-in mocking (`Bypasser`) that is safe under concurrent test execution via `ContextVar`.
- **Stateless module boundaries with static/class-level state**: most collaborators are static-method classes
  (namespaces) holding process-wide state, avoiding the need to thread dependencies through call sites.

## API-First Overview

The SDK is designed around the workflow described in the README:

1. `Client.build_context(...)` — configure domain, credentials, environment and `ContextOptions`.
2. `Client.get_switcher([key])` — obtain a `Switcher`, optionally cached/persisted by key.
3. `switcher.check_value(...).check_network(...)....is_on(key)` / `is_on_with_details(key)` — fluently attach
   strategy inputs and evaluate a criteria (locally or remotely).
4. Supporting capabilities are layered on top of this core loop: snapshot management, throttling, silent mode,
   hybrid (`remote()`) execution, mocking (`Client.assume/forget`, `switcher_test`/`assume_test`), and
   configuration validation (`Client.check_switchers`).

This mirrors a **Facade** (`Client`) in front of a **Fluent Builder** (`Switcher`/`SwitcherData`), keeping the
public API small while the internal library (`switcher_client.lib`) implements the heavier logic.

## High-Level Architecture

```
                          ┌───────────────────────────┐
                          │        Client (Facade)     │
                          │  build_context / get_switcher
                          │  load_snapshot / assume     │
                          └──────────────┬──────────────┘
                                         │ creates / configures
                                         ▼
                          ┌───────────────────────────┐
                          │   Switcher (SwitcherData)  │
                          │  fluent criteria builder    │
                          └──────────────┬──────────────┘
                                         │ is_on() / is_on_with_details()
                    ┌────────────────────┼─────────────────────┐
                    ▼                    ▼                     ▼
             ┌─────────────┐     ┌───────────────┐     ┌────────────────┐
             │  Bypasser    │     │ ExecutionLogger│    │   _submit()     │
             │ (mocks/tests)│     │ (throttle cache)│   │ local vs remote │
             └─────────────┘     └───────────────┘     └───┬────────┬────┘
                                                            ▼        ▼
                                                    ┌───────────┐ ┌──────────┐
                                                    │ Resolver   │ │  Remote  │
                                                    │ (local eval)│ │ (HTTP)  │
                                                    └─────┬─────┘ └────┬─────┘
                                                          │            │
                                                          ▼            ▼
                                                  ┌───────────────┐ ┌───────────┐
                                                  │ GlobalSnapshot │ │ RemoteAuth│
                                                  │ (snapshot state)│ │ (token)  │
                                                  └───────────────┘ └───────────┘
```

Cross-cutting infrastructure: `SnapshotAutoUpdater` and `SnapshotWatcher` (background threads keeping the
snapshot fresh), and `TimedMatch` (isolated-process regex evaluation used by the `Resolver`).

## Package Layout

```
switcher_client/
├── __init__.py                   # Public API surface (re-exports)
├── client.py                     # Client facade (entry point)
├── switcher.py                   # Switcher: execution/orchestration logic
├── switcher_data.py              # SwitcherData: fluent input builder (base class of Switcher)
├── testing.py                    # assume_test / switcher_test decorator utilities
├── version.py
├── errors/                       # Exception hierarchy
└── lib/                          # Internal implementation details
    ├── remote.py                 # HTTP client wrapper (httpx) for Switcher-API
    ├── remote_auth.py            # Token lifecycle, auto-renew, silent-mode token
    ├── resolver.py               # Local snapshot-based criteria evaluation
    ├── snapshot.py               # StrategiesType/OperationsType + operation processors
    ├── snapshot_loader.py        # Load/save/validate snapshot files, check_switchers (local)
    ├── snapshot_auto_updater.py  # Background thread: periodic snapshot refresh
    ├── snapshot_watcher.py       # Background thread: file-change watcher
    ├── types.py                  # Domain model (Snapshot, Domain, Group, Config, StrategyConfig, ResultDetail)
    ├── compat.py                 # typing.Self polyfill for older Python versions
    ├── bypasser/                 # Mocking engine (Bypasser, Key)
    ├── globals/                  # Process-wide state (Context, GlobalAuth, GlobalSnapshot, RetryOptions)
    └── utils/                    # execution_logger, ipcidr, payload_reader, date_moment, timed_match/
```

## Core Components

### Client (Facade)

`switcher_client/client.py`

- Static-only class (namespace) that is the single entry point for consumers.
- Owns process-wide singletons: `_context` (`Context`), `_switcher` (cache of named `Switcher` instances),
  `_snapshot_auto_updater`, `_snapshot_watcher`, `_test_mode`.
- `build_context()` resets/initializes all collaborators (`Bypasser`, `GlobalSnapshot`, `RemoteAuth`) and applies
  `ContextOptions` via a **handler-table dispatch** (`_build_options`) rather than nested conditionals — new
  options are added by registering a handler, not by modifying branching logic.
- Delegates snapshot lifecycle (`load_snapshot`, `check_snapshot`, `schedule_snapshot_auto_update`,
  `watch_snapshot`), mocking (`assume`/`forget`), execution introspection (`get_execution`, `clear_logger`), and
  validation (`check_switchers`) to the appropriate `lib` module.

### Context & Options

`switcher_client/lib/globals/global_context.py`

- `Context` is a plain data holder for connection info (`domain`, `url`, `api_key`, `component`, `environment`)
  plus a `ContextOptions` instance — passed explicitly to `Switcher`/`SwitcherData` rather than accessed as a
  global, which keeps evaluation logic testable and free of hidden global reads.
- `ContextOptions` centralizes all tunables (local mode, logger, freeze, snapshot location/interval, silent
  mode, throttle workers, regex limits, `restrict_relay`) with documented defaults.
- `RemoteOptions` isolates HTTP transport tuning (timeouts, connection pool limits, cert path, auto-renew) so
  `Remote`'s `httpx.Client` can be rebuilt only when its configuration actually changes.

### Switcher / SwitcherData (Builder)

`switcher_client/switcher.py`, `switcher_client/switcher_data.py`

- `SwitcherData` is an abstract base implementing the **fluent builder** pattern: `check_value`,
  `check_network`, `check_regex`, `check_payload`, `throttle`, `remote`, `default_result`, `restrict_relay` all
  return `Self`, enabling method chaining (`switcher.check_value(...).check_network(...).is_on(key)`).
- `Switcher` extends `SwitcherData` and adds **execution behavior**: `is_on`, `is_on_with_details`, `prepare`,
  `validate`, and the internal `_submit` dispatcher.
- `_submit()` is the routing decision point: bypass (mocks) → cache (throttle) → local snapshot vs. remote API
  vs. silent-mode fallback, wrapping remote failures with `default_result`/`silent_mode` recovery.
- Each `Switcher` owns a dedicated `ThreadPoolExecutor` (`_background_executor`) for non-blocking cache
  refreshes when throttling is enabled (see [Concurrency Model](#concurrency-model)).

### Resolver (Local Strategy Engine)

`switcher_client/lib/resolver.py`, `switcher_client/lib/snapshot.py`

- Pure, static, side-effect-free evaluator that walks the snapshot tree: `Domain → Group → Config →
  StrategyConfig`, short-circuiting on the first disabling condition (domain/group/config disabled, relay
  restriction, unmet strategy).
- Strategy evaluation is delegated to `snapshot.process_operation`, which **dispatches by `StrategiesType`**
  (`VALUE`, `NUMERIC`, `DATE`, `TIME`, `PAYLOAD`, `NETWORK`, `REGEX`) using Python's structural `match`
  statement — a clean **Strategy pattern** without a class-per-strategy, since each strategy is a small pure
  function operating on `(operation, values, input_value)`.
- `OperationsType` enumerates supported operations per strategy (`EXIST`, `EQUAL`, `BETWEEN`, `HAS_ONE`, etc.).

### Remote & RemoteAuth (Remote Strategy Engine)

`switcher_client/lib/remote.py`, `switcher_client/lib/remote_auth.py`

- `Remote` wraps `httpx.Client` for all Switcher-API HTTP calls (`auth`, `check_api_health`, `check_criteria`,
  `check_switchers`, `check_snapshot_version`, `resolve_snapshot` via GraphQL). It **lazily rebuilds** the
  client only when `RemoteOptions` change (`_get_client_config` fingerprinting), reusing keep-alive connections
  otherwise.
- Network errors are normalized into `RemoteError` subclasses so callers never see raw `httpx` exceptions.
- `RemoteAuth` owns the authentication token lifecycle: acquiring tokens, detecting expiration
  (`is_token_expired`), and — when `silent_mode` is configured — setting a sentinel `'SILENT'` token with a
  computed expiration so the system knows to evaluate locally until connectivity is restored
  (`check_health`/`update_silent_token`).
- Optional **auto-renew** (`RemoteOptions.auto_renew_token`) schedules a `threading.Timer` to refresh the token
  shortly before expiry; a monotonically increasing *generation counter* guards against races between
  overlapping timers/threads (stale generations are dropped).

### Bypasser (Mocking)

`switcher_client/lib/bypasser/bypasser.py`, `key.py`

- `Bypasser` stores forced ("assumed") switcher values in a `contextvars.ContextVar`, not a plain dict — this
  scopes mocks to the current execution context (thread/async task), preventing leakage across concurrently
  running tests in the same process.
- `Key` is a small fluent builder (`true()/false()/when()/with_metadata()`) producing a `ResultDetail` on
  `get_response`, optionally varying the result based on `when(strategy, input)` conditions matched against the
  actual inputs passed to `is_on`.
- Checked first in `Switcher.is_on`/`is_on_with_details`, short-circuiting both cache and network/local
  evaluation — mocks always win.

### Snapshot Management

`switcher_client/lib/globals/global_snapshot.py`, `snapshot_loader.py`, `snapshot_auto_updater.py`,
`snapshot_watcher.py`

- `GlobalSnapshot` is process-wide storage for the currently loaded `Snapshot` (parsed domain tree).
- `snapshot_loader.py` handles I/O: reading/writing `{environment}.json` snapshot files, validating a snapshot
  against the remote version (`validate_snapshot`), and local `check_switchers` validation.
- `SnapshotAutoUpdater` runs a daemon thread that periodically calls back into `Client.check_snapshot`,
  invoking a user callback with `(error, updated)`.
- `SnapshotWatcher` runs a daemon thread polling the snapshot file's mtime (`_POLL_INTERVAL = 1s`) and reloads
  `GlobalSnapshot` on change, notifying a `WatchSnapshotCallback` (`success`/`reject`).
- Both background services are disabled/guarded in `Client.test_mode()` to avoid file-locking issues in test
  suites.

### Execution Logger (Throttle Cache)

`switcher_client/lib/utils/execution_logger.py`

- In-memory list-based cache keyed by `(key, inputs)`, used to serve `throttle()`-enabled switchers without
  hitting local/remote evaluation on every call.
- Also the mechanism behind `Client.get_execution(switcher)` (introspection) and asynchronous error
  notification (`subscribe_notify_error`) surfaced when background refreshes or silent-mode fallbacks fail.
- **Design strategy: Stale-While-Revalidate (SWR)**. `throttle(period)` does not block callers waiting for a
  fresh evaluation; instead `Switcher._try_cached_result()` immediately returns the last cached `ResultDetail`
  ("stale") from `ExecutionLogger`, and — unless `freeze` is enabled — kicks off `schedule_background_refresh()`
  ("revalidate") on the switcher's own `ThreadPoolExecutor`. The refresh runs `_submit()` asynchronously and
  overwrites the cache entry (`ExecutionLogger.add`) once it completes, so the *next* call after `period`
  milliseconds observes the updated value. `_next_refresh_time` acts as the revalidation gate, ensuring only
  one background refresh is in flight per throttle period. This trades strict consistency for consistently
  low, predictable latency — the same trade-off popularized by HTTP's `stale-while-revalidate` `Cache-Control`
  directive (RFC 5861).

### TimedMatch (ReDoS Protection)

`switcher_client/lib/utils/timed_match/`

- Implements the SDK's **security feature**: regex evaluation is delegated to a persistent worker subprocess
  (`multiprocessing`, `spawn` context) so a catastrophic/pathological regex cannot block or crash the main
  process — it is simply terminated and replaced after `regex_max_time_limit` elapses.
- Maintains a bounded **blacklist** (`regex_max_black_list`) of previously-timed-out `(patterns, input)`
  combinations to short-circuit repeat attempts without re-invoking the worker.
- `worker.py` defines the message protocol (`WorkerTask`/`WorkerResult`, `TaskType.MATCH`/`SHUTDOWN`) exchanged
  over `multiprocessing.Queue`s with the isolated worker loop (`persistent_regex_worker`).

### Errors

`switcher_client/errors/__init__.py`

- Flat, purpose-specific exception hierarchy rooted at `RemoteError` (remote-only) plus standalone
  `LocalSwitcherError`, `LocalCriteriaError`, `SnapshotNotFoundError`, `TestModeError` — each mapped to a
  specific failure mode (auth, criteria evaluation, switcher-not-found, missing snapshot, disallowed test-mode
  operation), enabling callers to `except` precisely.

### Testing Utilities

`switcher_client/testing.py`

- `assume_test(key)` builds a `TestAssumption` (deep-clonable fluent builder mirroring `Key`'s API).
- `@switcher_test(*assumptions)` is a decorator (supporting both sync and `async def` tests) that applies
  assumptions via `Client.assume` before the test and guarantees `Client.forget` cleanup in a `finally` block,
  even on test failure — built on top of `Bypasser`'s context-scoped mocking for safe concurrent test runs.

## Execution Flow

`switcher.is_on(key)` / `is_on_with_details(key)`:

1. **Validate args** — update `_key`/`_show_details` if provided.
2. **Bypasser check** — if a mock was registered via `Client.assume(key)`, return its (possibly `when`-derived)
   result immediately.
3. **Cache check** — if throttling is enabled and a cached `ExecutionLogger` entry exists, return it (and
   opportunistically schedule a background refresh unless `freeze` is set).
4. **`_submit()`**:
   - If `local` is enabled and not forced remote → `_execute_local_criteria()` (via `Resolver` +
     `GlobalSnapshot`).
   - Else → `validate()` (checks auth/token/API health), then:
     - If the auth token is the `'SILENT'` sentinel → evaluate locally instead.
     - Otherwise → `_execute_remote_criteria()` (via `Remote.check_criteria`).
   - On any exception during remote evaluation: notify subscribed error callback; if `silent_mode` is
     configured, switch the token to `'SILENT'` and retry locally; otherwise propagate (unless
     `default_result` was set, in which case that value is returned instead of raising).

## Software Patterns Used

| Pattern | Where | Purpose |
|---|---|---|
| **Facade** | `Client` | Single simplified entry point over many internal subsystems |
| **Fluent Builder** | `SwitcherData`/`Switcher`, `Key`, `TestAssumption` | Chainable, readable criteria/mock construction |
| **Strategy** | `snapshot.process_operation` dispatch by `StrategiesType` | Pluggable evaluation logic per strategy type |
| **Static namespace / Singleton-like state** | `Client`, `GlobalAuth`, `GlobalSnapshot`, `RemoteAuth`, `Bypasser`, `ExecutionLogger`, `TimedMatch` | Process-wide shared state without DI plumbing |
| **Circuit Breaker** | `RemoteAuth` silent mode + `Switcher._submit` | Fail fast to local evaluation when remote API is unavailable |
| **Stale-While-Revalidate** | `Switcher.throttle`/`_try_cached_result`/`schedule_background_refresh` + `ExecutionLogger` | Serve cached result instantly while refreshing it asynchronously |
| **Decorator** | `testing.switcher_test` | Test lifecycle wrapping (setup mocks / guaranteed cleanup) |
| **Context Object** | `Context`/`ContextOptions`/`RemoteOptions` | Explicit dependency passed to evaluators instead of hidden globals |
| **Producer/Consumer (worker process)** | `TimedMatch`/`worker.py` | Isolate untrusted regex execution with timeout + blacklist |
| **Data Transfer Object** | `types.py` (`Snapshot`, `Domain`, `Group`, `Config`, `StrategyConfig`, `ResultDetail`) | Typed, parsed representation of the snapshot JSON contract |

## Concurrency Model

- **Thread-based**: `SnapshotAutoUpdater` and `SnapshotWatcher` each run a single daemon `threading.Thread`;
  `Switcher` uses a per-instance `ThreadPoolExecutor` for background throttle refreshes; `RemoteAuth` uses
  `threading.Timer` for token auto-renewal, guarded by a lock and generation counter to avoid stale timers
  overwriting a newer token.
- **Process-based**: `TimedMatch` isolates regex execution in a separate `multiprocessing` worker to guarantee
  that a hung/malicious regex can be killed without affecting the host process.
- **Context-local state**: `Bypasser` uses `contextvars.ContextVar` so mocked values don't leak across
  concurrently executing async tasks/threads sharing the same process — critical for parallel test execution.

## Extensibility Points

- **New strategy type**: add an entry to `StrategiesType`, a `_process_<type>` function in `snapshot.py`, and a
  `case` in `process_operation`; add a corresponding `check_<type>` fluent method on `SwitcherData` if it should
  be user-facing.
- **New context option**: add a field to `ContextOptions` (and default constant), then register a handler in
  `Client._build_options` if it requires side effects on `build_context`.
- **New remote operation**: add a method to `Remote` following the existing `_do_get`/`_do_post` + typed
  `error_cls` convention.
- **New error type**: add to `switcher_client/errors/__init__.py` and export it in `__all__`.
