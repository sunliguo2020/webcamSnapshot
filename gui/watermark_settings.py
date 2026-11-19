"""Watermark style editor dialog."""

import tkinter as tk
from tkinter import colorchooser, messagebox, ttk

from utils.watermark import (
    FONT_OPTIONS,
    POSITION_OPTIONS,
    normalize_watermark_style,
    save_watermark_style,
)

WATERMARK_TEXT_PRESETS = {
    "文件名": "{filename}",
    "IP 地址": "IP: {ip}",
    "时间": "时间: {time}",
    "摄像头类型": "类型: {camera_type}",
    "摄像头序号": "序号: {camera_index}",
    "设备型号": "型号: {model}",
    "MAC 地址": "MAC: {mac}",
    "序列号": "序列号: {serial_number}",
}


def edit_watermark_style(parent, style):
    """Show the modal style editor and return the saved style, if any."""
    dialog = tk.Toplevel(parent)
    dialog.title("水印样式设置")
    dialog.geometry("480x700")
    dialog.minsize(460, 620)
    dialog.resizable(True, True)
    dialog.transient(parent)
    dialog.update_idletasks()
    dialog_x = parent.winfo_rootx() + (
        parent.winfo_width() - dialog.winfo_width()
    ) // 2
    dialog_y = parent.winfo_rooty() + (
        parent.winfo_height() - dialog.winfo_height()
    ) // 2
    dialog_x = min(
        max(0, dialog_x),
        max(0, dialog.winfo_screenwidth() - dialog.winfo_width()),
    )
    dialog_y = min(
        max(0, dialog_y),
        max(0, dialog.winfo_screenheight() - dialog.winfo_height()),
    )
    dialog.geometry(f"+{dialog_x}+{dialog_y}")
    dialog.grab_set()

    font_var = tk.StringVar(
        dialog,
        value=next(
            label for label, font in FONT_OPTIONS.items()
            if font == style["font"]
        ),
    )
    scale_var = tk.StringVar(dialog, value=str(style["font_scale"]))
    position_var = tk.StringVar(
        dialog,
        value=next(
            label for label, position in POSITION_OPTIONS.items()
            if position == style["position"]
        ),
    )
    margin_var = tk.StringVar(dialog, value=str(style["margin"]))
    color_var = tk.StringVar(dialog, value=style["color"])
    outline_var = tk.StringVar(dialog, value=style["outline_color"])

    form = tk.Frame(dialog, padx=16, pady=12)
    form.pack(fill="both", expand=True)
    for column in range(3):
        form.grid_columnconfigure(column, weight=1)
    tk.Label(
        form,
        text=(
            "水印文字（每行一项；支持 {filename}、{ip}、{time}、"
            "{camera_type}、{camera_index}、{model}、{mac}、"
            "{serial_number}、{serial}）"
        ),
        wraplength=440,
    ).grid(
        row=0, column=0, columnspan=3, sticky="w", pady=(0, 4)
    )
    preset_var = tk.StringVar(dialog, value=next(iter(WATERMARK_TEXT_PRESETS)))
    ttk.Combobox(
        form,
        textvariable=preset_var,
        values=list(WATERMARK_TEXT_PRESETS),
        state="readonly",
        width=16,
    ).grid(row=1, column=0, sticky="w", pady=(0, 6))
    rows_container = tk.Frame(form)
    rows_container.grid(
        row=2, column=0, columnspan=3, sticky="nsew", pady=(0, 10)
    )
    rows_canvas = tk.Canvas(
        rows_container, height=120, highlightthickness=0
    )
    rows_scrollbar = ttk.Scrollbar(
        rows_container, orient="vertical", command=rows_canvas.yview
    )
    rows_canvas.configure(yscrollcommand=rows_scrollbar.set)
    rows_canvas.pack(side="left", fill="both", expand=True)
    rows_scrollbar.pack(side="right", fill="y")
    rows_frame = tk.Frame(rows_canvas)
    rows_window = rows_canvas.create_window(
        (0, 0), window=rows_frame, anchor="nw"
    )
    rows_frame.bind(
        "<Configure>",
        lambda _event: rows_canvas.configure(
            scrollregion=rows_canvas.bbox("all")
        ),
    )
    rows_canvas.bind(
        "<Configure>",
        lambda event: rows_canvas.itemconfigure(
            rows_window, width=event.width
        ),
    )
    form.grid_rowconfigure(2, weight=1)
    row_vars = []

    def render_text_rows():
        for child in rows_frame.winfo_children():
            child.destroy()
        for row, variable in enumerate(row_vars):
            ttk.Entry(rows_frame, textvariable=variable).grid(
                row=row, column=0, sticky="ew", pady=2
            )
            tk.Button(
                rows_frame,
                text="x",
                width=3,
                relief="flat",
                command=lambda row_var=variable: remove_text_row(row_var),
            ).grid(row=row, column=1, sticky="e", padx=(4, 0), pady=2)
        rows_frame.grid_columnconfigure(0, weight=1)
        rows_canvas.configure(scrollregion=rows_canvas.bbox("all"))

    def add_text_row(text):
        variable = tk.StringVar(dialog, value=text)
        variable.trace_add("write", draw_preview)
        row_vars.append(variable)
        render_text_rows()
        rows_canvas.yview_moveto(1)

    def remove_text_row(variable):
        row_vars.remove(variable)
        render_text_rows()
        draw_preview()

    def add_preset_row():
        add_text_row(WATERMARK_TEXT_PRESETS[preset_var.get()])

    tk.Button(
        form, text="添加数据行", command=add_preset_row
    ).grid(row=1, column=1, sticky="w", padx=(8, 0), pady=(0, 6))

    tk.Label(form, text="字体").grid(row=3, column=0, sticky="w")
    tk.Label(form, text="字号比例").grid(row=3, column=1, sticky="w")
    tk.Label(form, text="位置").grid(row=3, column=2, sticky="w")
    ttk.Combobox(
        form, textvariable=font_var, values=list(FONT_OPTIONS),
        state="readonly", width=14
    ).grid(row=4, column=0, sticky="ew", padx=(0, 8), pady=(2, 10))
    tk.Spinbox(
        form, textvariable=scale_var, from_=0.1, to=5, increment=0.1,
        width=12
    ).grid(row=4, column=1, sticky="ew", padx=(0, 8), pady=(2, 10))
    ttk.Combobox(
        form, textvariable=position_var, values=list(POSITION_OPTIONS),
        state="readonly", width=14
    ).grid(row=4, column=2, sticky="ew", pady=(2, 10))

    tk.Label(form, text="边距（画面宽度百分比）").grid(
        row=5, column=0, sticky="w"
    )
    tk.Label(form, text="文字颜色").grid(row=5, column=1, sticky="w")
    tk.Label(form, text="描边颜色").grid(row=5, column=2, sticky="w")
    tk.Spinbox(
        form, textvariable=margin_var, from_=0, to=20, increment=1,
        width=12
    ).grid(row=6, column=0, sticky="w", pady=(2, 10))

    def choose_color(variable):
        selected = colorchooser.askcolor(
            color=variable.get(), parent=dialog
        )[1]
        if selected:
            variable.set(selected.upper())

    tk.Button(
        form, textvariable=color_var,
        command=lambda: choose_color(color_var), width=12
    ).grid(row=6, column=1, sticky="w", pady=(2, 10))
    tk.Button(
        form, textvariable=outline_var,
        command=lambda: choose_color(outline_var), width=12
    ).grid(row=6, column=2, sticky="w", pady=(2, 10))

    tk.Label(form, text="预览").grid(
        row=7, column=0, columnspan=3, sticky="w"
    )
    preview = tk.Canvas(
        form, width=400, height=115, bg="#39465B",
        highlightthickness=0
    )
    preview.grid(row=8, column=0, columnspan=3, sticky="ew", pady=(4, 12))
    sample_values = {
        "filename": "192.168.1.100_dahua_20261118120000.jpg",
        "ip": "192.168.1.100",
        "time": "2026-11-18 12:00:00",
        "camera_type": "dahua",
        "camera_index": "0",
        "model": "DH-IPC-HFW1230S",
        "mac": "00:11:22:33:44:55",
        "serial_number": "ABC123456789",
        "serial": "ABC123456789",
    }

    def get_dialog_style():
        return normalize_watermark_style({
            "text": "\n".join(variable.get() for variable in row_vars),
            "font": FONT_OPTIONS[font_var.get()],
            "font_scale": float(scale_var.get()),
            "color": color_var.get(),
            "outline_color": outline_var.get(),
            "position": POSITION_OPTIONS[position_var.get()],
            "margin": int(margin_var.get()),
        })

    def draw_preview(*_):
        preview.delete("all")
        try:
            preview_style = get_dialog_style()
            sample_text = preview_style["text"].format_map(sample_values)
        except (KeyError, ValueError, TypeError):
            preview.create_text(
                max(1, preview.winfo_width()) // 2,
                max(1, preview.winfo_height()) // 2,
                text="水印文字或样式设置无效",
                fill="#FF8080", font=("微软雅黑", 10)
            )
            return

        if not sample_text:
            preview.create_text(
                max(1, preview.winfo_width()) // 2,
                max(1, preview.winfo_height()) // 2,
                text="（空水印）",
                fill="#FFFFFF", font=("微软雅黑", 10)
            )
            return

        width = max(1, preview.winfo_width())
        height = max(115, preview.winfo_height())
        margin = round(width * preview_style["margin"] / 100)
        vertical, horizontal = preview_style["position"].split("_")
        x = (
            margin if horizontal == "left"
            else width // 2 if horizontal == "center"
            else width - margin
        )
        y = (
            margin if vertical == "top"
            else height // 2 if vertical == "middle"
            else height - margin
        )
        anchor = {
            ("top", "left"): "nw",
            ("top", "center"): "n",
            ("top", "right"): "ne",
            ("middle", "left"): "w",
            ("middle", "center"): "center",
            ("middle", "right"): "e",
            ("bottom", "left"): "sw",
            ("bottom", "center"): "s",
            ("bottom", "right"): "se",
        }[(vertical, horizontal)]

        font_size = max(8, round(12 * preview_style["font_scale"]))
        text_options = {
            "text": sample_text,
            "anchor": anchor,
            "justify": horizontal,
            "font": ("Arial", font_size),
        }
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            preview.create_text(
                x + dx, y + dy,
                fill=preview_style["outline_color"],
                **text_options,
            )
        preview.create_text(
            x, y, fill=preview_style["color"], **text_options
        )

    for line in style["text"].split("\n"):
        add_text_row(line)

    for variable in (
        font_var, scale_var, position_var, margin_var, color_var,
        outline_var,
    ):
        variable.trace_add("write", draw_preview)

    preview.bind("<Configure>", draw_preview)
    draw_preview()

    result = {"style": None}
    buttons = tk.Frame(form)
    buttons.grid(row=9, column=0, columnspan=3, sticky="e")
    tk.Button(
        buttons, text="取消", command=dialog.destroy, width=10
    ).pack(side="right", padx=(8, 0))

    def save_style():
        try:
            new_style = get_dialog_style()
            try:
                new_style["text"].format_map(sample_values)
            except (KeyError, ValueError) as error:
                raise ValueError(f"水印文字模板无效：{error}") from error
            result["style"] = save_watermark_style(new_style)
        except (OSError, ValueError, TypeError) as error:
            messagebox.showerror("水印设置失败", str(error), parent=dialog)
            return
        dialog.destroy()

    tk.Button(
        buttons, text="保存", command=save_style, width=10
    ).pack(side="right")

    parent.wait_window(dialog)
    return result["style"]
