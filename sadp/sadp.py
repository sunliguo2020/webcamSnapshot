# -*- coding: utf-8 -*-
"""
================================================================================
海康 SADP (Search Active Device Protocol) SDK 封装模块
================================================================================

本模块对海康 SADP.dll / libsadp.so 动态库进行 Python ctypes 封装，
实现局域网内海康设备的搜索、配置修改、激活、密码重置等功能。

SADP 协议通过 UDP 广播方式发现局域网内的海康设备，可获取设备的
IP地址、MAC地址、序列号、设备型号、固件版本等信息，并能修改设备
网络参数、激活设备、重置密码等。

依赖: Sadp.dll (Windows) 或 libsadp.so (Linux)
"""

import ctypes
from ctypes import *
import sys

# ============================================================================
# 基本类型定义 (对应 Windows SDK 中的类型别名)
# ============================================================================
BOOL = c_int        # 布尔类型 (0=假, 非0=真)
WORD = c_ushort     # 16位无符号整数
DWORD = c_uint      # 32位无符号整数
BYTE = c_ubyte      # 8位无符号整数

# 根据操作系统选择调用约定 (Windows 使用 stdcall, Linux 使用 cdecl)
if sys.platform.startswith('win'):
    CALLBACK = ctypes.WINFUNCTYPE
else:
    CALLBACK = ctypes.CFUNCTYPE

# ============================================================================
# 常量宏定义 - 消息操作类型 (设备状态变更通知类型)
# ============================================================================
# 设备发现回调中 iResult 字段对应的消息类型
SADP_ADD = 1         # 新增一台设备（发现新设备）
SADP_UPDATE = 2      # 设备信息更新
SADP_DEC = 3         # 设备下线（离线）
SADP_RESTART = 4     # 设备重新启动
SADP_UPDATEFAIL = 5  # 设备更新失败

# 外部命令码 (用于 SADP_GetDeviceConfig / SADP_SetDeviceConfig 的 dwCommand 参数)
SADP_GET_DEVICE_CODE = 1              # 获取设备验证码
SADP_GET_ENCRYPT_STRING = 2           # 获取加密字符串
SADP_GET_DEVICE_TYPE_UNLOCK_CODE = 3  # 获取设备类型解锁码
SADP_SET_DEVICE_CUSTOM_TYPE = 4       # 设置设备自定义类型
SADP_GET_GUID = 5                     # 获取 GUID (全球唯一标识符)
SADP_GET_SECURITY_QUESTION = 6        # 获取安全问题配置
SADP_SET_SECURITY_QUESTION = 7        # 设置安全问题配置
SADP_SET_HCPLATFORM_STATUS = 8        # 设置 HCPlatform 状态
SADP_SET_VERIFICATION_CODE = 9        # 设置验证码
SADP_GET_BIND_LIST = 12               # 获取绑定列表
SADP_SET_BIND_LIST = 13               # 设置绑定列表
SADP_RESTORE_INACTIVE = 14            # 恢复未激活设备
SADP_SET_WIFI_REGION = 15             # 设置 WiFi 区域
SADP_SET_CHANNEL_DEFAULT_PASSWORD = 16  # 设置通道默认密码
SADP_GET_SELF_CHECK = 17              # 获取自检状态
SADP_DISK_LOCATE = 18                 # 硬盘定位
SADP_EHOME_ENABLE = 19                # 启用 eHome 协议
SADP_SET_USER_MAILBOX = 20            # 设置用户邮箱
SADP_GET_QR_CODES = 21                # 获取二维码
SADP_GET_PASSWORD_RESET_TYPE = 27     # 获取密码重置方式

# 长度限制常量 (结构体中字符数组的最大长度)
SADP_MAX_VERIFICATION_CODE_LEN = 12   # 验证码最大长度
MAX_PASS_LEN = 16                      # 密码最大长度
MAX_QUESTION_LIST_LEN = 32             # 安全问题列表最大长度
SADP_MAX_BIND_NUM = 32                 # 最大绑定设备数量
MAX_CPU_LEN = 32                       # CPU 信息字符串长度
MAX_MEMORY_LEN = 32                    # 内存信息字符串长度
MAX_USERNAME_LEN = 32                  # 用户名最大长度
SADP_MAX_SERIALNO_LEN = 64             # 序列号最大长度
MAX_DEVICE_CODE = 128                  # 设备验证码最大长度
MAX_MAILBOX_LEN = 128                  # 邮箱地址最大长度
MAX_GUID_LEN = 128                     # GUID 最大长度
MAX_EXCHANGE_CODE = 256                # 交换码最大长度
MAX_ENCRYPT_CODE = 256                 # 加密字符串最大长度
MAX_UNLOCK_CODE_KEY = 256              # 解锁码密钥最大长度
MAX_QR_CODES = 256                     # 二维码数据最大长度
MAX_ANSWER_LEN = 256                   # 安全问题答案最大长度
MAX_UNLOCK_CODE_RANDOM_LEN = 256       # 随机解锁码最大长度
MAX_FILE_PATH_LEN = 260                # 文件路径最大长度 (Windows MAX_PATH)

# 错误码 (通过 SADP_GetLastError 获取)
SADP_ERROR_BASE = 2000                          # 错误码起始值
SADP_NOERROR = 0                               # 无错误
SADP_ALLOC_RESOURCE_ERROR = SADP_ERROR_BASE + 1      # 分配资源失败
SADP_NOT_START_ERROR = SADP_ERROR_BASE + 2            # SADP 未启动
SADP_NO_ADAPTER_ERROR = SADP_ERROR_BASE + 3           # 未找到网络适配器
SADP_GET_ADAPTER_FAIL_ERROR = SADP_ERROR_BASE + 4     # 获取适配器失败
SADP_PARAMETER_ERROR = SADP_ERROR_BASE + 5            # 参数错误
SADP_OPEN_ADAPTER_FAIL_ERROR = SADP_ERROR_BASE + 6    # 打开适配器失败
SADP_SEND_PACKET_FAIL_ERROR = SADP_ERROR_BASE + 7     # 发送报文失败
SADP_SYSTEM_CALL_ERROR = SADP_ERROR_BASE + 8          # 系统调用失败
SADP_DEVICE_DENY = SADP_ERROR_BASE + 9                # 设备拒绝
SADP_NPF_INSTALL_ERROR = SADP_ERROR_BASE + 10         # NPF 安装失败
SADP_TIMEOUT = SADP_ERROR_BASE + 11                   # 操作超时
SADP_CREATE_SOCKET_ERROR = SADP_ERROR_BASE + 12       # 创建 Socket 失败
SADP_BIND_SOCKET_ERROR = SADP_ERROR_BASE + 13         # 绑定 Socket 失败
SADP_JOIN_MULTI_CAST_ERROR = SADP_ERROR_BASE + 14     # 加入组播失败
SADP_NETWORK_SEND_ERROR = SADP_ERROR_BASE + 15        # 网络发送失败
SADP_NETWORK_RECV_ERROR = SADP_ERROR_BASE + 16        # 网络接收失败
SADP_XML_PARSE_ERROR = SADP_ERROR_BASE + 17           # XML 解析失败
SADP_LOCKED = SADP_ERROR_BASE + 18                    # 设备已锁定
SADP_NOT_ACTIVATED = SADP_ERROR_BASE + 19             # 设备未激活
SADP_RISK_PASSWORD = SADP_ERROR_BASE + 20             # 风险密码
SADP_HAS_ACTIVATED = SADP_ERROR_BASE + 21             # 设备已激活
SADP_EMPTY_ENCRYPT_STRING = SADP_ERROR_BASE + 22      # 加密字符串为空
SADP_EXPORT_FILE_OVERDUE = SADP_ERROR_BASE + 23       # 导出文件过期
SADP_PASSWORD_ERROR = SADP_ERROR_BASE + 24            # 密码错误
SADP_LONG_SECURITY_ANSWER = SADP_ERROR_BASE + 25      # 安全问题答案过长
SADP_INVALID_GUID = SADP_ERROR_BASE + 26              # 无效 GUID
SADP_ANSWER_ERROR = SADP_ERROR_BASE + 27              # 安全问题答案错误
SADP_QUESTION_NUM_ERR = SADP_ERROR_BASE + 28          # 安全问题数量错误
SADP_LOAD_WPCAP_FAIL = SADP_ERROR_BASE + 30           # 加载 wpcap 失败
SADP_ILLEGAL_VERIFICATION_CODE = SADP_ERROR_BASE + 33 # 非法验证码
SADP_BIND_ERROR_DEV = SADP_ERROR_BASE + 34            # 绑定设备错误
SADP_EXTED_MAX_BIND_NUM = SADP_ERROR_BASE + 35        # 超出最大绑定数量
SADP_MAILBOX_NOT_EXIST = SADP_ERROR_BASE + 36         # 邮箱不存在
SADP_MAILBOX_NOT_SET = SADP_ERROR_BASE + 38           # 邮箱未设置
SADP_INVALID_RESET_CODE = SADP_ERROR_BASE + 39        # 无效重置码
SADP_NO_PERMISSION = SADP_ERROR_BASE + 40             # 无权限
SADP_GET_EXCHANGE_CODE_ERROR = SADP_ERROR_BASE + 41   # 获取交换码失败
SADP_CREATE_RSA_KEY_ERROR = SADP_ERROR_BASE + 42      # 创建 RSA 密钥失败
SADP_BASE64_ENCODE_ERROR = SADP_ERROR_BASE + 43       # Base64 编码失败
SADP_BASE64_DECODE_ERROR = SADP_ERROR_BASE + 44       # Base64 解码失败
SADP_AES_ENCRYPT_ERROR = SADP_ERROR_BASE + 45         # AES 加密失败

# SADP 设备过滤规则类型 (用于 SADP_SetDeviceFilterRule)
SADP_DISPLAY_ALL = 0              # 显示所有设备
SADP_FILTER_EZVIZ = 0x01          # 过滤萤石(EZVIZ)设备
SADP_FILTER_OEM = 0x02            # 过滤 OEM 设备
SADP_FILTER_EZVIZ_OEM = 0x03      # 过滤萤石和 OEM 设备
SADP_ONLY_DISPLAY_OEM = 0xfffffffd  # 仅显示 OEM 设备
SADP_ONLY_DISPLAY_EZVIZ = 0xfffffffe  # 仅显示萤石设备


# ============================================================================
# 结构体定义 (对应 C 中的 struct，字段顺序和大小必须与 C 端完全一致)
# ============================================================================


class SADP_DEVICE_INFO(Structure):
    """
    SADP 设备信息结构体 - 通过设备发现回调获取的核心设备信息

    该结构体包含海康设备的基本网络参数和状态信息，是 SADP 协议
    设备搜索功能返回的主要数据类型。字段命名遵循海康 SDK 规范：
      sz*  = 字符串 (c_char 数组)
      dw*  = DWORD (32位无符号整数)
      w*   = WORD (16位无符号整数)
      by*  = BYTE (8位无符号整数)
      i*   = int (有符号整数)
    """
    _fields_ = [
        ("szSeries", c_char * 12),              # 设备系列 (如 "DS-", "iDS-")
        ("szSerialNO", c_char * 48),            # 设备序列号 (唯一标识)
        ("szMAC", c_char * 20),                 # MAC地址 (格式: "XX:XX:XX:XX:XX:XX")
        ("szIPv4Address", c_char * 16),         # IPv4地址 (格式: "192.168.1.100")
        ("szIPv4SubnetMask", c_char * 16),      # IPv4子网掩码
        ("dwDeviceType", DWORD),                # 设备类型编码 (如: 1504=某型号IPC)
        ("dwPort", DWORD),                      # SDK 通信端口 (默认 8000)
        ("dwNumberOfEncoders", DWORD),          # 编码器数量 (通道数)
        ("dwNumberOfHardDisk", DWORD),          # 硬盘数量
        ("szDeviceSoftwareVersion", c_char * 48),  # 设备软件版本号
        ("szDSPVersion", c_char * 48),          # DSP 版本号
        ("szBootTime", c_char * 48),            # 设备启动时间
        ("iResult", c_int),                     # 回调消息类型 (1=新增, 2=更新, 3=下线等)
        ("szDevDesc", c_char * 24),             # 设备描述信息
        ("szOEMinfo", c_char * 24),             # OEM 厂商信息
        ("szIPv4Gateway", c_char * 16),         # IPv4 默认网关
        ("szIPv6Address", c_char * 46),         # IPv6 地址
        ("szIPv6Gateway", c_char * 46),         # IPv6 默认网关
        ("byIPv6MaskLen", BYTE),                # IPv6 前缀长度 (如 64)
        ("bySupport", BYTE),                    # 支持能力位图
        ("byDhcpEnabled", BYTE),                # DHCP 是否启用 (0=禁用, 1=启用)
        ("byDeviceAbility", BYTE),              # 设备能力等级
        ("wHttpPort", WORD),                    # HTTP WEB 端口 (默认 80)
        ("wDigitalChannelNum", WORD),           # 数字通道数量
        ("szCmsIPv4", c_char * 16),             # CMS 服务器 IPv4 地址
        ("wCmsPort", WORD),                     # CMS 服务器端口
        ("byOEMCode", BYTE),                    # OEM 编码
        ("byActivated", BYTE),                  # 激活状态 (0=未激活, 1=已激活)
        ("szBaseDesc", c_char * 24),            # 基础描述信息
        ("bySupport1", BYTE),                   # 扩展支持标志1
        ("byHCPlatform", BYTE),                 # 是否支持 HCPlatform
        ("byEnableHCPlatform", BYTE),           # HCPlatform 是否启用
        ("byEZVIZCode", BYTE),                  # 萤石编码
        ("dwDetailOEMCode", DWORD),             # 细分 OEM 编码
        ("byModifyVerificationCode", BYTE),     # 验证码是否可修改
        ("byMaxBindNum", BYTE),                 # 最大绑定设备数量
        ("wOEMCommandPort", WORD),              # OEM 命令端口
        ("bySupportWifiRegion", BYTE),          # 是否支持 WiFi 区域设置
        ("byEnableWifiEnhancement", BYTE),      # WiFi 增强是否启用
        ("byWifiRegion", BYTE),                 # WiFi 区域编码
        ("bySupport2", BYTE),                   # 扩展支持标志2
    ]


class SADP_DEVICE_INFO_V40(Structure):
    """
    SADP V4.0 扩展设备信息结构体 (海康 newer 设备)

    在 SADP_DEVICE_INFO 基础上增加了 V4.0 特有字段，
    支持更多安全功能和网络配置信息。
    struSadpDeviceInfo 字段包含了完整的 V3.0 设备信息。
    """
    _fields_ = [
        ("struSadpDeviceInfo", SADP_DEVICE_INFO),    # 基础设备信息 (V3.0 完整结构)
        ("byLicensed", BYTE),                        # 授权状态
        ("bySystemMode", BYTE),                      # 系统模式
        ("byControllerType", BYTE),                  # 控制器类型
        ("szEhmoeVersion", c_char * 16),             # eHome 版本号
        ("bySpecificDeviceType", BYTE),              # 细分设备类型
        ("dwSDKOverTLSPort", DWORD),                 # SDK over TLS 端口
        ("bySecurityMode", BYTE),                    # 安全模式
        ("bySDKServerStatus", BYTE),                 # SDK 服务器状态
        ("bySDKOverTLSServerStatus", BYTE),          # SDK over TLS 服务器状态
        ("szUserName", c_char * (MAX_USERNAME_LEN + 1)),  # 当前登录用户名
        ("szWifiMAC", c_char * 20),                  # WiFi MAC 地址
        ("byDataFromMulticast", BYTE),               # 数据是否来自组播
        ("bySupportEzvizUnbind", BYTE),              # 是否支持萤石解绑
        ("bySupportCodeEncrypt", BYTE),              # 是否支持验证码加密
        ("bySupportPasswordResetType", BYTE),        # 是否支持密码重置方式选择
        ("byEZVIZBindStatus", BYTE),                 # 萤石绑定状态
        ("szPhysicalAccessVerification", c_char * 16),  # 物理访问验证码
        ("byRes", BYTE * 411),                       # 保留字段 (填充至固定大小)
    ]


class SADP_DEV_NET_PARAM(Structure):
    """
    设备网络参数结构体 - 用于修改设备网络配置

    用于 SADP_ModifyDeviceNetParam / SADP_ModifyDeviceNetParam_V40 函数，
    指定设备的新网络参数（IP地址、子网掩码、网关、端口等）。
    """
    _fields_ = [
        ("szIPv4Address", c_char * 16),      # IPv4 地址 (格式: "192.168.1.100")
        ("szIPv4SubNetMask", c_char * 16),   # IPv4 子网掩码 (格式: "255.255.255.0")
        ("szIPv4Gateway", c_char * 16),      # IPv4 默认网关
        ("szIPv6Address", c_char * 128),     # IPv6 地址
        ("szIPv6Gateway", c_char * 128),     # IPv6 默认网关
        ("wPort", WORD),                     # SDK 通信端口
        ("byIPv6MaskLen", BYTE),             # IPv6 前缀长度
        ("byDhcpEnable", BYTE),              # DHCP 启用标志 (0=禁用, 1=启用)
        ("wHttpPort", WORD),                 # HTTP WEB 端口
        ("dwSDKOverTLSPort", DWORD),         # SDK over TLS 端口
        ("byRes", BYTE * 122),               # 保留字段
    ]


class SADP_DEV_RET_NET_PARAM(Structure):
    """
    网络参数修改返回结构体 - 返回操作后的锁定状态

    用于 SADP_ModifyDeviceNetParam_V40 的输出参数，
    指示设备修改后的重试次数和剩余锁定时间。
    """
    _fields_ = [
        ("byRetryModifyTime", BYTE),    # 重试修改次数（修改失败时的已尝试次数）
        ("bySurplusLockTime", BYTE),    # 剩余锁定时间（分钟）
        ("byRes", BYTE * 126),          # 保留字段
    ]


class SADP_CMS_PARAM(Structure):
    """CMS (Center Management Server) 参数结构体 - 用于配置设备注册到 CMS 服务器"""
    _fields_ = [
        ("szPUID", c_char * 32),          # PUID (设备在 CMS 中的唯一标识)
        ("szPassword", c_char * 16),      # CMS 注册密码
        ("szCmsIPv4", c_char * 16),       # CMS 服务器 IPv4 地址
        ("szCmsIPv6", c_char * 128),      # CMS 服务器 IPv6 地址
        ("wCmsPort", WORD),               # CMS 服务器端口
        ("byRes", BYTE * 30),             # 保留字段
    ]


class SADP_SAFE_CODE(Structure):
    """设备验证码结构体 - 存储设备验证码及其长度"""
    _fields_ = [
        ("dwCodeSize", DWORD),                        # 验证码字符串的实际长度
        ("szDeviceCode", c_char * MAX_DEVICE_CODE),   # 设备验证码内容
        ("byRes", BYTE * 128),                        # 保留字段
    ]


class SADP_QR_CODES(Structure):
    """二维码数据结构体 - 存储密码重置二维码和关联的邮箱地址"""
    _fields_ = [
        ("dwCodeSize", DWORD),                             # 二维码数据长度
        ("dwMailBoxSize", DWORD),                          # 用户邮箱地址长度
        ("dwServiceMailBoxSize", DWORD),                   # 服务邮箱地址长度
        ("szQrCodes", c_char * MAX_QR_CODES),              # 二维码 Base64 数据
        ("szMailBoxAddr", c_char * MAX_MAILBOX_LEN),       # 用户邮箱地址
        ("szServiceMailBoxAddr", c_char * MAX_MAILBOX_LEN),  # 服务邮箱地址
        ("byRes", BYTE * 128),                             # 保留字段
    ]


class SADP_ENCRYPT_STRING(Structure):
    """加密字符串结构体 - 存储密码重置过程中设备返回的加密字符串"""
    _fields_ = [
        ("dwEncryptStringSize", DWORD),                          # 加密字符串长度
        ("szEncryptString", c_char * MAX_ENCRYPT_CODE),          # 加密字符串内容
        ("byRes", BYTE * 128),                                   # 保留字段
    ]


class SADP_RESET_PARAM(Structure):
    """密码重置参数结构体 (V3.0) - 用于 SADP_ResetPasswd"""
    _fields_ = [
        ("szCode", c_char * MAX_ENCRYPT_CODE),        # 加密验证码（从设备获取）
        ("szAuthFile", c_char * MAX_FILE_PATH_LEN),   # 认证文件路径（验证码文件）
        ("szPassword", c_char * MAX_PASS_LEN),        # 设置的新密码
        ("byEnableSyncIPCPW", BYTE),                  # 是否同步 IPC 密码 (NVR用)
        ("byRes", BYTE * 511),                        # 保留字段
    ]


class SADP_DISPLAY_OEM_CFG(Structure):
    """OEM 显示配置结构体 - 控制设备列表中的 OEM 显示过滤策略"""
    _fields_ = [
        ("dwDisplayOEM", DWORD),   # OEM 显示过滤类型 (对应 SADP_FILTER_* 常量)
        ("byRes", BYTE * 32),      # 保留字段
    ]


class SADP_TYPE_UNLOCK_CODE(Structure):
    """设备类型解锁码结构体 - 存储获取到的设备类型解锁码"""
    _fields_ = [
        ("dwCodeSize", DWORD),                                       # 解锁码长度
        ("szDeviceTypeUnlockCode", c_char * MAX_UNLOCK_CODE_RANDOM_LEN),  # 解锁码内容
        ("byRes", BYTE * 128),                                       # 保留字段
    ]


class SADP_CUSTOM_DEVICE_TYPE(Structure):
    """自定义设备类型结构体 - 用于设置设备的自定义类型密钥"""
    _fields_ = [
        ("dwCodeSize", DWORD),                                   # 密钥字符串长度
        ("szDeviceTypeSecretKey", c_char * MAX_UNLOCK_CODE_KEY),  # 自定义类型密钥
        ("byRes", BYTE * 128),                                   # 保留字段
    ]


class SADP_GUID_FILE_COND(Structure):
    """GUID 文件条件结构体 - 获取 GUID 时需提供设备当前密码"""
    _fields_ = [
        ("szPassword", c_char * MAX_PASS_LEN),  # 设备当前密码（用于验证身份）
        ("byRes", BYTE * 128),                  # 保留字段
    ]


class SADP_GUID_FILE(Structure):
    """GUID 文件结构体 - 存储获取到的密码重置 GUID 信息"""
    _fields_ = [
        ("dwGUIDSize", DWORD),              # GUID 字符串长度
        ("szGUID", c_char * MAX_GUID_LEN),  # GUID 内容（用于生成重置文件）
        ("byRetryGUIDTime", BYTE),          # 重试 GUID 获取次数
        ("bySurplusLockTime", BYTE),        # 剩余锁定时间（分钟）
        ("byRes", BYTE * 254),             # 保留字段
    ]


class SADP_SINGLE_SECURITY_QUESTION_CFG(Structure):
    """单条安全问题配置结构体 - 存储一条安全问题及其答案"""
    _fields_ = [
        ("dwSize", DWORD),                         # 本结构体大小
        ("dwId", DWORD),                           # 安全问题编号 (1-32)
        ("szAnswer", c_char * MAX_ANSWER_LEN),     # 安全问题的答案
        ("byMark", BYTE),                          # 标记位
        ("byRes", BYTE * 127),                     # 保留字段
    ]


class SADP_SECURITY_QUESTION_CFG(Structure):
    """安全问题组配置结构体 - 包含多条安全问题答案和操作密码"""
    _fields_ = [
        ("dwSize", DWORD),                                                              # 本结构体大小
        ("struSecurityQuestion", SADP_SINGLE_SECURITY_QUESTION_CFG * MAX_QUESTION_LIST_LEN),  # 安全问题列表
        ("szPassword", c_char * MAX_PASS_LEN),                                          # 设备当前密码（验证身份）
        ("byRes", BYTE * 512),                                                          # 保留字段
    ]


class SADP_SECURITY_QUESTION(Structure):
    """安全问题返回状态结构体 - 返回答案错误后的重试和锁定信息"""
    _fields_ = [
        ("byRetryAnswerTime", BYTE),    # 已尝试回答错误次数
        ("bySurplusLockTime", BYTE),    # 剩余锁定时间（分钟）
        ("byRes", BYTE * 254),          # 保留字段
    ]


class SADP_RESET_PARAM_V40(Structure):
    """密码重置参数结构体 (V4.0) - 用于 SADP_ResetPasswd_V40，支持多种重置方式"""
    _fields_ = [
        ("dwSize", DWORD),                              # 本结构体大小
        ("byResetType", BYTE),                          # 重置类型 (0=验证码, 1=GUID, 2=安全问题)
        ("byEnableSyncIPCPW", BYTE),                    # 是否同步 IPC 密码
        ("byRes2", BYTE * 2),                           # 保留字段2
        ("szPassword", c_char * MAX_PASS_LEN),          # 要设置的新密码
        ("szCode", c_char * MAX_ENCRYPT_CODE),          # 加密验证码（验证码方式）
        ("szAuthFile", c_char * MAX_FILE_PATH_LEN),     # 认证文件路径（GUID方式）
        ("szGUID", c_char * MAX_GUID_LEN),              # GUID 字符串（GUID方式）
        ("struSecurityQuestionCfg", SADP_SECURITY_QUESTION_CFG),  # 安全问题配置（安全问题方式）
        ("byRes", BYTE * 512),                          # 保留字段
    ]


class SADP_RET_RESET_PARAM_V40(Structure):
    """V4.0 密码重置返回结构体 - 返回操作后的重试次数和锁定状态"""
    _fields_ = [
        ("byRetryGUIDTime", BYTE),     # 已重试次数
        ("bySurplusLockTime", BYTE),   # 剩余锁定时间（分钟）
        ("bRetryTimeValid", BYTE),     # 重试次数是否有效 (0=无效, 1=有效)
        ("bLockTimeValid", BYTE),      # 锁定时间是否有效 (0=无效, 1=有效)
        ("byRes", BYTE * 252),         # 保留字段
    ]


class SADP_HCPLATFORM_STATUS_INFO(Structure):
    """HCPlatform 平台状态配置结构体 - 用于启用/禁用海康云平台"""
    _fields_ = [
        ("dwSize", DWORD),                  # 本结构体大小
        ("byEnableHCPlatform", BYTE),       # 是否启用 HCPlatform (0=禁用, 1=启用)
        ("byRes", BYTE * 3),                # 保留字段
        ("szPassword", c_char * MAX_PASS_LEN),  # 设备当前密码（验证身份）
        ("byRes2", BYTE * 128),             # 保留字段2
    ]


class SADP_USER_MAILBOX(Structure):
    """用户邮箱配置结构体 - 用于设置设备关联的用户邮箱（密码重置用）"""
    _fields_ = [
        ("dwSize", DWORD),                             # 本结构体大小
        ("szPassword", c_char * MAX_PASS_LEN),         # 设备当前密码
        ("szMailBoxAddr", c_char * MAX_MAILBOX_LEN),   # 用户邮箱地址
        ("byRes", BYTE * 128),                         # 保留字段
    ]


class SADP_VERIFICATION_CODE_INFO(Structure):
    """验证码信息结构体 - 用于设置设备验证码（修改设备安全验证码）"""
    _fields_ = [
        ("dwSize", DWORD),                                          # 本结构体大小
        ("szVerificationCode", c_char * SADP_MAX_VERIFICATION_CODE_LEN),  # 新的验证码
        ("szPassword", c_char * MAX_PASS_LEN),                      # 设备当前密码
        ("byRes", BYTE * 128),                                      # 保留字段
    ]


class SADP_INACTIVE_INFO(Structure):
    """设备未激活信息结构体 - 用于恢复未激活设备时提供当前密码"""
    _fields_ = [
        ("dwSize", DWORD),                          # 本结构体大小
        ("szPassword", c_char * MAX_PASS_LEN),      # 设备出厂密码
    ]


class SADP_DEV_LOCK_INFO(Structure):
    """设备锁定信息结构体 - 返回设备当前锁定状态（操作失败时获取）"""
    _fields_ = [
        ("byRetryTime", BYTE),          # 已重试次数
        ("bySurplusLockTime", BYTE),    # 剩余锁定时间（分钟）
        ("byRes", BYTE * 126),          # 保留字段
    ]


class SADP_BIND_INFO(Structure):
    """单条设备绑定信息结构体 - 记录一台设备的序列号和绑定状态"""
    _fields_ = [
        ("szSerialNO", c_char * SADP_MAX_SERIALNO_LEN),  # 设备序列号
        ("byiBind", BYTE),                               # 绑定状态 (0=未绑定, 1=已绑定)
        ("byRes", BYTE * 127),                           # 保留字段
    ]


class SADP_BIND_LIST(Structure):
    """绑定列表结构体 - 管理设备与 NVR 的绑定关系（最大32台）"""
    _fields_ = [
        ("struBindInfo", SADP_BIND_INFO * SADP_MAX_BIND_NUM),  # 绑定信息列表
        ("szPassword", c_char * MAX_PASS_LEN),                 # NVR 当前密码
        ("byUnbindAll", BYTE),                                 # 是否解绑所有 (0=否, 1=全部解绑)
        ("byRes", BYTE * 127),                                 # 保留字段
    ]


class SADP_WIFI_REGION_INFO(Structure):
    """WiFi 区域配置结构体 - 设置设备 WiFi 区域和增强模式"""
    _fields_ = [
        ("byMode", BYTE),                       # 模式选择
        ("byWifiRegion", BYTE),                 # WiFi 区域编码 (各国无线电规范不同)
        ("byWifiEnhancementEnabled", BYTE),     # WiFi 信号增强是否启用
        ("byRes", BYTE),                        # 保留字段
        ("szPassword", c_char * MAX_PASS_LEN),  # 设备当前密码
        ("byRes2", BYTE * 128),                 # 保留字段2
    ]


class SADP_CHANNEL_DEFAULT_PASSWORD(Structure):
    """通道默认密码结构体 - 为 NVR 通道设置统一的默认密码"""
    _fields_ = [
        ("szPassword", c_char * MAX_PASS_LEN),              # NVR 当前密码
        ("szChannelDefaultPassword", c_char * MAX_PASS_LEN), # 通道默认密码
        ("byRes", BYTE * 128),                              # 保留字段
    ]


class SADP_SELF_CHECK_STATE(Structure):
    """设备自检状态结构体 - 返回设备硬件、存储、网络等自检信息"""
    _fields_ = [
        ("dwSize", DWORD),                     # 本结构体大小
        ("dwTotalDisk", c_int),                # 硬盘总数
        ("dwGoodDisk", c_int),                 # 健康硬盘数量
        ("szCPU", c_char * MAX_CPU_LEN),       # CPU 信息字符串
        ("szMemory", c_char * MAX_MEMORY_LEN), # 内存信息字符串
        ("byProgress", BYTE),                  # 自检进度百分比 (0-100)
        ("byTemperatureState", BYTE),          # 温度状态 (0=正常, 1=过高)
        ("byFanState", BYTE),                  # 风扇状态 (0=正常, 1=异常)
        ("byPowerState", BYTE),                # 电源状态 (0=正常, 1=异常)
        ("bySASConnectState", BYTE),           # SAS 连接状态
        ("byTotalNetworkPort", c_char),        # 网络端口总数
        ("byConnectNetworkPort", c_char),      # 已连接网络端口数量
        ("byRes", BYTE * 129),                 # 保留字段
    ]


class SADP_EHOME_ENABLE_PARAM(Structure):
    """eHome 协议启用参数结构体 - 配置设备通过 eHome 协议接入平台"""
    _fields_ = [
        ("dwSize", DWORD),                          # 本结构体大小
        ("szDevID", c_char * MAX_PASS_LEN),        # eHome 设备 ID
        ("szEhomeKey", c_char * MAX_PASS_LEN),      # eHome 连接密钥
        ("szPassword", c_char * MAX_PASS_LEN),      # 设备当前密码
        ("byRes", BYTE * 64),                       # 保留字段
    ]


class SADP_WIFI_CONFIG_PARAM(Structure):
    """WiFi 配置参数结构体 - 配置设备连接指定 WiFi 网络"""
    _fields_ = [
        ("dwSize", DWORD),                                      # 本结构体大小
        ("szSSID", c_char * SADP_MAX_SERIALNO_LEN),            # WiFi 名称 (SSID)
        ("szPassword", c_char * SADP_MAX_SERIALNO_LEN),        # WiFi 密码
        ("byWifiMode", BYTE),                                   # WiFi 模式
        ("byRes", BYTE * 64),                                   # 保留字段
    ]


class SADP_PASSWORD_RESET_TYPE_PARAM(Structure):
    """密码重置方式参数结构体 - 配置设备支持的密码重置方式"""
    _fields_ = [
        ("dwSize", DWORD),                         # 本结构体大小
        ("byEnable", BYTE),                        # 总开关 (0=禁用所有, 1=启用)
        ("byGuidEnabled", BYTE),                   # GUID 文件重置方式
        ("bySecurityQuestionEnabled", BYTE),       # 安全问题重置方式
        ("bySecurityMailBoxEnabled", BYTE),        # 安全邮箱重置方式
        ("byHikConnectEnabled", BYTE),             # Hik-Connect 重置方式
        ("byRes1", BYTE * 3),                      # 保留字段1
        ("byRes", BYTE * 64),                      # 保留字段
    ]


# ============================================================================
# 回调函数类型定义
# ============================================================================
PDEVICE_FIND_CALLBACK = CALLBACK(None, POINTER(SADP_DEVICE_INFO), c_void_p)
PDEVICE_FIND_CALLBACK_V40 = CALLBACK(None, POINTER(SADP_DEVICE_INFO_V40), c_void_p)


# ============================================================================
# 动态库加载及接口封装类
# ============================================================================
class SADPTool:
    """
    SADP SDK 封装类

    封装海康 SADP.dll / libsadp.so 动态库的全部接口函数，
    提供设备搜索、网络配置修改、激活、密码重置等功能。

    用法:
        tool = SADPTool("Sadp.dll")
        tool.start_v30(callback, 1, None)  # 启动设备搜索
        tool.stop()                         # 停止搜索
    """

    def __init__(self, dll_path):
        """
        初始化并加载 DLL / SO 动态库
        :param dll_path: SADP 库的路径 (如 'Sadp.dll' 或 './libsadp.so')
        """
        # 根据操作系统选择加载方式: Windows 用 WinDLL(stdcall), Linux 用 CDLL(cdecl)
        if sys.platform.startswith('win'):
            self.dll = ctypes.WinDLL(dll_path)
        else:
            self.dll = ctypes.CDLL(dll_path)

        # 配置所有 DLL 函数的参数类型和返回值类型
        self._setup_functions()

    def _setup_functions(self):
        """
        配置所有 DLL 导出函数的参数类型(argtypes)和返回值类型(restype)
        这是 ctypes 正确调用 C 函数的关键步骤，确保类型安全
        """
        # ---- 设备搜索控制 ----
        # SADP_Start_V30: 启动设备搜索 (V3.0 回调)
        self.dll.SADP_Start_V30.argtypes = [PDEVICE_FIND_CALLBACK, c_int, c_void_p]
        self.dll.SADP_Start_V30.restype = BOOL

        # SADP_Start_V40: 启动设备搜索 (V4.0 回调，支持更多字段)
        self.dll.SADP_Start_V40.argtypes = [PDEVICE_FIND_CALLBACK_V40, c_int, c_void_p]
        self.dll.SADP_Start_V40.restype = BOOL

        # SADP_SendInquiry: 发送一次设备搜索广播查询
        self.dll.SADP_SendInquiry.argtypes = []
        self.dll.SADP_SendInquiry.restype = BOOL

        # SADP_Stop: 停止设备搜索
        self.dll.SADP_Stop.argtypes = []
        self.dll.SADP_Stop.restype = BOOL

        # SADP_Clearup: 清理 SADP 资源
        self.dll.SADP_Clearup.argtypes = []
        self.dll.SADP_Clearup.restype = BOOL

        # ---- 网络参数修改 ----
        # SADP_ModifyDeviceNetParam: 修改设备网络参数 (V3.0)
        self.dll.SADP_ModifyDeviceNetParam.argtypes = [c_char_p, c_char_p, POINTER(SADP_DEV_NET_PARAM)]
        self.dll.SADP_ModifyDeviceNetParam.restype = BOOL

        # SADP_ModifyDeviceNetParam_V40: 修改设备网络参数 (V4.0，返回锁定状态)
        self.dll.SADP_ModifyDeviceNetParam_V40.argtypes = [c_char_p, c_char_p, POINTER(SADP_DEV_NET_PARAM),
                                                           POINTER(SADP_DEV_RET_NET_PARAM), DWORD]
        self.dll.SADP_ModifyDeviceNetParam_V40.restype = BOOL

        # ---- 设备激活与密码重置 ----
        # SADP_ActivateDevice: 激活设备（设置初始密码）
        self.dll.SADP_ActivateDevice.argtypes = [c_char_p, c_char_p]
        self.dll.SADP_ActivateDevice.restype = BOOL

        # SADP_ResetPasswd: 重置密码 (V3.0 方式)
        self.dll.SADP_ResetPasswd.argtypes = [c_char_p, POINTER(SADP_RESET_PARAM)]
        self.dll.SADP_ResetPasswd.restype = BOOL

        # SADP_ResetPasswd_V40: 重置密码 (V4.0 方式，支持多种重置类型)
        self.dll.SADP_ResetPasswd_V40.argtypes = [c_char_p, POINTER(SADP_RESET_PARAM_V40),
                                                  POINTER(SADP_RET_RESET_PARAM_V40)]
        self.dll.SADP_ResetPasswd_V40.restype = BOOL

        # SADP_ResetDefaultPasswd: 恢复默认密码
        self.dll.SADP_ResetDefaultPasswd.argtypes = [c_char_p, c_char_p]
        self.dll.SADP_ResetDefaultPasswd.restype = BOOL

        # ---- 设备配置获取/设置 ----
        # SADP_GetDeviceConfig: 获取设备配置（如验证码、加密字符串等）
        self.dll.SADP_GetDeviceConfig.argtypes = [c_char_p, DWORD, c_void_p, DWORD, c_void_p, DWORD]
        self.dll.SADP_GetDeviceConfig.restype = BOOL

        # SADP_SetDeviceConfig: 设置设备配置
        self.dll.SADP_SetDeviceConfig.argtypes = [c_char_p, DWORD, c_void_p, DWORD, c_void_p, DWORD]
        self.dll.SADP_SetDeviceConfig.restype = BOOL

        # SADP_GetDeviceConfigByMAC: 通过 MAC 地址获取设备配置
        self.dll.SADP_GetDeviceConfigByMAC.argtypes = [c_char_p, DWORD, c_void_p, DWORD, c_void_p, DWORD]
        self.dll.SADP_GetDeviceConfigByMAC.restype = BOOL

        # ---- CMS 注册配置 ----
        # SADP_SetCMSInfo: 设置设备注册到 CMS 服务器的参数
        self.dll.SADP_SetCMSInfo.argtypes = [c_char_p, POINTER(SADP_CMS_PARAM)]
        self.dll.SADP_SetCMSInfo.restype = BOOL

        # ---- 其他功能 ----
        # SADP_GetSadpVersion: 获取 SADP SDK 版本号
        self.dll.SADP_GetSadpVersion.argtypes = []
        self.dll.SADP_GetSadpVersion.restype = DWORD

        # SADP_SetLogToFile: 设置日志输出到文件
        self.dll.SADP_SetLogToFile.argtypes = [c_int, c_char_p, c_int]
        self.dll.SADP_SetLogToFile.restype = BOOL

        # SADP_GetLastError: 获取最后一次操作的错误码
        self.dll.SADP_GetLastError.argtypes = []
        self.dll.SADP_GetLastError.restype = DWORD

        # SADP_SetAutoRequestInterval: 设置自动搜索的时间间隔
        self.dll.SADP_SetAutoRequestInterval.argtypes = [DWORD]
        self.dll.SADP_SetAutoRequestInterval.restype = None

        # SADP_SetDeviceFilterRule: 设置设备过滤规则（过滤萤石/OEM设备）
        self.dll.SADP_SetDeviceFilterRule.argtypes = [DWORD, c_void_p, DWORD]
        self.dll.SADP_SetDeviceFilterRule.restype = BOOL

        # SADP_SendLamp: 发送设备定位闪烁命令（让设备指示灯闪烁便于定位）
        self.dll.SADP_SendLamp.argtypes = [c_char_p, DWORD]
        self.dll.SADP_SendLamp.restype = BOOL

