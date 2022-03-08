# -*- coding: utf-8 -*-
# @Author   : xiaohuzi
# @Time     : 2022-03-08 14:47
import logging

import cfg4py
from flask import request

from thstrader.common import api
from thstrader.config import app
from thstrader.apps import response
from thstrader.config.schema import Config

global_store = {}
logger = logging.getLogger(__name__)
cfg: Config = cfg4py.get_instance()


@app.route("/prepare", methods=["POST"])
@response
def post_prepare():
    user = api.use(cfg.borker)
    user.prepare(**{
        "user": cfg.user,
        "password": cfg.password,
        "exe_path": cfg.exe_path,
    })
    if cfg.enable_type_keys_for_editor:
        user.enable_type_keys_for_editor()
    global_store["user"] = user
    return {"msg": "login success"}


@app.route("/balance", methods=["POST"])
@response
def get_balance():
    user = global_store["user"]
    balance = user.balance
    return balance


@app.route("/position", methods=["POST"])
@response
def get_position():
    user = global_store["user"]
    position = user.position

    return position


@app.route("/auto_ipo", methods=["POST"])
@response
def get_auto_ipo():
    user = global_store["user"]
    res = user.auto_ipo()

    return res


@app.route("/today_entrusts", methods=["POST"])
@response
def get_today_entrusts():
    user = global_store["user"]
    today_entrusts = user.today_entrusts

    return today_entrusts


@app.route("/today_trades", methods=["POST"])
@response
def get_today_trades():
    user = global_store["user"]
    today_trades = user.today_trades

    return today_trades


@app.route("/cancel_entrusts", methods=["POST"])
@response
def get_cancel_entrusts():
    user = global_store["user"]
    cancel_entrusts = user.cancel_entrusts

    return cancel_entrusts


@app.route("/buy", methods=["POST"])
@response
def post_buy():
    json_data = request.get_json(force=True)
    user = global_store["user"]
    res = user.buy(**json_data)

    return res


@app.route("/sell", methods=["POST"])
@response
def post_sell():
    json_data = request.get_json(force=True)

    user = global_store["user"]
    res = user.sell(**json_data)

    return res


@app.route("/cancel_entrust", methods=["POST"])
@response
def post_cancel_entrust():
    json_data = request.get_json(force=True)

    user = global_store["user"]
    res = user.cancel_entrust(**json_data)

    return res


@app.route("/exit", methods=["POST"])
@response
def get_exit():
    user = global_store["user"]
    user.exit()

    return {"msg": "exit success"}
