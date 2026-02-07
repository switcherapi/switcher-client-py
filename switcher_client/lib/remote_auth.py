from time import time
from datetime import datetime

from .remote import Remote
from .globals.global_context import Context
from .globals import GlobalAuth, RetryOptions
from .utils.date_moment import DateMoment

class RemoteAuth:
    __context: Context = Context.empty()
    __retry_options: RetryOptions

    @staticmethod
    def init(context: Context):
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
        token, exp = Remote.auth(RemoteAuth.__context)
        GlobalAuth.set_token(token)
        GlobalAuth.set_exp(exp)

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
