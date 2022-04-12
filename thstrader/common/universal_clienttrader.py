# -*- coding: utf-8 -*-
import datetime
import enum
import logging
from collections import defaultdict
from typing import Dict, List

import cfg4py
import pywinauto
import pywinauto.clipboard

from thstrader.common import grid_strategies
from thstrader.common import clienttrader
from thstrader.config import Config

cfg: Config = cfg4py.get_instance()

logger = logging.getLogger(__name__)


class OrderStatus(enum.IntEnum):
    ERROR = -1
    NO_DEAL = 1  # 未成交
    PARTIAL_TRANSACTION = 2  # #部分成交
    ALL_TRANSACTIONS = 3  # 全部成交
    CANCEL_ALL_ORDERS = 4  # 全部撤单

    @classmethod
    def get_status(cls, status_cn):
        status_map = {
            "未成交": cls.NO_DEAL.value,
            "部分成交": cls.PARTIAL_TRANSACTION.value,
            "全部成交": cls.ALL_TRANSACTIONS.value,
            "全部撤单": cls.CANCEL_ALL_ORDERS.value,
            "异常": cls.ERROR.value
        }

        return status_map.get(status_cn, cls.ERROR.value)


class UniversalClientTrader(clienttrader.BaseLoginClientTrader):
    grid_strategy = grid_strategies.Xls
    status_map = {
        "未成交": 1,
        "部分成交": 2,
        "全部成交": 3,
        "全部撤单": 4,
    }
    side_map = {
        "买入": 1,
        "卖出": -1,
    }

    @property
    def broker_type(self):
        return "universal"

    def login(self, user, password, exe_path, comm_password=None, **kwargs):
        """
        :param user: 用户名
        :param password: 密码
        :param exe_path: 客户端路径, 类似
        :param comm_password:
        :param kwargs:
        :return:
        """
        self._editor_need_type_keys = False

        try:
            self._app = pywinauto.Application().connect(
                path=self._run_exe_path(exe_path), timeout=1
            )
        # pylint: disable=broad-except
        except Exception:
            self._app = pywinauto.Application().start(exe_path)

            # wait login window ready
            while True:
                try:
                    login_window = pywinauto.findwindows.find_window(
                        class_name="#32770", found_index=1
                    )
                    break
                except:
                    self.wait(1)

            self.wait(1)
            self._app.window(handle=login_window).Edit1.set_focus()
            self._app.window(handle=login_window).Edit1.type_keys(user)

            self._app.window(handle=login_window).button7.click()

            # detect login is success or not
            # self._app.top_window().wait_not("exists", 100)
            self.wait(5)

            self._app = pywinauto.Application().connect(
                path=self._run_exe_path(exe_path), timeout=10
            )

        self._close_prompt_windows()
        self._main = self._app.window(title="网上股票交易系统5.0")

    @classmethod
    def conversion_security_to_code(cls, security, broker_cn):
        """将证券6位转换成带交易所的代码"""
        suffix = ""
        if broker_cn.startswith("深"):
            suffix = ".XSHE"
        elif broker_cn.startswith("上"):
            suffix = ".XSHG"
        return security + suffix

    def get_today_entrusts(self):
        entrusts_data = self.entrust_list_to_dict(self.today_entrusts())

        return entrusts_data

    @staticmethod
    def get_trade_fees(filled, price, order_side, code):
        if not hasattr(cfg, "commission"):
            cfg.commission = 3
            logger.error("commission not set, default 3")
        if not hasattr(cfg, "transfer_fee"):
            cfg.transfer_fee = 10
            logger.error("transfer_fee not set, default 10")
            logger.error("stamp_duty not set, default 10")
        if not hasattr(cfg, "min_limit"):
            cfg.min_limit = 5
            logger.error("min_limit not set, default 5")
        total_value = filled * price
        trade_fees = total_value * cfg.commission * 0.0001
        if trade_fees < cfg.min_limit:
            trade_fees = cfg.min_limit
        if code.startswith("6"):
            trade_fees += total_value * cfg.transfer_fee * 0.0001
        if order_side == -1:
            # 只有卖出有印花税
            if not hasattr(cfg, "stamp_duty"):
                cfg.stamp_duty = 10
            trade_fees += total_value * cfg.stamp_duty * 0.0001
        return trade_fees

    def entrust_list_to_dict(self, entrust_data: list) -> Dict:
        """将委托合同号转换成字典，并且计算手续费"""
        today = datetime.datetime.now().date().strftime("%Y-%m-%d")
        result = {}
        for data in entrust_data:
            entrust_no = data.get("合同编号")  # type: str
            security = data.get("证券代码")
            broker_cn = data.get("交易市场")  # type: str
            side_cn = data.get("操作")  # type: str
            price = data.get("委托价格")  # type: float
            volume = data.get("委托数量")  # type: float
            filled = data.get("成交数量")  # type: int
            status_cn = data.get("备注")  # type: str
            # date = data.get("委托日期")  # type: str 需要处理成时间
            t = data.get("委托时间")  # type: str
            name = data.get("证券名称")  # type: str
            average_price = data.get("成交均价")  # type: str
            status = OrderStatus.get_status(status_cn)
            if status == 0:
                logger.info(f"status_cn:{status_cn}，未找到枚举项")
            code = self.conversion_security_to_code(security, broker_cn)
            order_side = self.side_map.get(side_cn, 0)
            trade_fees = self.get_trade_fees(filled, price, order_side, code)
            result[entrust_no] = {
                "code": code,
                "entrust_no": entrust_no,
                "name": name,
                "price": price,
                "volume": volume,
                "filled": filled,
                "order_side": order_side,
                "status": status,
                "time": f'{today} {t}',
                "average_price": average_price,
                "trade_fees": trade_fees,
            }
        return result

    def trader_list_to_dict(self, trader_data: list) -> Dict:
        """将成交数据进行映射
        [{'买卖标志': '买入',
          '交易市场': '深A',
          '委托序号': '12345',
          '成交价格': 0.626,
          '成交数量': 100,
          '成交日期': '20170313',
          '成交时间': '09:50:30',
          '成交金额': 62.60,
          '股东代码': 'xxx',
          '证券代码': '162411',
          '证券名称': '华宝油气'}]
        """
        today = datetime.datetime.now().date().strftime("%Y-%m-%d")

        result = defaultdict(list)
        for trader in trader_data:
            entrust_no = trader.get("合同编号")  # 委托合同号

            result[entrust_no].append({
                "volume": trader.get("成交数量"),
                "average_price": trader.get("成交均价"),
                "value": trader.get("成交金额"),
                "price": trader.get("成交均价"),
                "order_side": self.side_map.get(trader.get("操作"), 0),
                "eid": trader.get("成交编号"),
                "time": f'{today} {trader.get("成交时间")}',
            })
        return result

    @staticmethod
    def balance_to_dict(balance):

        return {
            "available": balance.get("可用金额"),

        }

    def position_to_list(self, positions):
        """
        {
            "Unnamed: 14": "",
            "交易市场": "深圳Ａ股",
            "冻结数量": 0,
            "可用余额": 1500,
            "市价": 14.48,
            "市值": 21720.0,
            "当日买入": 0,
            "当日卖出": 200,
            "成本价": 14.548,
            "明细": "",
            "盈亏": -102.18,
            "盈亏比例(%)": -0.47,
            "股票余额": 1500,
            "证券代码": "000001",
            "证券名称": "平安银行"
        },
        """
        result = []
        for position in positions:
            security = position.get("证券代码")
            broker_cn = position.get("交易市场")  # type: str
            result.append(
                {
                    "code": self.conversion_security_to_code(security, broker_cn),
                    "name": "平安银行",
                    "shares": position.get("股票余额"),  # 总股数
                    "sellable": position.get("可用余额"),  # 可用股票数
                    "price": position.get("成本价"),  # 成本均价
                    "market_value": position.get("市值")  # 持仓市值
                }
            )
        return result
