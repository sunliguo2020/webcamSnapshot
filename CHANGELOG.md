# 更新日志

## 2026-05-27

### 修复
- **修复 PyInstaller 打包后 exe 无法运行的问题**
  - 修复 `logging.config.fileConfig()` 在打包环境中找不到 `logging.conf` 文件的问题
  - `capture_tk.py`：使用 `sys._MEIPASS` 获取 PyInstaller 打包后的临时解压路径，正确拼接配置文件路径
  - `main.py`：添加 `getattr(sys, 'frozen', False)` 判断，根据运行环境选择正确的配置文件路径
  - `make.py`：添加 `--clean` 和 `--noupx` 打包参数，避免缓存和 UPX 压缩问题
- **修复打包后缺少依赖模块的问题**
  - 安装缺失的 `zeep` 模块（SOAP 客户端库）
  - 安装缺失的 `onvif-zeep` 模块（ONVIF 协议支持）

## 2024-08-11

### 修复
- 修复统计结果时，判断错误。

## 2024-08-10

### 修复
- 修复了电脑截图的情况下，打开文件夹按钮失效的问题。
