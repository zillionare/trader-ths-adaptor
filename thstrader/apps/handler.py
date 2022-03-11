# -*- coding: utf-8 -*-
# @Author   : xiaohuzi
# @Time     : 2022-03-09 09:38
import logging
import time
from thstrader.common.universal_clienttrader import UniversalClientTrader
from typing import Callable, List, Dict
from threading import Thread
import requests

logger = logging.getLogger(__name__)


class LocalOrderData:
    """保存了下单时的订单属性"""

    def __init__(self,
                 security: str,
                 price: float,
                 volume: int,
                 side: int,
                 request_id: str,
                 entrust_no: str,
                 ):
        self.security = security
        self.price = price
        self.volume = volume  # 委托数量
        self.side = side
        self.request_id = request_id
        self.entrust_no = entrust_no


class QueryEntrust:
    order_list = []  # type: List[LocalOrderData] # 需要查询的订单列表
    user: UniversalClientTrader = None  # 同花顺登录的用户的实例，只有有user 才可以查询和买卖
    """
    [{
            "Unnamed: 13": "",
            "交易市场": "深圳Ａ股",
            "合同编号": "2648899843",
            "备注": "未成交",
            "委托价格": 12.5,
            "委托数量": 100,
            "委托时间": "16:21:38",
            "成交均价": 0.0,
            "成交数量": 0,
            "撤消数量": 0,
            "操作": "买入",
            "股东帐户": 127934657,
            "证券代码": "000001",
            "证券名称": "平安银行"
        }]
    """

    status_map = {
        "未成交": 1,
        "部分成交": 2,
        "全部成交": 3,
        "全部撤单": 4,
    }

    @classmethod
    def entrust_list_to_dict(cls, entrust_data: list) -> Dict:
        result = {}
        for data in entrust_data:
            entrust_no = data.get("合同编号")  # type: str
            code = data.get("证券代码")
            broker_cn = data.get("交易市场")  # type: str
            price = data.get("委托价格")  # type: float
            volume = data.get("委托数量")  # type: float
            filled = data.get("成交数量")  # type: int
            status_cn = data.get("备注")  # type: str
            # date = data.get("委托日期")  # type: str 需要处理成时间
            t = data.get("委托时间")  # type: str
            name = data.get("证券名称")  # type: str
            average_price = data.get("成交均价")  # type: str
            suffix = ""
            side = 0  # 1-买入 2-卖出
            if broker_cn.startswith("深"):
                suffix = ".XSHE"
            elif broker_cn.startswith("上"):
                suffix = ".XSHG"
            status = cls.status_map.get(status_cn, 0)
            if status == 0:
                logger.info(f"status_cn:{status_cn}，未找到枚举项")

            security = code + suffix
            result[entrust_no] = {
                "security": security,
                "entrust_no": entrust_no,
                "name": name,
                "price": price,
                "volume": volume,
                "filled": filled,
                "side": side,
                "status": status,
                "time": t,
                "average_price": average_price
            }
        return result

    @classmethod
    def analysis_entrust_data(cls, entrust_no: str, entrust_data: list) -> Dict:
        # 解析委托订单数据，并找到指定的委托单号
        entrust_dict = cls.entrust_list_to_dict(entrust_data)
        return entrust_dict.get(entrust_no, {})

    @classmethod
    def timed_query_entrust(cls) -> int:
        """定时查询我的委托
        根据当前的订单列表数量动态控制等待时间
        """
        if cls.user is None:
            return 5
        if not cls.order_list:
            return 1
        # result = cls.user.today_entrusts()
        result = cls.analysis_entrust_data(cls.user.today_entrusts())
        print(result)
        print(f"查询我的委托：time:{int(time.time())}")
        # 查询之后，拿到结果，需要对当前的订单列表做遍历，如果数据有变化，需要做回调z_trader_server通知
        failed = []  # 保存了失败了的request_id列表，以便于服务器返还金额
        need_update_list = []  # 保存了需要更新的数据
        for order in cls.order_list.copy():  # type: LocalOrderData
            if not order.entrust_no:
                failed.append(order.request_id)
                continue
            for entrust in result:
                entrust_no = entrust["entrust_no"]
                status = entrust["status"]
                if order.entrust_no != entrust_no:
                    continue
                if status in (2, 3):
                    # 说明这两个单已经完成了
                    cls.order_list.remove(order)

                need_update_list.append(
                    {
                        "request_id": order.request_id,
                        "entrust_no": entrust_no,
                        "status": status,
                        "price": entrust["price"],
                        "volume": entrust["volume"],
                        "filled": entrust["filled"],
                        "side": entrust["side"],
                        "date": entrust["date"]
                    }
                )
        requests.post("http://192.168.100.9:8000/callback", json={
            "failed": failed,
            "need_update_list": need_update_list
        })
        return 20

    @classmethod
    def run_timed_query_entrust(cls):
        while True:
            timeout = cls.timed_query_entrust()
            time.sleep(timeout)

    @classmethod
    def run(cls):
        executor_action_thread = Thread(target=cls.run_timed_query_entrust, daemon=True)
        executor_action_thread.start()


def executor_action():
    """循环执行actions_queue队列中的任务
    """
    logger.info("executor_action started")
    while True:
        action = actions_queue.get()  # type: Action
        ret = action()
        print(ret)


def start_executor_action():
    executor_action_thread = Thread(target=executor_action, daemon=True)
    executor_action_thread.start()
