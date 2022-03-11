# -*- coding: utf-8 -*-
# @Author   : xiaohuzi
# @Time     : 2022-03-08 14:47
import functools
import logging

import cfg4py
from flask import request

from thstrader.common import api
from thstrader.config import app
from thstrader.apps import response
from thstrader.apps.handler import QueryEntrust
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
        gui_lock.acquire()
        prepare()  # 检查登录操作
        try:
            resp = func(*args, **kwargs)
        except Exception as e:
            raise e
        finally:
            gui_lock.release()

        return resp

    return wrapper


@app.route("/", methods=["POST"])
@response
def index(request_id):
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
@response
def get_balance(request_id):
    user = global_store["user"]
    balance = user.balance()
    return balance


@app.route("/position", methods=["POST"])
@response
def get_position(request_id):
    user = global_store["user"]
    position = user.position()

    return position


@app.route("/auto_ipo", methods=["POST"])
@response
def get_auto_ipo(request_id):
    user = global_store["user"]
    res = user.auto_ipo()

    return res


@app.route("/today_entrusts", methods=["POST"])
@serialization_lock
@response
def get_today_entrusts(request_id):
    user = global_store["user"]

    today_entrusts = user.today_entrusts()

    return user.entrust_list_to_dict(today_entrusts)


@app.route("/today_trades", methods=["POST"])
@serialization_lock
@response
def get_today_trades(request_id):
    user = global_store["user"]
    today_trades = user.today_trades()
    return today_trades


@app.route("/today_trades_and_entrusts", methods=["POST"])
@serialization_lock
@response
def get_today_trades_and_entrusts(request_id):
    """获取今日委托单和成交单"""
    user = global_store["user"]
    today_trades = user.today_trades()  # 先查成交单是为了防止先查询委托单后，已成交数量对应不上的情况
    trade_data = user.trader_list_to_dict(today_trades)
    today_entrusts = user.today_entrusts()
    entrusts_data = QueryEntrust.entrust_list_to_dict(today_entrusts)
    # 将数据进行合并
    for entrusts in entrusts_data:
        entrusts_data[entrusts_data]["trader_order"] = trade_data.get(entrusts)
    return entrusts_data


@app.route("/cancel_entrusts", methods=["POST"])
@response
def get_cancel_entrusts(request_id):
    user = global_store["user"]
    cancel_entrusts = user.cancel_entrusts()

    return cancel_entrusts


@app.route("/buy", methods=["POST"])
@serialization_lock
@response
def post_buy(request_id):
    """
    根据买的request_id来绑定子账户
    """
    json_data = request.get_json(force=True)
    user = global_store["user"]
    resp = user.buy(**json_data)
    entrust_no = resp.get("entrust_no")
    entrusts = user.today_entrusts()  # 查询当日委托
    # 遍历找到刚刚委托的订单
    entrust_data = QueryEntrust.analysis_entrust_data(entrust_no, entrusts)
    resp.update(entrust_data)
    return resp


@app.route("/sell", methods=["POST"])
@serialization_lock
@response
def post_sell(request_id):
    json_data = request.get_json(force=True)

    user = global_store["user"]
    res = user.sell(**json_data)

    return res


@app.route("/cancel_entrust", methods=["POST"])
@response
def post_cancel_entrust(request_id):
    json_data = request.get_json(force=True)

    user = global_store["user"]
    res = user.cancel_entrust(**json_data)

    return res


@app.route("/exit", methods=["POST"])
@response
def get_exit(request_id):
    user = global_store["user"]
    user.exit()

    return {"msg": "exit success"}
