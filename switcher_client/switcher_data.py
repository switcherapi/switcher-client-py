from typing import Optional

class SwitcherData:
    def __init__(self, key: Optional[str] = None):
        self.key = key
        self.input = {}
        self.show_details = False