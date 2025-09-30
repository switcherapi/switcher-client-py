from typing import Optional

class GlobalAuth:
    __token = None
    __exp = None

    @staticmethod
    def init():
        GlobalAuth.__token = None
        GlobalAuth.__exp = None

    @staticmethod
    def get_token():
        return GlobalAuth.__token
    
    @staticmethod
    def get_exp():
        return GlobalAuth.__exp
    
    @staticmethod
    def set_token(token: str):
        GlobalAuth.__token = token

    @staticmethod
    def set_exp(exp: str):
        GlobalAuth.__exp = exp