import threading

from time import time
from functools import partial
from datetime import datetime
from typing import Optional

from switcher_client.lib.remote import Remote
from switcher_client.lib.globals.global_context import Context
from switcher_client.lib.globals import GlobalAuth, RetryOptions
from switcher_client.lib.utils.date_moment import DateMoment

class RemoteAuth:
    """
    RemoteAuth handles authentication with the remote switcher service.
    It manages the authentication token, checks for token expiration, and handles silent mode token updates.
    """

    __context: Context = Context.empty()
    __retry_options: RetryOptions
    __auto_renew_timer: Optional[threading.Timer] = None
    __auto_renew_generation: int = 0
    __auto_renew_lock = threading.Lock()
    __auto_renew_buffer_seconds = 5.0
    __auto_renew_min_delay_seconds = 1.0

    @staticmethod
    def init(context: Context):
        RemoteAuth._stop_auto_renew()
        RemoteAuth.__context = context
        GlobalAuth.init()

    @staticmethod
    def set_retry_options(silent_mode: str):
        RemoteAuth.__retry_options = RetryOptions(
            retry_time=int(silent_mode[:-1]),
            retry_duration_in=silent_mode[-1]
        )

    @staticmethod
    def auth():
        RemoteAuth._refresh_token()

    @staticmethod
    def check_health():
        if GlobalAuth.get_token() != 'SILENT':
            return

        if RemoteAuth.is_token_expired():
            RemoteAuth.update_silent_token()
            if Remote.check_api_health(RemoteAuth.__context):
                RemoteAuth.auth()

    @staticmethod
    def is_token_expired() -> bool:
        exp = GlobalAuth.get_exp()
        if exp is None:
            return True

        return float(exp) < time()

    @staticmethod
    def update_silent_token():
        expiration_time = DateMoment(datetime.now()).add(
            RemoteAuth.__retry_options.retry_time,
            RemoteAuth.__retry_options.retry_duration_in
        ).get_date().timestamp()

        GlobalAuth.set_token('SILENT')
        GlobalAuth.set_exp(str(round(expiration_time)))

    @staticmethod
    def is_valid():
        required_fields = [
            ('url', RemoteAuth.__context.url),
            ('component', RemoteAuth.__context.component),
            ('api_key', RemoteAuth.__context.api_key),
        ]

        errors = [name for name, value in required_fields if not value]
        if errors:
            raise ValueError(f"Something went wrong: Missing or empty required fields ({', '.join(errors)})")

    @staticmethod
    def _refresh_token(schedule_next: bool = True, generation: Optional[int] = None):
        # Prevent token refresh if the generation is stale
        if not RemoteAuth._is_current_generation(generation):
            return

        token, exp = Remote.auth(RemoteAuth.__context)

        # Timer is valid, another thread may have already updated the token, so we should not overwrite it
        if not RemoteAuth._is_current_generation(generation):
            return

        GlobalAuth.set_token(token)
        GlobalAuth.set_exp(exp)

        if schedule_next:
            RemoteAuth._schedule_auto_renew(exp)

    @staticmethod
    def _schedule_auto_renew(exp: str):
        if not RemoteAuth.__context.options.remote.auto_renew_token:
            return

        delay = RemoteAuth._get_auto_renew_delay(exp)
        with RemoteAuth.__auto_renew_lock:
            RemoteAuth.__auto_renew_generation += 1
            current_generation = RemoteAuth.__auto_renew_generation
            previous_timer = RemoteAuth.__auto_renew_timer

        timer = threading.Timer(delay, partial(RemoteAuth._auto_renew, current_generation))
        timer.daemon = True

        with RemoteAuth.__auto_renew_lock:
            RemoteAuth.__auto_renew_timer = timer

        if previous_timer is not None:
            previous_timer.cancel()

        timer.start()

    @staticmethod
    def _auto_renew(generation: int):
        try:
            RemoteAuth._refresh_token(generation=generation)
        except Exception:  # pylint: disable=broad-exception-caught
            RemoteAuth._stop_auto_renew(generation)

    @staticmethod
    def _stop_auto_renew(generation: Optional[int] = None):
        with RemoteAuth.__auto_renew_lock:
            if generation is not None and generation != RemoteAuth.__auto_renew_generation:
                return

            RemoteAuth.__auto_renew_generation += 1
            timer = RemoteAuth.__auto_renew_timer
            RemoteAuth.__auto_renew_timer = None

        if timer is not None:
            timer.cancel()

    @staticmethod
    def _is_current_generation(generation: Optional[int]) -> bool:
        if generation is None:
            return True

        with RemoteAuth.__auto_renew_lock:
            return generation == RemoteAuth.__auto_renew_generation

    @staticmethod
    def _get_auto_renew_delay(exp: str) -> float:
        expiration = float(exp)
        remaining = expiration - time()
        delay = remaining - RemoteAuth.__auto_renew_buffer_seconds
        return max(delay, RemoteAuth.__auto_renew_min_delay_seconds)
