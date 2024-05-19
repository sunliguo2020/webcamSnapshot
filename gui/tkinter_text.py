# -*- coding: utf-8 -*-
"""
@author: sunliguo
@contact: QQ376440229
@Created on: 2024-05-18 13:36
"""
# -*- coding:utf-8 -*-
from tkinter import *

'''
NW  N   NE
W   C   E
SW  S   SE
'''


class textbox:
    def __init__(self):
        self.root = Tk()
        self.root.title("文本框")  # 设置窗口标题
        self.root.geometry("600x600")  # 设置窗口大小 注意：是x 不是*

        '''文本框样式'''
        # 设置文本框高度为1，宽度为2，height=2表示一行的高度，width=2表示宽度为两个字节
        self.height_width_label = Label(self.root, text='文本框高度和宽度：')
        self.height_width_text = Text(self.root, height=2, width=10)
        # 文本框插入数据
        self.insert_label = Label(self.root, text='文本框插入字符：')
        self.insert_text = Text(self.root, height=1, width=10)
        self.insert_text.insert('0.0', '1234567890')
        # 文本框删除数据
        self.del_label = Label(self.root, text='文本框删除字符：')
        self.del_text = Text(self.root, height=1, width=10)
        self.del_text.insert('0.0', '123456789')
        self.button_del = Button(self.root, text='<==', command=self.delete_text)
        # 文本框获取数据
        self.get_label = Label(self.root, text='文本框获取字符')
        self.get_text = Text(self.root, height=1, width=10)
        self.get_text.insert('0.0', '1234567890')
        self.button_get = Button(self.root, text='获取字符', command=self.text_get)
        # 文本框样式
        self.relief_label = Label(self.root, text='文本框样式：')
        self.flat_text = Text(self.root, height=1, width=10, relief=FLAT)
        self.flat_text.insert('0.0', '边框平坦')
        self.sunken_text = Text(self.root, height=1, width=10, relief=SUNKEN)
        self.sunken_text.insert('0.0', '边框凹陷')
        self.taised_text = Text(self.root, height=1, width=10, relief=RAISED)
        self.taised_text.insert('0.0', '边框凸起')
        self.groove_text = Text(self.root, height=1, width=10, relief=GROOVE)
        self.groove_text.insert('0.0', '边框压线')
        self.tidge_text = Text(self.root, height=1, width=10, relief=RIDGE)
        self.tidge_text.insert('0.0', '边框脊线')
        # 文本框边框大小，bd='边框大小'
        self.db_label = Label(self.root, text='边框大小：')
        self.db_text = Text(self.root, height=1, width=10, bd=5)
        # 文本框后颜色，bg='背景色'，fg='前景色'
        self.colour_label = Label(self.root, text='文本框颜色：')
        self.activebackground_text = Text(self.root, height=1, width=10, bg='blue')
        self.activeforeground_text = Text(self.root, height=1, width=10, fg='blue')
        # 文本框文字字体格式， font=('字体', 字号, 'bold/italic/underline/overstrike')
        self.font_Label = Label(self.root, text='显示边框样式：')
        self.font_text_1 = Text(self.root, height=1, width=20, font=('软体雅黑', 10, 'overstrike'))
        self.font_text_1.insert('0.0', '软体雅黑/10/重打印')
        self.font_text_2 = Text(self.root, height=1, width=20, font=('宋体', 10, 'italic'))
        self.font_text_2.insert('0.0', '宋体/10/斜体')
        self.font_text_3 = Text(self.root, height=1, width=20, font=('黑体', 10, 'bold'))
        self.font_text_3.insert('0.0', '黑体/10/加粗')
        self.font_text_4 = Text(self.root, height=1, width=20, font=('楷体', 10, 'underline'))
        self.font_text_4.insert('0.0', '楷体/10/下划线')
        # 文本框状态，禁用状态无法输入，正常状态可以输入
        self.state_Label = Label(self.root, text='文本框状态：')
        self.state_text_1 = Text(self.root, height=1, width=20)
        self.state_text_1.insert('0.0', '禁用状态')
        self.state_text_1.config(state=DISABLED)
        self.state_text_2 = Text(self.root, height=1, width=20)
        self.state_text_2.insert('0.0', '正常状态')
        self.state_text_2.config(state=NORMAL)
        # 文本框点击颜色，及颜色厚度。highlightcolor='颜色'，highlightthickness=厚度
        self.label_colour = Label(self.root, text='点击颜色/厚度：')
        self.highlightcolor = Text(self.root, height=1, width=10, highlightcolor='red', highlightthickness=1)
        # 文本框插入按钮
        self.button_text_label = Label(self.root, text='文本框插入按钮：')
        self.button_text = Text(self.root, height=5, width=20)
        self.button_text.insert('0.0', '文本框插入按钮')
        self.text_button = Button(self.button_text, text='按钮', command=self.print_text)
        self.button_text.window_create(INSERT, window=self.text_button)
        # 文本框插入图片
        self.image_text_label = Label(self.root, text='文本框插入图片：')
        self.image_text = Text(self.root, height=12, width=30)
        self.image_text.insert('0.0', '\n文本框插入图片')
        photo = PhotoImage(file="2.gif")
        self.image_text.image_create('1.0', image=photo)

        '''grid布局'''
        self.height_width_label.grid(row=0, column=0, sticky=E)
        self.height_width_text.grid(row=0, column=1, sticky=W)
        self.insert_label.grid(row=1, column=0, sticky=E)
        self.insert_text.grid(row=1, column=1, sticky=W)
        self.del_label.grid(row=2, column=0, sticky=E)
        self.del_text.grid(row=2, column=1, sticky=W)
        self.button_del.grid(row=2, column=2, sticky=W)
        self.get_label.grid(row=3, column=0, sticky=E)
        self.get_text.grid(row=3, column=1, sticky=W)
        self.button_get.grid(row=3, column=2, sticky=W)
        self.relief_label.grid(row=4, column=0, sticky=E)
        self.flat_text.grid(row=4, column=1, sticky=W)
        self.sunken_text.grid(row=4, column=2, sticky=W)
        self.taised_text.grid(row=4, column=3, sticky=W)
        self.groove_text.grid(row=4, column=4, sticky=W)
        self.tidge_text.grid(row=4, column=5, sticky=W)
        self.db_label.grid(row=5, column=0, sticky=E)
        self.db_text.grid(row=5, column=1, sticky=W)
        self.colour_label.grid(row=6, column=0, sticky=E)
        self.activebackground_text.grid(row=6, column=1, sticky=W)
        self.activeforeground_text.grid(row=6, column=2, sticky=W)
        self.font_Label.grid(row=7, column=0, rowspan=2, sticky=E)
        self.font_text_1.grid(row=7, column=1, columnspan=2, sticky=W)
        self.font_text_2.grid(row=7, column=3, columnspan=2, sticky=W)
        self.font_text_3.grid(row=8, column=1, columnspan=2, sticky=W)
        self.font_text_4.grid(row=8, column=3, columnspan=2, sticky=W)
        self.state_Label.grid(row=9, column=0, sticky=E)
        self.state_text_1.grid(row=9, column=1, columnspan=2, sticky=W)
        self.state_text_2.grid(row=9, column=3, columnspan=2, sticky=W)
        self.label_colour.grid(row=10, column=0, sticky=E)
        self.highlightcolor.grid(row=10, column=1, sticky=W)
        self.button_text_label.grid(row=11, column=0, sticky=E)
        self.button_text.grid(row=11, column=1, columnspan=2, sticky=W)
        self.image_text_label.grid(row=12, column=0, sticky=E)
        self.image_text.grid(row=12, column=1, columnspan=3, sticky=W)
        self.root.mainloop()

    def print_text(self):
        print(self.button_text.get('0.0', 'end'))

    def delete_text(self):
        self.del_text.delete('0.0', END)

    def text_get(self):
        print(self.get_text.get('0.0', END))


if __name__ == '__main__':
    textbox()