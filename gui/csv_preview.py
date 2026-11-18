"""CSV file preview dialog."""

import csv
import os
import tkinter as tk
from tkinter import ttk

from utils.log_utils import gui_queue

COLOR_BG = "#F0F0F0"
COLOR_FRAME_BG = "#FFFFFF"
COLOR_BUTTON = "#4A90D9"
COLOR_BUTTON_TEXT = "white"
FONT_BUTTON = ("微软雅黑", 10)


def show_csv_preview(parent, csv_path):
    """Read a CSV file and show its contents in a scrollable table."""
    if not csv_path:
        gui_queue.put(("show_warning", ("提示", "请先选择 CSV 文件")))
        return

    if not csv_path.lower().endswith(".csv"):
        gui_queue.put(("show_warning", ("提示", "请选择 CSV 格式的文件")))
        return

    try:
        with open(csv_path, "r", encoding="utf-8-sig") as file:
            rows = list(csv.reader(file))

        if not rows:
            gui_queue.put(("show_warning", ("提示", "CSV 文件为空")))
            return

        headers = rows[0]
        data_rows = rows[1:]
        preview_win = tk.Toplevel(parent)
        preview_win.title(f"CSV 预览 - {os.path.basename(csv_path)}")
        preview_win.geometry("600x400+350+250")
        preview_win.configure(bg=COLOR_BG)
        preview_win.resizable(True, True)

        info_frame = tk.Frame(preview_win, bg=COLOR_BG)
        info_frame.pack(fill="x", padx=10, pady=(10, 5))
        tk.Label(
            info_frame,
            text=f"文件: {csv_path}",
            font=("微软雅黑", 9),
            bg=COLOR_BG,
            fg="#555555",
            anchor="w",
        ).pack(fill="x")
        tk.Label(
            info_frame,
            text=f"共 {len(data_rows)} 条记录，{len(headers)} 列",
            font=("微软雅黑", 9, "bold"),
            bg=COLOR_BG,
            fg="#333333",
            anchor="w",
        ).pack(fill="x")

        tree_frame = tk.Frame(preview_win, bg=COLOR_FRAME_BG)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=5)

        canvas = tk.Canvas(tree_frame, bg="white", highlightthickness=0)
        v_scrollbar = ttk.Scrollbar(
            tree_frame, orient="vertical", command=canvas.yview
        )
        h_scrollbar = ttk.Scrollbar(
            tree_frame, orient="horizontal", command=canvas.xview
        )
        canvas.configure(
            yscrollcommand=v_scrollbar.set,
            xscrollcommand=h_scrollbar.set,
        )
        v_scrollbar.pack(side="right", fill="y")
        h_scrollbar.pack(side="bottom", fill="x")
        canvas.pack(side="left", fill="both", expand=True)

        col_widths = [45]
        for column_index, column_name in enumerate(headers):
            max_length = len(column_name)
            for row in data_rows:
                if column_index < len(row):
                    cell_length = sum(
                        2 if ord(char) > 127 else 1 for char in row[column_index]
                    )
                    max_length = max(max_length, cell_length)
            col_widths.append(max(70, max_length * 7 + 24))

        total_width = sum(col_widths)
        row_height = 26
        canvas_width = total_width + 4
        canvas_height = (len(data_rows) + 1) * row_height + 4
        canvas.config(scrollregion=(0, 0, canvas_width, canvas_height))

        x = 2
        y = 2
        for column_name, column_width in zip(
            ["序号"] + headers, col_widths
        ):
            canvas.create_rectangle(
                x, y, x + column_width, y + row_height,
                outline="#999999", fill="#E8E8E8",
            )
            canvas.create_text(
                x + column_width // 2, y + row_height // 2,
                text=column_name, font=("微软雅黑", 9, "bold"),
                anchor="center",
            )
            x += column_width

        y += row_height
        for row_index, row in enumerate(data_rows):
            x = 2
            padded_row = row + [""] * (len(headers) - len(row))
            values = [str(row_index + 1)] + padded_row[:len(headers)]
            for value, column_width in zip(values, col_widths):
                canvas.create_rectangle(
                    x + 1, y + 1, x + column_width - 1, y + row_height - 1,
                    outline="#CCCCCC", fill="white",
                )
                canvas.create_text(
                    x + column_width // 2, y + row_height // 2,
                    text=value, font=("微软雅黑", 9), anchor="center",
                )
                x += column_width
            y += row_height

        button_frame = tk.Frame(preview_win, bg=COLOR_BG)
        button_frame.pack(fill="x", padx=10, pady=10)
        tk.Button(
            button_frame,
            text="关闭",
            font=FONT_BUTTON,
            bg=COLOR_BUTTON,
            fg=COLOR_BUTTON_TEXT,
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=20,
            pady=5,
            command=preview_win.destroy,
        ).pack(side="right")

    except UnicodeDecodeError:
        gui_queue.put(
            ("show_error", ("错误", "CSV 文件编码错误，请使用 UTF-8 编码"))
        )
    except Exception as error:
        gui_queue.put(
            ("show_error", ("错误", f"读取 CSV 文件失败: {error}"))
        )
