"""Watermark style editor dialog."""

import tkinter as tk
from tkinter import colorchooser, messagebox, ttk

from utils.watermark import (
    FONT_OPTIONS,
    POSITION_OPTIONS,
    normalize_watermark_style,
    save_watermark_style,
)


def edit_watermark_style(parent, style):
    """Show the modal style editor and return the saved style, if any."""
    dialog = tk.Toplevel(parent)
    dialog.title("水印样式设置")
    dialog.geometry("700x480")
    dialog.minsize(680, 460)
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
            "水印文字（支持 {filename}、{ip}、{time}、{model}、"
            "{mac}、{serial_number}、{serial}；按回车换行）"
        ),
    ).grid(
        row=0, column=0, columnspan=3, sticky="w", pady=(0, 4)
    )
    text_input = tk.Text(form, width=74, height=3, wrap="word")
    text_input.insert("1.0", style["text"])
    text_input.grid(
        row=1, column=0, columnspan=3, sticky="ew", pady=(0, 10)
    )

    tk.Label(form, text="字体").grid(row=2, column=0, sticky="w")
    tk.Label(form, text="字号比例").grid(row=2, column=1, sticky="w")
    tk.Label(form, text="位置").grid(row=2, column=2, sticky="w")
    ttk.Combobox(
        form, textvariable=font_var, values=list(FONT_OPTIONS),
        state="readonly", width=14
    ).grid(row=3, column=0, sticky="ew", padx=(0, 8), pady=(2, 10))
    tk.Spinbox(
        form, textvariable=scale_var, from_=0.1, to=5, increment=0.1,
        width=12
    ).grid(row=3, column=1, sticky="ew", padx=(0, 8), pady=(2, 10))
    ttk.Combobox(
        form, textvariable=position_var, values=list(POSITION_OPTIONS),
        state="readonly", width=14
    ).grid(row=3, column=2, sticky="ew", pady=(2, 10))

    tk.Label(form, text="边距（画面宽度百分比）").grid(
        row=4, column=0, sticky="w"
    )
    tk.Label(form, text="文字颜色").grid(row=4, column=1, sticky="w")
    tk.Label(form, text="描边颜色").grid(row=4, column=2, sticky="w")
    tk.Spinbox(
        form, textvariable=margin_var, from_=0, to=20, increment=1,
        width=12
    ).grid(row=5, column=0, sticky="w", pady=(2, 10))

    def choose_color(variable):
        selected = colorchooser.askcolor(
            color=variable.get(), parent=dialog
        )[1]
        if selected:
            variable.set(selected.upper())

    tk.Button(
        form, textvariable=color_var,
        command=lambda: choose_color(color_var), width=12
    ).grid(row=5, column=1, sticky="w", pady=(2, 10))
    tk.Button(
        form, textvariable=outline_var,
        command=lambda: choose_color(outline_var), width=12
    ).grid(row=5, column=2, sticky="w", pady=(2, 10))

    tk.Label(form, text="预览").grid(
        row=6, column=0, columnspan=3, sticky="w"
    )
    preview = tk.Canvas(
        form, width=640, height=115, bg="#39465B",
        highlightthickness=0
    )
    preview.grid(row=7, column=0, columnspan=3, sticky="ew", pady=(4, 12))
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
            "text": text_input.get("1.0", "end-1c"),
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

        width = max(640, preview.winfo_width())
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

    for variable in (
        font_var, scale_var, position_var, margin_var, color_var,
        outline_var,
    ):
        variable.trace_add("write", draw_preview)

    def on_text_modified(event):
        event.widget.edit_modified(False)
        draw_preview()

    text_input.bind("<<Modified>>", on_text_modified)
    preview.bind("<Configure>", draw_preview)
    draw_preview()

    result = {"style": None}
    buttons = tk.Frame(form)
    buttons.grid(row=8, column=0, columnspan=3, sticky="e")
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
