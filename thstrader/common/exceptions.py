# -*- coding: utf-8 -*-
# @Author   : xiaohuzi
# @Time     : 2022-01-27 17:01
import logging

logger = logging.getLogger(__name__)


class APIException(Exception):
    """自定义异常类"""

    msg = "服务器内部异常"
    error_code = 1

    def __init__(self, msg=None, error_code=None):
        super(Exception, self).__init__()
        self.error_code = error_code or self.error_code
        self.msg = msg or self.msg


class MissHeaderRequestID(APIException):
    msg = "Miss Header Request ID"


class UserNotFound(APIException):
    msg = "User Not Found"


class MissHeaderToken(APIException):
    msg = "Miss Header Token"


class ErrorHeaderToken(APIException):
    msg = "Error Header Token"


class PermissionDenied(APIException):
    msg = "Permission Denied"


class UnsupportedSecuritiesCode(APIException):
    msg = "Unsupported Securities Code"


class ParamsRequire(APIException):
    def __init__(self, *msg):
        super(Exception, self).__init__()
        s = []
        for i in msg:
            s.append(i)
        self.msg = "Params [%s] Require" % ", ".join(s)


class TradeError(IOError):
    pass


class NotLoginError(Exception):
    def __init__(self, result=None):
        super(NotLoginError, self).__init__()
        self.result = result
