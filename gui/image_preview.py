"""Image preview dialog."""

import logging
import os
import tkinter as tk

from PIL import Image, ImageTk

logger = logging.getLogger("camera_logger")

COLOR_BG = "#F0F0F0"
COLOR_BUTTON = "#4A90D9"
COLOR_BUTTON_TEXT = "white"
COLOR_FRAME_BG = "#FFFFFF"
FONT_BUTTON = ("微软雅黑", 10)


def show_preview_image(parent, image_path):
    """Display a screenshot in a new window."""
    try:
        img = Image.open(image_path)
        win_width = min(img.width + 40, 800)
        win_height = min(img.height + 80, 600)

        preview_win = tk.Toplevel(parent)
        preview_win.title(f"截图预览 - {os.path.basename(image_path)}")
        preview_win.geometry(f"{win_width}x{win_height}+400+200")
        preview_win.configure(bg=COLOR_BG)
        preview_win.resizable(True, True)

        canvas_frame = tk.Frame(
            preview_win, bg=COLOR_FRAME_BG, relief="solid", bd=1
        )
        canvas_frame.pack(fill="both", expand=True, padx=10, pady=10)

        canvas = tk.Canvas(
            canvas_frame, bg="#FAFAFA", highlightthickness=0
        )
        canvas.pack(fill="both", expand=True, padx=5, pady=5)

        display_width = win_width - 60
        display_height = win_height - 120
        img_copy = img.copy()
        img_copy.thumbnail(
            (display_width, display_height), Image.Resampling.LANCZOS
        )
        photo = ImageTk.PhotoImage(img_copy)
        canvas.delete("all")
        x = (display_width - img_copy.width) // 2
        y = (display_height - img_copy.height) // 2
        canvas.create_image(max(x, 0), max(y, 0), anchor="nw", image=photo)
        canvas.image = photo

        info_frame = tk.Frame(preview_win, bg=COLOR_BG)
        info_frame.pack(fill="x", padx=10, pady=(0, 10))

        tk.Label(
            info_frame,
            text=f"{os.path.basename(image_path)}  ({img.width}x{img.height})",
            font=("微软雅黑", 9),
            bg=COLOR_BG,
            fg="#555555",
        ).pack(side="left")

        tk.Button(
            info_frame, text="关闭",
            font=FONT_BUTTON,
            bg=COLOR_BUTTON, fg=COLOR_BUTTON_TEXT,
            relief="flat", bd=0, cursor="hand2",
            padx=15, pady=3,
            command=preview_win.destroy
        ).pack(side="right")

    except Exception as error:
        logger.error(f"预览图片失败: {error}")
