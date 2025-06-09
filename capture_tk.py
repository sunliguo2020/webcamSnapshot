# -*- coding: utf-8 -*-
"""
@author: sunliguo
@contact: QQ376440229
@Created on: 2023-05-19 18:13
摄像头批量截图的图形界面

pyinstaller -F -w -i cam_capture.ico capture_tk.py -n 摄像头批量截图

"""
import logging
import os.path
import queue
import threading
import time
import tkinter as tk
from tkinter import ttk, N, S, E, W, filedialog, END, DISABLED, NORMAL, Label
from tkinter.scrolledtext import ScrolledText

from PIL import ImageTk, Image

from lib.Camera import Camera
from utils.capture_pool import capture_pool, onvif_pool

logger = logging.getLogger('camera_logger')


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
        self.scrolled_text.grid(row=10, column=0, sticky=(N, S, W, E))
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
        logger.addHandler(self.queue_handler)

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


# 保存目录
save_dir = None


def clear_log():
    """清空日志区的函数"""
    console.scrolled_text.configure(state='normal')
    console.scrolled_text.delete("1.0", 'end')
    console.scrolled_text.configure(state='disabled')


def select_file():
    # 单个文件选择
    selected_file_path = filedialog.askopenfilename(
        filetypes=[('csv files', '*.csv'), ("All Files", "*.*")]  # 设置文件类型
    )  # 使用askopenfilename函数选择单个文件
    select_path.set(selected_file_path)


def select_files():
    # 多个文件选择
    selected_files_path = filedialog.askopenfilenames()  # askopenfilenames函数选择多个文件
    select_path.set('\n'.join(selected_files_path))  # 多个文件的路径用换行符隔开


def select_folder():
    """
    保存图片的文件夹选择
    @return:
    """
    selected_folder = filedialog.askdirectory()  # 使用askdirectory函数选择文件夹
    select_dir.set(selected_folder)


def callbackFunc(event):
    """
    设备类型选择后的回调函数
    @param event:
    @return:
    """
    # print(f"New Element Selected{event}")
    # print(numberChosen.current(), numberChosen.get())

    # 如果用户选择电脑，则下面的csv为不可选择状态
    if numberChosen.get() == '电脑':
        csv_entry['state'] = 'disable'
        csv_button['state'] = DISABLED
    else:
        csv_entry['state'] = NORMAL
        csv_button['state'] = NORMAL


def start_cap():
    """
    开始采集按钮绑定的函数
    :return:
    """
    global save_dir
    # 清空日志区
    clear_log()

    # 清空select_dir
    select_dir.set('')

    # 获取摄像头类型
    client_type = numberChosen.get()
    logger.debug(f"采集的摄像头类型为：{client_type}")

    # 获取是否添加水印
    watermark_flag = watermark_var.get()
    logger.debug(f"是否添加水印：{watermark_flag}")

    # 网络摄像头截图csv 文件的路径
    csv_file = csv_entry.get()

    # 判断csv_file的合法性，如果是电脑摄像头的话，不用考虑csv
    if client_type != '电脑' and (not os.path.isfile(csv_file) or os.path.splitext(csv_file)[-1] != ".csv"):
        logger.error(f'没有选择csv文件,请重新选择包含ip,password的文件!')
        raise ValueError('请重新选择包含ip,password的文件!')

    # 截图保存路径 或 保存截图的文件夹默认是 csv文件名 + 当前日期
    save_dir = os.path.join((dir_entry.get() or
                             os.path.splitext(os.path.basename(csv_file))[0]),
                            time.strftime('%Y-%m-%d', time.localtime()),
                            time.strftime('%Y-%m-%d_%H-%M-%S', time.localtime()))

    # 保存截图的文件夹默认是 csv文件名 + 当前日期,设置保存截图的文件夹的默认值
    select_dir.set(save_dir)
    # messagebox.showinfo("设置成功", f"保存目录已设置为：{save_dir}")

    #  判断路径是否存在，不存在则创建
    if os.path.exists(save_dir):
        os.makedirs(save_dir, exist_ok=True)

    # 生成打开该路径的按钮
    open_button.configure(command=lambda: open_folder(save_dir))

    logger.info(f'摄像头类型：{client_type}')
    logger.info(f'截图保存路径：{save_dir}')
    logger.info(f'是否添加水印：{"是" if watermark_flag else "否"}')

    # 如果是电脑摄像头，直接截图
    if client_type == '电脑':
        result = Camera(camera_type='computer').capture()
        if result[0] == 1:
            logger.debug(f"截图成功！图片路径为：{result[1]}")
            image_path = result[1]  # 获取截图文件的路径
            display_image(image_path)  # 显示捕获的图像
        else:
            logger.debug(f'电脑截图失败！')
        return

    # 其余为海康 大华的rtsp协议
    # onvif也是先获取rtsp地址，再截图

    if client_type == '海康':
        capture_pool(csv_file, camera_type="hik", is_water_mark=watermark_flag, folder_path=save_dir)

    elif client_type == '大华':
        capture_pool(csv_file, camera_type='dahua', is_water_mark=watermark_flag, folder_path=save_dir)

    elif client_type == 'onvif':
        # capture_pool(csv_file, camera_type='onvif', folder_path=save_dir)
        onvif_pool(csv_file, folder_path=save_dir)


def display_image(image_path):
    """
    # img = Image.open("a.jpg").resize((160, 90))  # 打开图片
    # photo = ImageTk.PhotoImage(img)  # 使用ImageTk的PhotoImage方法
    # # tk.Label(master=root,image=photo).grid(row=0, column=4)
    @param image_path:
    @return:
    """
    # 打开图像文件
    img = Image.open(image_path)

    # 将图像调整为合适的大小
    img = img.resize((100, 50))

    # 将 PIL 图像转换为 PhotoImage
    photo = ImageTk.PhotoImage(img)
    # global image_label, root
    # 创建 Label 组件以显示图像
    image_label = Label(root, image=photo)
    image_label.image = photo  # 保持对图片的引用，避免被垃圾回收
    image_label.grid(row=10, column=1, sticky=W, padx=20)


def open_folder(save_dir):
    """
    打开截图的文件夹
    Returns:

    """
    logger.debug(f'要打开截图保存路径：{save_dir}')
    try:
        os.startfile(save_dir)
    except Exception as e:
        logger.debug(f'打开截图保存路径失败：{e}')


root = tk.Tk()
# 标题
root.title('网络摄像头截图小工具')
# 定义窗口显示大小和显示位置
root.geometry('650x450+300+200')

frame1 = tk.Frame(root)
console = LogWidget(frame1)
frame1.grid(row=10, column=0, columnspan=5, padx=20)

# 初始化Entry控件的text variable属性值
select_path = tk.StringVar()
select_dir = tk.StringVar()
watermark_var = tk.BooleanVar(value=True)  # 添加水印复选框变量，默认选中

# 布局空间

# 截图的类型 电脑摄像头  海康  大华 onvif
# 创建一个下拉列表
tk.Label(root, text='摄像头类型:', font='微软雅黑 12').grid(column=0, row=0, sticky=tk.W, padx=20)
number = tk.StringVar()
numberChosen = ttk.Combobox(root, state='readonly', width=12, height=12, textvariable=number)
numberChosen['values'] = ('海康', '大华', 'onvif', '电脑')  # 设置下拉列表的值
numberChosen.grid(column=1, row=0, sticky=tk.W)  # 设置其在界面中出现的位置  column代表列   row 代表行
numberChosen.current(0)  # 设置下拉列表默认显示的值，0为 numberChosen['values'] 的下标

# 绑定改变值的回调函数
numberChosen.bind("<<ComboboxSelected>>", callbackFunc)

# 保存 ip地址和密码的csv文件
# 标签组件
csv_file_label = tk.Label(root, text='包含ip和密码的csv文件路径:', font='微软雅黑 12', fg='green')
csv_file_label.grid(column=0, row=1, sticky=tk.W, padx=20)
# 输入框
csv_entry = tk.Entry(root, textvariable=select_path)
csv_entry.grid(column=1, row=1, sticky=tk.W)

csv_button = tk.Button(root, text="浏览", command=select_file)
csv_button.grid(row=1, column=3)

# 截图保存目录 标签
cap_dir_label = tk.Label(root, text='截图保存位置\n(留空为当前目录):', font='微软雅黑 12')
cap_dir_label.grid(row=2, column=0, sticky=tk.W, padx=20)

# 截图保存目录
dir_entry = tk.Entry(root, textvariable=select_dir)
dir_entry.grid(column=1, row=2, sticky=tk.W)

# 截图保存路径浏览按钮
tk.Button(root, text="浏览", command=select_folder).grid(row=2, column=3)

# 添加水印复选框
watermark_check = tk.Checkbutton(root, text="添加水印", variable=watermark_var, font='微软雅黑 12')
watermark_check.grid(row=3, column=0, sticky=tk.W, padx=20)

# 采集按钮
capture_button = tk.Button(root,
                           text='开始截图',
                           font='宋体 12',
                           bg='lightblue',
                           width=20,
                           command=lambda: threading.Thread(target=start_cap).start())
capture_button.grid(row=8, columnspan=4, padx=10, pady=10)

# 打开截图目录
open_button = tk.Button(root, text='打开截图路径')
open_button.grid(row=8, column=2, sticky='ew')

# 清空日志按钮
clear_button = tk.Button(root, text='清空日志', command=clear_log)
clear_button.grid(row=8, column=3, sticky='ew')

if __name__ == '__main__':
    root.mainloop()
