# -*- coding: utf-8 -*-
import logging
from collections import defaultdict
from typing import Dict, List

import pywinauto
import pywinauto.clipboard

from thstrader.common import grid_strategies
from thstrader.common import clienttrader
logger = logging.getLogger(__name__)


class UniversalClientTrader(clienttrader.BaseLoginClientTrader):
    grid_strategy = grid_strategies.Xls
    status_map = {
        "未成交": 1,
        "部分成交": 2,
        "全部成交": 3,
        "全部撤单": 4,
    }
    side_map = {
        "买入":1,
        "卖出":-1,
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

    def get_today_trades_and_entrusts(self):
        entrusts_data = self.entrust_list_to_dict(self.today_entrusts())
        print(entrusts_data)
        for entrust in entrusts_data:
            if entrusts_data[entrust].get("filled", 0) > 0:
                # 说明有成交记录，需要查成交
                trade_data = self.trader_list_to_dict(self.today_trades())
                break
        else:
            trade_data = {}
        # 将数据进行合并
        for entrust in entrusts_data:
            entrusts_data[entrust]["trader_orders"] = trade_data.get(entrust, [])
        return entrusts_data

    def entrust_list_to_dict(self, entrust_data: list) -> Dict:
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
            status = self.status_map.get(status_cn, 0)
            if status == 0:
                logger.info(f"status_cn:{status_cn}，未找到枚举项")

            code = self.conversion_security_to_code(security, broker_cn)

            result[entrust_no] = {
                "code": code,
                "entrust_no": entrust_no,
                "name": name,
                "price": price,
                "volume": volume,
                "filled": filled,
                "order_side": self.side_map.get(side_cn, 0),
                "status": status,
                "time": t,
                "average_price": average_price
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
                "time": trader.get("成交时间"),
            })
        return result
