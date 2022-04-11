# -*- coding: utf-8 -*-
# @Author   : xiaohuzi
# @Time     : 2022-01-25 15:31
import logging
from tkinter import HORIZONTAL
import threading
import tkinter as tk
import time
import datetime


class Application(tk.Frame):
    text_pady = 2
    text_padx = 10
    button_ipady = 10

    def __init__(self, master=None):
        tk.Frame.__init__(self, master)

        self.text = tk.Text(self, wrap="none")
        self.scrolly = tk.Scrollbar(self)
        self.scrollx = tk.Scrollbar(self, orient=HORIZONTAL)
        self.scrolly.grid(
            row=0, column=1, sticky=tk.N + tk.S + tk.E, padx=1, pady=self.text_pady
        )
        self.scrollx.grid(
            row=1,
            column=0,
            sticky=tk.N + tk.S + tk.E + tk.W,
            padx=self.text_padx,
            pady=1,
            columnspan=2,
        )

        self.text.grid(
            row=0,
            column=0,
            sticky=tk.N + tk.S + tk.E + tk.W,
            padx=self.text_padx,
            pady=self.text_pady,
            ipadx=2,
            ipady=2,
            columnspan=2,
        )
        self.text.config(yscrollcommand=self.scrolly.set)
        self.text.config(xscrollcommand=self.scrollx.set)
        self.scrolly.config(command=self.text.yview)
        self.scrollx.config(command=self.text.xview)
        self.quit_button = tk.Button(self, text="退出", command=self.quit)
        self.clear_button = tk.Button(self, text="清空日志", command=self.clear)

        self.clear_button.grid(
            row=2, column=0, sticky=tk.E + tk.W, ipady=self.button_ipady
        )

        self.quit_button.grid(
            row=2, column=1, sticky=tk.E + tk.W, ipady=self.button_ipady
        )  # 6
        self.grid(sticky=tk.N + tk.S + tk.E + tk.W)
        self.createWidgets()
        self.master.title("EasyTrader Server")
        self.master.geometry("800x700+500+200")
        # threading.Thread(target=self.cron, daemon=True).start()

    def cron(self):

        while True:
            self.master.title(
                f'EasyTrader Server\t{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
            )
            time.sleep(1)

    def createWidgets(self):
        top = self.winfo_toplevel()  # 1
        top.rowconfigure(0, weight=3)  # 2
        top.columnconfigure(0, weight=3)  # 3
        self.rowconfigure(0, weight=3)  # 4
        self.columnconfigure(0, weight=3)  # 5

    def clear(self):
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.configure(state="disabled")

    def push_log(self):
        while True:
            self.write_log("cccc")
            time.sleep(0.5)

    def write_log(self, content):
        self.text.configure(state="normal")
        rate = self.scrolly.get()[-1]
        if rate > 0.91:
            self.text.see("end")
        self.text.insert("end", str(content) + "\n")
        self.text.configure(state="disabled")


gui_app = Application()  # 8


class MyLogHandler(logging.Handler, object):
    """
    自定义日志handler 输出到gui
    """

    def __init__(self, name=None, other_attr=None, **kwargs):
        logging.Handler.__init__(self)

    def emit(self, record):
        """
        emit函数为自定义handler类时必重写的函数，这里可以根据需要对日志消息做一些处理，比如发送日志到服务器

        发出记录(Emit a record)
        """
        try:
            msg = self.format(record)
            gui_app.write_log(msg)
        except Exception:
            self.handleError(record)
