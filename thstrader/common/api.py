# -*- coding: utf-8 -*-
import logging
import sys

from thstrader.config import logger

if sys.version_info <= (3, 5):
    raise TypeError("不支持 Python3.5 及以下版本，请升级")


def use(broker, debug=False, **kwargs):
    """用于生成特定的券商对象
    :param broker:券商名支持 ['yh_client', '银河客户端'] ['ht_client', '华泰客户端']
    :param debug: 控制 debug 日志的显示, 默认为 True
    :return the class of trader
    """
    if debug:
        logger.setLevel(logging.DEBUG)

    if broker.lower() in ["universal_client", "通用同花顺客户端"]:
        from thstrader.common.universal_clienttrader import UniversalClientTrader

        return UniversalClientTrader()

    if broker.lower() in ["ths", "同花顺客户端"]:
        from thstrader.common.clienttrader import ClientTrader

        return ClientTrader()

    raise NotImplementedError
