# -*- coding: utf-8 -*-
"""Tkinter GUI for discovering and configuring Hikvision SADP devices."""

import argparse
from ctypes import byref
import ipaddress
import json
from pathlib import Path
import queue
import threading
import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime

# Import SADP SDK and CLI modules, handling relative imports for package context
# This allows the script to be run both as a standalone module and as part of a package.
# 汉语注释：导入 SADP SDK 和 CLI 模块，处理包上下文的相对导入
if __package__:
    from . import sadp as sdk
    from .sadp_cli import (
        SADP_ADD,
        SADP_DEC,
        SADP_RESTART,
        SADP_UPDATE,
        SADP_UPDATEFAIL,
        SADPSearchTool,
        _decode_field,
    )
else:
    import sadp as sdk
    from sadp_cli import (
        SADP_ADD,
        SADP_DEC,
        SADP_RESTART,
        SADP_UPDATE,
        SADP_UPDATEFAIL,
        SADPSearchTool,
        _decode_field,
    )


class SADPGui:
    """Display SADP device events and provide common SDK operations.
        展示 SADP 设备事件，并提供常用 SDK 操作。
    """

    def __init__(self, root, tool, record_file):
        self.root = root    # Tkinter root window
        self.tool = tool    # SADPSearchTool instance
        self.record_file = Path(record_file)    # 获取设备记录文件路径
        self.devices = {}
        self.devices_lock = threading.Lock()
        self.events = queue.Queue()
        self.searching = False
        self.callback = sdk.PDEVICE_FIND_CALLBACK(self._on_device_find)

        # 初始化 Tkinter 窗口
        self.root.title("SADP 局域网设备搜索工具")
        self.root.geometry("1100x650")
        self.root.minsize(850, 480)
        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self._close)
        self.root.after(100, self._poll_events)

        version = self.tool.dll.SADP_GetSadpVersion()
        version_text = ".".join(
            str((version >> shift) & 0xff) for shift in (24, 16, 8, 0)
        )
        self.version_var.set(f"SADP SDK 版本：V{version_text}")
        if not self.tool.dll.SADP_SetLogToFile(3, b".\\log", 1):
            self._set_status(f"设置 SDK 日志失败，错误码：{self._error_code()}")
        else:
            self._set_status(f"设备记录文件：{self.record_file}")

    def _build_ui(self):
        """
        构建 Tkinter 用户界面，包括工具栏、设备列表表格、设备详情和事件日志区域，以及状态栏。
        """
        toolbar = ttk.Frame(self.root, padding=(10, 10, 10, 4))
        toolbar.pack(fill=tk.X)

        self.start_button = ttk.Button(toolbar, text="开始搜索", command=self._start_search)
        self.start_button.pack(side=tk.LEFT, padx=(0, 6))
        self.refresh_button = ttk.Button(toolbar, text="手动刷新", command=self._refresh)
        self.refresh_button.pack(side=tk.LEFT, padx=6)
        self.stop_button = ttk.Button(toolbar, text="停止搜索", command=self._stop_search)
        self.stop_button.pack(side=tk.LEFT, padx=6)
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=8)
        ttk.Button(toolbar, text="激活设备", command=self._activate_device).pack(
            side=tk.LEFT, padx=6
        )
        ttk.Button(toolbar, text="修改网络参数", command=self._modify_network).pack(
            side=tk.LEFT, padx=6
        )
        ttk.Button(toolbar, text="清空列表", command=self._clear_devices).pack(
            side=tk.LEFT, padx=6
        )

        self.version_var = tk.StringVar()
        ttk.Label(toolbar, textvariable=self.version_var).pack(side=tk.RIGHT, padx=4)

        table_frame = ttk.Frame(self.root, padding=(10, 4, 10, 4))
        table_frame.pack(fill=tk.BOTH, expand=True)
        columns = ("serial", "mac", "ip", "port", "type", "description", "activated")
        self.device_table = ttk.Treeview(
            table_frame, columns=columns, show="headings", selectmode="browse"
        )
        headings = {
            "serial": ("序列号", 155),
            "mac": ("MAC 地址", 140),
            "ip": ("IP 地址", 120),
            "port": ("端口", 65),
            "type": ("设备类型", 85),
            "description": ("设备描述", 220),
            "activated": ("激活状态", 85),
        }
        for column, (title, width) in headings.items():
            self.device_table.heading(column, text=title)
            self.device_table.column(column, width=width, minwidth=60, anchor=tk.W)
        vertical_scroll = ttk.Scrollbar(
            table_frame, orient=tk.VERTICAL, command=self.device_table.yview
        )
        horizontal_scroll = ttk.Scrollbar(
            table_frame, orient=tk.HORIZONTAL, command=self.device_table.xview
        )
        self.device_table.configure(
            yscrollcommand=vertical_scroll.set, xscrollcommand=horizontal_scroll.set
        )
        self.device_table.grid(row=0, column=0, sticky="nsew")
        vertical_scroll.grid(row=0, column=1, sticky="ns")
        horizontal_scroll.grid(row=1, column=0, sticky="ew")
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)
        self.device_table.bind("<<TreeviewSelect>>", self._show_device_details)

        output = ttk.Notebook(self.root)
        output.pack(fill=tk.X, padx=10, pady=(2, 6))
        details_frame = ttk.Frame(output, padding=8)
        events_frame = ttk.Frame(output, padding=8)
        output.add(details_frame, text="设备详情")
        output.add(events_frame, text="事件日志")
        self.details_text = tk.Text(
            details_frame, height=3, wrap=tk.WORD, state=tk.DISABLED
        )
        self.details_text.pack(fill=tk.X)
        self.events_text = tk.Text(
            events_frame, height=4, wrap=tk.WORD, state=tk.DISABLED
        )
        self.events_text.pack(fill=tk.X)

        footer = ttk.Frame(self.root, padding=(10, 2, 10, 8))
        footer.pack(fill=tk.X)
        self.status_var = tk.StringVar(value="就绪")
        ttk.Label(footer, textvariable=self.status_var).pack(side=tk.LEFT)
        self._update_buttons()

    def _error_code(self):
        return self.tool.dll.SADP_GetLastError()

    def _set_status(self, text):
        self.status_var.set(text)

    def _append_record(self, event, info):
        """
        将设备事件记录追加到文件中。
        """
        record = {
            "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
            "event": event,
            "device": info,
        }
        try:
            self.record_file.parent.mkdir(parents=True, exist_ok=True)
            with self.record_file.open("a", encoding="utf-8", newline="\n") as stream:
                stream.write(json.dumps(record, ensure_ascii=False) + "\n")
                stream.flush()
        except OSError as exc:
            self.events.put(("error", f"写入设备记录失败 ({self.record_file})：{exc}"))

    def _on_device_find(self, device_pointer, _user_data):
        """
        SADP 设备发现回调函数，处理设备事件并更新设备列表。
        """
        if not device_pointer:
            return
        try:
            device = device_pointer.contents
            result = device.iResult
            label = {
                SADP_ADD: "新增设备",
                SADP_UPDATE: "更新设备",
                SADP_DEC: "设备下线",
                SADP_RESTART: "设备重启",
                SADP_UPDATEFAIL: "更新失败",
            }.get(result)
            if label is None:
                return

            info = {
                "serial": _decode_field(device.szSerialNO),
                "mac": _decode_field(device.szMAC),
                "ip": _decode_field(device.szIPv4Address),
                "port": device.dwPort,
                "type": device.dwDeviceType,
                "description": _decode_field(device.szDevDesc),
                "software_version": _decode_field(device.szDeviceSoftwareVersion),
                "dsp_version": _decode_field(device.szDSPVersion),
                "boot_time": _decode_field(device.szBootTime),
                "http_port": device.wHttpPort,
                "dhcp_enabled": bool(device.byDhcpEnabled),
                "activated": bool(device.byActivated),
                "support": device.bySupport,
            }
            with self.devices_lock:
                self._append_record(label, info)
                if result == SADP_DEC:
                    self.devices.pop(info["serial"], None)
                elif result != SADP_UPDATEFAIL:
                    self.devices[info["serial"]] = info
            self.events.put(("device", label, info))
        except Exception as exc:
            self.events.put(("error", f"SADP 设备回调处理失败：{exc}"))

    def _poll_events(self):
        """
        定期轮询事件队列，处理设备事件和错误信息，并更新设备列表和状态栏。
        """
        while True:
            try:
                event = self.events.get_nowait()
            except queue.Empty:
                break
            if event[0] == "device":
                _, label, info = event
                self._refresh_table()
                self._append_event(f"{label}：{info['serial']} ({info['ip']})")
                self._set_status(f"已发现/更新设备：{info['serial']}，当前 {self._device_count()} 台")
            else:
                self._append_event(event[1])
                self._set_status(event[1])
        self.root.after(100, self._poll_events)

    def _device_count(self):
        """
        返回当前设备列表中的设备数量。
        """
        with self.devices_lock:
            return len(self.devices)

    def _refresh_table(self):
        with self.devices_lock:
            devices = list(self.devices.values())
        selected = self.device_table.selection()
        selected_serial = selected[0] if selected else None
        self.device_table.delete(*self.device_table.get_children())
        for info in sorted(devices, key=lambda item: item["serial"]):
            serial = info["serial"] or info["mac"] or f"device-{id(info)}"
            self.device_table.insert(
                "",
                tk.END,
                iid=serial,
                values=(
                    info["serial"],
                    info["mac"],
                    info["ip"],
                    info["port"],
                    info["type"],
                    info["description"],
                    "已激活" if info["activated"] else "未激活",
                ),
            )
        if selected_serial and self.device_table.exists(selected_serial):
            self.device_table.selection_set(selected_serial)

    def _append_event(self, text):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.events_text.configure(state=tk.NORMAL)
        self.events_text.insert(tk.END, f"[{timestamp}] {text}\n")
        self.events_text.see(tk.END)
        self.events_text.configure(state=tk.DISABLED)

    def _show_device_details(self, _event=None):
        """
        
        """
        selection = self.device_table.selection()
        if not selection:
            return
        with self.devices_lock:
            info = self.devices.get(selection[0])
            if info is None:
                info = next(
                    (item for item in self.devices.values() if item["mac"] == selection[0]),
                    None,
                )
            if info is None:
                return
            details = (
                f"序列号：{info['serial']}    MAC：{info['mac']}    IP：{info['ip']}    "
                f"端口：{info['port']}    HTTP端口：{info['http_port']}\n"
                f"描述：{info['description']}    类型：{info['type']}    "
                f"DHCP：{'启用' if info['dhcp_enabled'] else '禁用'}    "
                f"激活：{'已激活' if info['activated'] else '未激活'}\n"
                f"软件版本：{info['software_version']}    DSP版本：{info['dsp_version']}    "
                f"开机时间：{info['boot_time']}    支持功能：0x{info['support']:02x}"
            )
        self.details_text.configure(state=tk.NORMAL)
        self.details_text.delete("1.0", tk.END)
        self.details_text.insert(tk.END, details + "\n")
        self.details_text.configure(state=tk.DISABLED)

    def _selected_device(self):
        selection = self.device_table.selection()
        if not selection:
            messagebox.showwarning("未选择设备", "请先在设备列表中选择一台设备。", parent=self.root)
            return None
        with self.devices_lock:
            info = self.devices.get(selection[0])
            if info is None:
                info = next(
                    (item for item in self.devices.values() if item["mac"] == selection[0]),
                    None,
                )
            return info

    def _update_buttons(self):
        self.start_button.configure(state=tk.DISABLED if self.searching else tk.NORMAL)
        self.refresh_button.configure(state=tk.NORMAL if self.searching else tk.DISABLED)
        self.stop_button.configure(state=tk.NORMAL if self.searching else tk.DISABLED)

    def _start_search(self):
        if self.searching:
            return
        if self.tool.dll.SADP_Start_V30(self.callback, 1, None):
            self.searching = True
            self._update_buttons()
            self._set_status("正在搜索设备…")
            self._append_event("已开始搜索设备")
        else:
            self._show_sdk_error("启动 SADP 搜索失败")

    def _refresh(self):
        if not self.searching:
            messagebox.showinfo("提示", "请先开始搜索设备。", parent=self.root)
        elif self.tool.dll.SADP_SendInquiry():
            self._set_status("已发送手动刷新请求")
        else:
            self._show_sdk_error("刷新设备失败")

    def _stop_search(self):
        if not self.searching:
            return
        if self.tool.dll.SADP_Stop():
            self.searching = False
            self._update_buttons()
            self._set_status("设备搜索已停止")
            self._append_event("已停止搜索设备")
        else:
            self._show_sdk_error("停止 SADP 搜索失败")

    def _clear_devices(self):
        if not messagebox.askyesno("确认清空", "确定清空 SADP 设备缓存和当前列表吗？", parent=self.root):
            return
        if not self.tool.dll.SADP_Clearup():
            self._show_sdk_error("清空设备列表失败")
            return
        with self.devices_lock:
            self.devices.clear()
        self.device_table.delete(*self.device_table.get_children())
        self._set_status("设备列表已清空")
        self._append_event("已清空设备列表")

    def _activate_device(self):
        """
        弹出激活设备对话框，允许用户输入设备序列号和新密码，并调用 SDK 激活设备。
        """
        info = self._selected_device()
        if info is None:
            return
        dialog = tk.Toplevel(self.root)
        dialog.title("激活设备")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)
        frame = ttk.Frame(dialog, padding=12)
        frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(frame, text="设备序列号：").grid(row=0, column=0, sticky=tk.W, pady=4)
        serial_var = tk.StringVar(value=info["serial"])
        ttk.Entry(frame, textvariable=serial_var, width=34).grid(row=0, column=1, pady=4)
        ttk.Label(frame, text="新密码（至少8位）：").grid(row=1, column=0, sticky=tk.W, pady=4)
        password_var = tk.StringVar()
        password_entry = ttk.Entry(frame, textvariable=password_var, show="*", width=34)
        password_entry.grid(row=1, column=1, pady=4)

        def activate():
            serial = serial_var.get().strip()
            password = password_var.get()
            if not serial or not password:
                messagebox.showwarning("输入不完整", "序列号和新密码不能为空。", parent=dialog)
                return
            if len(password) < 8:
                messagebox.showwarning("密码长度不足", "新密码至少需要8位。", parent=dialog)
                return
            if self.tool.dll.SADP_ActivateDevice(serial.encode("utf-8"), password.encode("utf-8")):
                dialog.destroy()
                self._set_status(f"设备 {serial} 激活成功")
                self._append_event(f"设备 {serial} 激活成功")
                messagebox.showinfo("激活成功", f"设备 {serial} 已激活。", parent=self.root)
            else:
                messagebox.showerror(
                    "激活失败", f"错误码：{self._error_code()}", parent=dialog
                )

        buttons = ttk.Frame(frame)
        buttons.grid(row=2, column=0, columnspan=2, sticky=tk.E, pady=(10, 0))
        ttk.Button(buttons, text="激活", command=activate).pack(side=tk.LEFT, padx=4)
        ttk.Button(buttons, text="取消", command=dialog.destroy).pack(side=tk.LEFT, padx=4)
        password_entry.focus_set()

    def _modify_network(self):
        """
        弹出修改设备网络参数对话框，允许用户输入新的网络参数，并调用 SDK 更新设备网络配置。
        """
        info = self._selected_device()
        if info is None:
            return
        dialog = tk.Toplevel(self.root)
        dialog.title("修改设备网络参数")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)
        frame = ttk.Frame(dialog, padding=12)
        frame.pack(fill=tk.BOTH, expand=True)
        fields = (
            ("设备 MAC 地址：", info["mac"]),
            ("设备密码：", ""),
            ("新 IP 地址：", info["ip"]),
            ("网关地址：", ""),
            ("子网掩码：", ""),
        )
        variables = []
        for row, (label, value) in enumerate(fields):
            ttk.Label(frame, text=label).grid(row=row, column=0, sticky=tk.W, pady=4)
            variable = tk.StringVar(value=value)
            entry = ttk.Entry(
                frame, textvariable=variable, width=34, show="*" if row == 1 else ""
            )
            entry.grid(row=row, column=1, pady=4)
            variables.append(variable)

        def update_network():
            mac, password, ip, gateway, netmask = [var.get().strip() for var in variables]
            if not mac or not password:
                messagebox.showwarning(
                    "输入不完整", "设备 MAC 地址和密码不能为空。", parent=dialog
                )
                return
            try:
                for address in (ip, gateway, netmask):
                    ipaddress.IPv4Address(address)
            except ipaddress.AddressValueError:
                messagebox.showwarning(
                    "地址无效", "IP、网关和子网掩码必须是有效的 IPv4 地址。", parent=dialog
                )
                return

            net_param = sdk.SADP_DEV_NET_PARAM()
            net_param.szIPv4Address = ip.encode("ascii")
            net_param.szIPv4Gateway = gateway.encode("ascii")
            net_param.szIPv4SubNetMask = netmask.encode("ascii")
            net_param.wPort = 8000
            net_param.wHttpPort = 80
            net_param.byDhcpEnable = 0
            if self.tool.dll.SADP_ModifyDeviceNetParam(
                mac.encode("utf-8"), password.encode("utf-8"), byref(net_param)
            ):
                dialog.destroy()
                self._set_status(f"已提交设备 {mac} 的网络参数修改")
                self._append_event(f"已提交设备 {mac} 的网络参数修改")
                messagebox.showinfo(
                    "修改成功", "设备网络参数修改请求已提交。", parent=self.root
                )
            else:
                messagebox.showerror(
                    "修改失败", f"错误码：{self._error_code()}", parent=dialog
                )

        buttons = ttk.Frame(frame)
        buttons.grid(row=len(fields), column=0, columnspan=2, sticky=tk.E, pady=(10, 0))
        ttk.Button(buttons, text="修改", command=update_network).pack(side=tk.LEFT, padx=4)
        ttk.Button(buttons, text="取消", command=dialog.destroy).pack(side=tk.LEFT, padx=4)

    def _show_sdk_error(self, action):
        code = self._error_code()
        message = f"{action}，错误码：{code}"
        self._set_status(message)
        self._append_event(message)
        messagebox.showerror("SADP 操作失败", message, parent=self.root)

    def _close(self):
        if self.searching:
            if not self.tool.dll.SADP_Stop():
                self._show_sdk_error("退出前停止 SADP 搜索失败")
                return
            self.searching = False
        self.root.destroy()


def main(argv=None):
    """
    
    """
    parser = argparse.ArgumentParser(description="海康 SADP Tkinter 图形界面")
    default_dll = Path(__file__).resolve().with_name("Sadp.dll")
    parser.add_argument("--dll", default=str(default_dll), help="SADP 动态库路径")
    default_record_file = Path(__file__).resolve().with_name("sadp_devices.jsonl")
    parser.add_argument(
        "--record-file", default=str(default_record_file), help="设备搜索记录文件"
    )
    args = parser.parse_args(argv)

    root = tk.Tk()
    try:
        tool = SADPSearchTool(args.dll)
    except (OSError, AttributeError) as exc:
        root.withdraw()
        messagebox.showerror("加载 SADP 动态库失败", str(exc), parent=root)
        root.destroy()
        return 1

    SADPGui(root, tool, args.record_file)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
