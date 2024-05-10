# -*- coding: utf-8 -*-
"""
@author: sunliguo
@contact: QQ376440229
@Created on: 2024-05-10 18:52
"""
import logging


class WidgetLogger(logging.Handler):
    # The init function needs the widget which will hold the log messages passed to it as
    # well as other basic information (log level, format, etc.)

    def __init__(self, widget, logLevel, format):
        logging.Handler.__init__(self)

        # Basic logging configuration
        self.setLevel(logLevel)
        self.setFormatter(logging.Formatter(format))
        self.widget = widget

        # The ScrolledText box must be disabled so users can't enter their own text
        self.widget.config(state='disabled')

    # This function is called when a log message is to be handled
    def emit(self, record):
        # Enable the widget to allow new text to be inserted
        self.widget.config(state='normal')

        # Append log message to the widget
        # self.widget.insert('insert', str(self.format(record) + '\n'))

        msg = self.format(record)
        self.widget.insert("end", msg + "\n")

        # Scroll down to the bottom of the ScrolledText box to ensure the latest log message
        # is visible
        self.widget.see("end")

        # Re-disable the widget to prevent users from entering text
        self.widget.config(state='disabled')
