# -*- coding: utf-8 -*-
"""
@author: sunliguo
@contact: QQ376440229
@Created on: 2026/1/16 15:12
"""
"""
日志工具类抽离 - 包含日志队列处理器、日志UI组件、GUI安全队列
"""
import logging
import queue
from tkinter import END, N, S,W,E
from tkinter.scrolledtext import ScrolledText


# 定义GUI操作队列（全局）
gui_queue = queue.Queue()
# 全局状态变量  全局截图状态标记
is_capturing = False


def poll_gui_queue(root):
    """
    GUI队列轮询，处理子线程的GUI操作请求（弹窗、图片显示等）
    需要在主线程中定期调用（通常通过 root.after()）
    @param root: tkinter 主窗口
    """
    from tkinter import messagebox
    from utils.other_utils import display_image

    while True:
        try:
            task, args = gui_queue.get(block=False)
            if task == "show_error":
                messagebox.showerror(*args)
            elif task == "show_info":
                messagebox.showinfo(*args)
            elif task == "show_warning":
                messagebox.showwarning(*args)
            elif task == "display_image":
                display_image(*args)
        except queue.Empty:
            break
    root.after(100, lambda: poll_gui_queue(root))


class QueueHandler(logging.Handler):
    """
    类将日志记录发送到队列
    Class to send logging records to a queue
    它可以在不同的线程中被使用
    It can be used from different threads
    ConsoleUi类轮询此队列以在ScrolledText小部件中显示记录
    The ConsoleUi class polls this queue to display records in a ScrolledText widget
    """

    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        """
        用于实际输出日志记录
        @param record:
        @return:
        """
        self.log_queue.put(record)


class LogWidget:
    """
    从日志记录队列轮询消息，并在滚动文本小部件中显示它们
    Poll messages from a logging queue and display them in a scrolled text widget
    """

    def __init__(self, frame):
        self.frame = frame
        # Create a ScrolledText wdiget
        self.scrolled_text = ScrolledText(frame, state='disabled', height=20)
        self.scrolled_text.pack(fill="both", expand=True)
        self.scrolled_text.configure(font=('宋体', '10'))
        self.scrolled_text.tag_config('INFO', foreground='black')
        self.scrolled_text.tag_config('DEBUG', foreground='gray')
        self.scrolled_text.tag_config('WARNING', foreground='orange')
        self.scrolled_text.tag_config('ERROR', foreground='red')
        self.scrolled_text.tag_config('CRITICAL', foreground='red', underline=True)

        # Create a logging handler using a queue
        # 创建一个使用队列的日志记录处理程序
        self.log_queue = queue.Queue()
        self.queue_handler = QueueHandler(self.log_queue)
        formatter = logging.Formatter("%(asctime)s-%(name)s-%(levelname)s-%(filename)-8s: %(lineno)s line-%(message)s",
                                      datefmt='%Y-%m-%d %H:%M:%S')
        self.queue_handler.setFormatter(formatter)
        self.logger = logging.getLogger('camera_logger')
        self.logger.addHandler(self.queue_handler)

        # Start polling messages from the queue
        self.frame.after(100, self.poll_log_queue)

    def display(self, record):
        msg = self.queue_handler.format(record)
        self.scrolled_text.configure(state='normal')
        self.scrolled_text.insert(END, msg + '\n', record.levelname)
        self.scrolled_text.configure(state='disabled')
        # Autoscroll to the bottom
        self.scrolled_text.yview(END)

    def poll_log_queue(self):
        # Check every 100ms if there is a new message in the queue to display
        while True:
            try:
                record = self.log_queue.get(block=False)
            except queue.Empty:
                break
            else:
                self.display(record)
        self.frame.after(100, self.poll_log_queue)

    def clear_log(self):
        """
        清空日志区+日志队列
        @return:
        """
        self.scrolled_text.configure(state="normal")
        self.scrolled_text.delete("1.0", 'end')
        self.scrolled_text.configure(state="disabled")
        # 清空日志队列
        while not self.log_queue.empty():
            try:
                self.log_queue.get(block=False)
            except queue.Empty:
                break
