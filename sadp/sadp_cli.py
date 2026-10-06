# -*- coding: utf-8 -*-
"""Interactive Hikvision SADP device search tool."""

import argparse
import ctypes
import ipaddress
from pathlib import Path
import sys
import threading
from ctypes import byref

if __package__:
    from . import sadp as sdk
else:
    import sadp as sdk


SADP_ADD = sdk.SADP_ADD
SADP_UPDATE = sdk.SADP_UPDATE
SADP_DEC = sdk.SADP_DEC
SADP_RESTART = sdk.SADP_RESTART
SADP_UPDATEFAIL = sdk.SADP_UPDATEFAIL


class SADPSearchTool:
    """Load only the SDK exports used by this CLI."""

    def __init__(self, dll_path):
        if sys.platform.startswith("win"):
            self.dll = ctypes.WinDLL(dll_path)
        else:
            self.dll = ctypes.CDLL(dll_path)

        self._configure("SADP_Start_V30", [sdk.PDEVICE_FIND_CALLBACK, ctypes.c_int, ctypes.c_void_p], sdk.BOOL)
        self._configure("SADP_SendInquiry", [], sdk.BOOL)
        self._configure("SADP_Stop", [], sdk.BOOL)
        self._configure("SADP_Clearup", [], sdk.BOOL)
        self._configure("SADP_ActivateDevice", [ctypes.c_char_p, ctypes.c_char_p], sdk.BOOL)
        self._configure(
            "SADP_ModifyDeviceNetParam",
            [ctypes.c_char_p, ctypes.c_char_p, ctypes.POINTER(sdk.SADP_DEV_NET_PARAM)],
            sdk.BOOL,
        )
        self._configure("SADP_GetSadpVersion", [], sdk.DWORD)
        self._configure("SADP_SetLogToFile", [ctypes.c_int, ctypes.c_char_p, ctypes.c_int], sdk.BOOL)
        self._configure("SADP_GetLastError", [], sdk.DWORD)

    def _configure(self, name, argtypes, restype):
        try:
            function = getattr(self.dll, name)
        except AttributeError as exc:
            raise AttributeError(f"SADP动态库缺少必需接口: {name}") from exc
        function.argtypes = argtypes
        function.restype = restype


def _decode_field(value):
    return bytes(value).split(b"\0", 1)[0].decode("utf-8", errors="replace")


class SADPConsole:
    """Provide the menu-driven functionality of sadp/main.cpp."""

    def __init__(self, tool):
        self.tool = tool
        self.devices = {}
        self.devices_lock = threading.Lock()
        self.searching = False
        self.callback = sdk.PDEVICE_FIND_CALLBACK(self._on_device_find)

    def _on_device_find(self, device_pointer, _user_data):
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
                if result == SADP_DEC:
                    self.devices.pop(info["serial"], None)
                elif result != SADP_UPDATEFAIL:
                    self.devices[info["serial"]] = info

            print(f"\n[{label}]")
            if result == SADP_UPDATEFAIL:
                return
            print("----------------------------------------")
            print(f"设备序列号: {info['serial']}")
            print(f"设备MAC: {info['mac']}")
            print(f"设备IP: {info['ip']}")
            print(f"设备端口: {info['port']}")
            print(f"设备类型: {info['type']}")
            print(f"设备描述: {info['description']}")
            print(f"软件版本: {info['software_version']}")
            print(f"DSP版本: {info['dsp_version']}")
            print(f"开机时间: {info['boot_time']}")
            print(f"HTTP端口: {info['http_port']}")
            print(f"DHCP: {'启用' if info['dhcp_enabled'] else '禁用'}")
            print(f"激活状态: {'已激活' if info['activated'] else '未激活'}")
            print(f"支持功能: 0x{info['support']:02x}")
            print("----------------------------------------")
        except Exception as exc:
            print(f"SADP设备回调处理失败: {exc}", file=sys.stderr)

    def _error_code(self):
        return self.tool.dll.SADP_GetLastError()

    def _print_menu(self):
        print("\n========== SADP局域网设备搜索工具 ==========")
        print("1. 开始搜索设备")
        print("2. 手动刷新设备")
        print("3. 停止搜索设备")
        print("4. 显示当前设备列表")
        print("5. 清空设备列表")
        print("6. 激活设备")
        print("7. 修改设备网络参数")
        print("8. 显示SDK版本")
        print("0. 退出程序")
        print("===========================================")

    def _show_devices(self):
        with self.devices_lock:
            devices = [self.devices[key].copy() for key in sorted(self.devices)]

        if not devices:
            print("\n当前没有搜索到设备!")
            return

        print(f"\n========== 当前设备列表（{len(devices)}台） ==========")
        for index, device in enumerate(devices, start=1):
            print(f"[{index}]")
            print(f"  序列号: {device['serial']}")
            print(f"  MAC: {device['mac']}")
            print(f"  IP: {device['ip']}")
            print(f"  端口: {device['port']}")
            print(f"  描述: {device['description']}")
            print(f"  激活: {'是' if device['activated'] else '否'}")
            print("----------------------------------------")

    def _show_version(self):
        version = self.tool.dll.SADP_GetSadpVersion()
        print(
            "SADP SDK版本: V"
            f"{(version >> 24) & 0xff}."
            f"{(version >> 16) & 0xff}."
            f"{(version >> 8) & 0xff}."
            f"{version & 0xff}"
        )

    def _activate_device(self):
        serial = input("\n请输入设备序列号: ").strip()
        password = input("请输入新密码(至少8位): ")
        if not serial or not password:
            print("设备序列号和密码不能为空!")
            return

        if self.tool.dll.SADP_ActivateDevice(
            serial.encode("utf-8"), password.encode("utf-8")
        ):
            print("设备激活成功!")
        else:
            print(f"设备激活失败! 错误码: {self._error_code()}")

    def _modify_network(self):
        mac = input("\n请输入设备MAC地址: ").strip()
        password = input("请输入设备密码: ")
        ip = input("请输入新IP地址: ").strip()
        gateway = input("请输入网关地址: ").strip()
        netmask = input("请输入子网掩码: ").strip()

        if not mac or not password:
            print("设备MAC地址和密码不能为空!")
            return
        try:
            for value in (ip, gateway, netmask):
                ipaddress.IPv4Address(value)
        except ipaddress.AddressValueError:
            print("IP地址、网关和子网掩码必须是有效的IPv4地址!")
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
            print("修改设备网络参数成功!")
        else:
            print(f"修改设备网络参数失败! 错误码: {self._error_code()}")

    def _handle_choice(self, choice):
        if choice == 1:
            if self.searching:
                print("设备搜索已经在运行中!")
            elif self.tool.dll.SADP_Start_V30(self.callback, 1, None):
                self.searching = True
                print("开始搜索设备...")
            else:
                print(f"启动SADP失败! 错误码: {self._error_code()}")
        elif choice == 2:
            if not self.searching:
                print("请先开始搜索设备!")
            elif self.tool.dll.SADP_SendInquiry():
                print("手动刷新设备...")
            else:
                print(f"刷新失败! 错误码: {self._error_code()}")
        elif choice == 3:
            if not self.searching:
                print("设备搜索未运行!")
            elif self.tool.dll.SADP_Stop():
                self.searching = False
                print("停止搜索设备成功!")
            else:
                print(f"停止搜索失败! 错误码: {self._error_code()}")
        elif choice == 4:
            self._show_devices()
        elif choice == 5:
            if self.tool.dll.SADP_Clearup():
                with self.devices_lock:
                    self.devices.clear()
                print("清空设备列表成功!")
            else:
                print(f"清空失败! 错误码: {self._error_code()}")
        elif choice == 6:
            self._activate_device()
        elif choice == 7:
            self._modify_network()
        elif choice == 8:
            self._show_version()
        elif choice == 0:
            return False
        else:
            print("无效的选择，请重新输入!")
        return True

    def run(self):
        print("========================================")
        print("    SADP局域网设备搜索工具 v1.0")
        print("========================================")

        if not self.tool.dll.SADP_SetLogToFile(3, b".\\log", 1):
            print(f"设置日志失败! 错误码: {self._error_code()}")
        self._show_version()

        while True:
            self._print_menu()
            try:
                choice = input("请选择操作: ").strip()
            except EOFError:
                print("\n收到输入结束信号，正在退出...")
                break

            try:
                keep_running = self._handle_choice(int(choice))
            except ValueError:
                print("无效的选择，请重新输入!")
                continue
            if not keep_running:
                break

        if self.searching:
            if self.tool.dll.SADP_Stop():
                self.searching = False
            else:
                print(f"停止搜索失败! 错误码: {self._error_code()}")
        print("程序退出!")


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="海康 SADP 局域网设备搜索工具")
    default_dll = Path(__file__).resolve().with_name("Sadp.dll")
    parser.add_argument(
        "--dll",
        default=str(default_dll),
        help="SADP 动态库路径 (默认: %(default)s)",
    )
    args = parser.parse_args(argv)

    try:
        tool = SADPSearchTool(args.dll)
    except (OSError, AttributeError) as exc:
        print(f"加载 SADP 动态库失败: {exc}", file=sys.stderr)
        return 1

    SADPConsole(tool).run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
