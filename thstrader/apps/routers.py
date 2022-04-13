# -*- coding: utf-8 -*-
# @Author   : xiaohuzi
# @Time     : 2022-03-08 14:47
import functools
import logging

import cfg4py
from flask import request

from thstrader.common import api, exceptions
from thstrader.config import app
from thstrader.apps import response
from threading import Lock
from thstrader.config.schema import Config

logger = logging.getLogger(__name__)
cfg: Config = cfg4py.get_instance()

global_store = {}
gui_lock = Lock()


def serialization_lock(func):
    """中间件，检查调用的来源是否有权限"""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        """执行每个请求之前，加锁"""
        try:
            gui_lock.acquire()
            prepare()  # 检查登录操作
            resp = func(*args, **kwargs)
        except Exception as e:
            raise e
        finally:
            gui_lock.release()

        return resp

    return wrapper


@app.route("/", methods=["POST"])
@response
def index():
    return


# @app.before_request
def prepare():
    if "user" in global_store:
        return
    user = api.use(cfg.broker)
    user.prepare(**{
        "user": cfg.user,
        "password": cfg.password,
        "exe_path": cfg.exe_path,
    })
    if cfg.enable_type_keys_for_editor:
        user.enable_type_keys_for_editor()
    global_store["user"] = user


@app.route("/balance", methods=["POST"])
@serialization_lock
@response
def get_balance():
    user = global_store["user"]
    resp = user.balance()

    return user.balance_to_dict(resp)


@app.route("/positions", methods=["POST"])
@serialization_lock
@response
def get_position():
    user = global_store["user"]
    position = user.position()

    return user.position_to_list(position)


@app.route("/auto_ipo", methods=["POST"])
@response
def get_auto_ipo():
    user = global_store["user"]
    res = user.auto_ipo()

    return res


@app.route("/today_entrusts", methods=["POST"])
@serialization_lock
@response
def get_today_entrusts():
    user = global_store["user"]
    return user.get_today_entrusts()


@app.route("/today_trades", methods=["POST"])
@serialization_lock
@response
def get_today_trades():
    user = global_store["user"]
    today_trades = user.today_trades()
    return today_trades


@app.route("/today_trades_and_entrusts", methods=["POST"])
@serialization_lock
@response
def get_today_trades_and_entrusts():
    """获取今日委托单和成交单"""
    user = global_store["user"]
    return user.get_today_entrusts()


@app.route("/buy", methods=["POST"])
@serialization_lock
@response
def post_buy():
    """
    根据买的来绑定子账户
    """
    json_data = request.get_json(force=True)
    user = global_store["user"]
    resp = user.buy(**json_data)
    entrust_no = resp.get("entrust_no")
    today_trades_and_entrusts = user.get_today_entrusts()
    entrust_data = today_trades_and_entrusts.get(entrust_no)
    resp.update(entrust_data)
    return resp


@app.route("/sell", methods=["POST"])
@serialization_lock
@response
def post_sell():
    json_data = request.get_json(force=True)
    user = global_store["user"]
    resp = user.sell(**json_data)
    entrust_no = resp.get("entrust_no")
    today_trades_and_entrusts = user.get_today_entrusts()
    entrust_data = today_trades_and_entrusts.get(entrust_no)
    resp.update(entrust_data)
    return resp


@app.route("/cancel_entrusts", methods=["POST"])
@serialization_lock
@response
def post_cancel_entrusts():
    json_data = request.get_json(force=True)
    entrust_no = json_data.get("entrust_no")
    user = global_store["user"]
    resp = user.cancel_entrust(entrust_no)
    if resp is False:
        # 说明撤单失败了
        raise exceptions.APIException("撤销失败")
    today_trades_and_entrusts = user.get_today_entrusts()
    result = {}
    for item in resp:
        result[item] = today_trades_and_entrusts.get(item)
    return result


@app.route("/cancel_entrust", methods=["POST"])
@serialization_lock
@response
def post_cancel_entrust():
    json_data = request.get_json(force=True)
    entrust_no = json_data.get("entrust_no")
    user = global_store["user"]
    resp = user.cancel_entrust([entrust_no])
    if not resp:
        # 说明撤单失败了
        raise exceptions.APIException("撤销失败")
    today_trades_and_entrusts = user.get_today_entrusts()
    entrust_data = today_trades_and_entrusts.get(entrust_no)
    return entrust_data


@app.route("/exit", methods=["POST"])
@response
def get_exit():
    user = global_store["user"]
    user.exit()

    return {"msg": "exit success"}
