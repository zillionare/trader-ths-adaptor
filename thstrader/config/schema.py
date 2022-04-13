# noqa
from typing import Optional


class Config(object):
    __access_counter__ = 0

    def __cfg4py_reset_access_counter__(self):
        self.__access_counter__ = 0

    def __getattribute__(self, name):
        obj = object.__getattribute__(self, name)
        if name.startswith("__") and name.endswith("__"):
            return obj

        if callable(obj):
            return obj

        self.__access_counter__ += 1
        return obj

    def __init__(self):
        raise TypeError("Do NOT instantiate this class")

    log_level: Optional[str] = None

    user: Optional[str] = None

    password: Optional[str] = None

    exe_path: Optional[str] = None

    broker: Optional[str] = None

    enable_type_keys_for_editor: Optional[bool] = None

    api_token: Optional[str] = None

    commission: Optional[int] = None

    transfer_fee: Optional[int] = None

    stamp_duty: Optional[int] = None

    min_limit: Optional[int] = None
