# -*- coding: utf-8 -*-
# @Author   : xiaohuzi
# @Time     : 2022-03-08 14:47
import functools
import logging
from collections.abc import Iterable

import cfg4py
from flask import views, request, Response, jsonify

from thstrader.common import exceptions
from thstrader.config import Config

cfg: Config = cfg4py.get_instance()
logger = logging.getLogger(__name__)


def response(func):
    """中间件，检查调用的来源是否有权限"""

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        resp = {"status": 0, "msg": "ok"}
        result = {}
        request_id = request.headers.get("request_id")
        token = request.headers.get("Authorization")
        try:
            # 将request_id 记录进redis
            if not request_id:
                raise exceptions.MissHeaderRequestID()
            # 检查传过来的用户名和token是否匹配
            if not token:
                raise exceptions.MissHeaderToken()
            if token != cfg.api_token:
                raise exceptions.ErrorHeaderToken()
            result = await func(request, *args, **kwargs)
        except exceptions.APIException as e:
            resp.update({"status": e.error_code, "msg": e.msg})
        except Exception as e:
            logger.exception(e)
            resp.update({"status": 1, "msg": "服务器异常"})

        if isinstance(result, Response):
            return result
        if isinstance(result, Iterable):
            result = {"data": result}
        resp.update(result)
        resp = jsonify(resp)
        return resp

    return wrapper


class BaseView(views.MethodView):
    """所有视图的基类，都继承这个"""

    decorators = [response]
