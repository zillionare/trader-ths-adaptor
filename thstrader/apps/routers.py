# -*- coding: utf-8 -*-
# @Author   : xiaohuzi
# @Time     : 2022-03-08 14:47
import logging
from tkinter import N

import cfg4py
from flask import request

from thstrader.common import api
from thstrader.config import app
from thstrader.apps import response
from thstrader.apps.handler import Action, LocalOrderData, TimedQueryEntrust

from thstrader.config.schema import Config

global_store = {}
logger = logging.getLogger(__name__)
cfg: Config = cfg4py.get_instance()


def sss():
    import time
    time.sleep(100)


@app.route("/", methods=["POST"])
@response
def index(request_id):
    action = Action(sss)
    action.put_self()


@app.before_request
def prepare():
    if TimedQueryEntrust.user is not None:
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
    TimedQueryEntrust.user = user


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
@response
def get_today_entrusts(request_id):
    print("=================")
    today_entrusts = TimedQueryEntrust.user.today_entrusts()

    return today_entrusts


@app.route("/today_trades", methods=["POST"])
@response
def get_today_trades(request_id):
    today_trades = TimedQueryEntrust.user.today_trades()
    return today_trades


@app.route("/cancel_entrusts", methods=["POST"])
@response
def get_cancel_entrusts(request_id):
    user = global_store["user"]
    cancel_entrusts = user.cancel_entrusts()

    return cancel_entrusts


def buy(security: str,
        price: float,
        volume: int,
        request_id: str):
    try:
        entrust = TimedQueryEntrust.user.buy(security,
                                price,
                                volume)
        print(f"购买完成：委托合同号是{entrust}")
    except Exception as e:
        logger.exception(e)
        entrust = None  # 说明委托失败，需要将账户资金返还回去
    if entrust is not None:
        entrust_no = entrust.get("entrust_no")
    side = 1
    local_order = LocalOrderData(security,
                                 price,
                                 volume,
                                 side,
                                 request_id,
                                 entrust_no
                                 )
    TimedQueryEntrust.order_list.append(local_order) 
    print("购买完成")
    print(TimedQueryEntrust.order_list)
    # 调用user.buy 去下单
    # 等待扫单定时任务执行
    return


@app.route("/buy", methods=["POST"])
@response
def post_buy(request_id):
    """
    根据买的request_id来绑定子账户
    """
    json_data = request.get_json(force=True)
    json_data.update({"request_id": request_id})
    action = Action(buy, **json_data)
    action.put_self()
    return 


@app.route("/sell", methods=["POST"])
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
