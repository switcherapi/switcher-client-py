class RetryOptions:
    def __init__(self, retry_time: int, retry_duration_in: str):
        """
        :param retry_time: The maximum number of retries
        :param retry_duration_in: The duration to wait between retries (e.g. '5s' (s: seconds - m: minutes - h: hours))
        """
        self.retry_time = retry_time
        self.retry_duration_in = retry_duration_in