# 更新日志

## 2026-05-27

### 新增
- **新增 CSV 文件预览功能**
  - 在 CSV 文件路径旁添加"预览"按钮
  - 使用 Canvas 绘制带边框的表格，支持序号列和动态列宽
  - 显示文件路径、记录数和列数信息
- **新增截图暂停/继续功能**
  - 截图开始后显示暂停按钮，点击后等待当前任务完成再暂停
  - 暂停后按钮变为"继续"，点击恢复截图任务
  - 使用 `pause_event` 和 `is_paused` 标志控制暂停状态
- **新增摄像头类型为空校验**
  - 未选择摄像头类型时弹出警告提示

### 优化
- **优化 CSV 预览表格显示**
  - 改用 Canvas 绘制表格，每个单元格独立绘制边框
  - 根据数据内容动态计算列宽
  - 添加序号列，从 1 开始编号
- **截图开始后预览按钮保持可用**
  - 只禁用 CSV 浏览按钮，预览按钮可随时查看 CSV 内容

### 修复
- **修复暂停功能无效的问题**
  - 暂停时调用 `pause_event.clear()` 使 `wait()` 阻塞
  - 去掉 `ThreadPoolExecutor`，改用直接循环调用，确保暂停后立即停止
- **修复 `mylogger/setlogger.py` 创建 `log` 目录的问题**
  - 将日志路径改为 `logs/` 目录，与 `utils/log_config.py` 保持一致
- **删除 USB 截图开始时的弹窗**
  - USB 截图（电脑摄像头）开始后不再弹出提示框

### 重构
- **重构 `capture_tk.py`，将功能性函数抽离到独立模块**
  - 创建 `utils/log_config.py` - 日志配置模块，统一管理日志配置
  - 将 `validate_csv_file()` 移到 `utils/tool.py`
  - 将 `build_save_dir()` 移到 `utils/other_utils.py`
  - 将 `batch_capture_computer_cameras()` 移到 `utils/capture_pool.py`
  - 将 `poll_gui_queue()` 移到 `utils/log_utils.py`
  - 将 `capture_tk.py` 改造成 `CameraSnapshotApp` 类，提高代码可维护性

### 优化
- **优化 UI 布局和样式**
  - 窗口尺寸调整为 720x520，禁止调整大小
  - 添加标题和副标题说明
  - 统一字体和颜色风格（微软雅黑、扁平化按钮）
  - 按钮使用图标符号（▶ 📂 🗑）和颜色区分功能
  - 添加分隔线，优化布局间距
  - 修复 LogWidget 中 grid/pack 混用问题
  - 提取辅助方法 `_create_label/_create_entry/_create_button` 减少重复代码

### 修复
- **修复 PyInstaller 打包后 exe 无法运行的问题**
  - 修复 `logging.config.fileConfig()` 在打包环境中找不到 `logging.conf` 文件的问题
  - `capture_tk.py`：使用 `sys._MEIPASS` 获取 PyInstaller 打包后的临时解压路径，正确拼接配置文件路径
  - `main.py`：添加 `getattr(sys, 'frozen', False)` 判断，根据运行环境选择正确的配置文件路径
  - `make.py`：添加 `--clean` 和 `--noupx` 打包参数，避免缓存和 UPX 压缩问题
- **修复打包后缺少依赖模块的问题**
  - 安装缺失的 `zeep` 模块（SOAP 客户端库）
  - 安装缺失的 `onvif-zeep` 模块（ONVIF 协议支持）
- **修复打包后日志文件路径错误的问题**
  - `utils/log_config.py`：改用 `sys.executable` 获取 exe 所在目录，确保日志文件创建在 exe 旁边的 `logs/` 目录下
  - 清除 `mylogger.setlogger` 提前配置的旧 handlers，避免日志写入 `log/` 目录
  - `main.py`：使用 `--paths` 参数指定项目根目录，解决 PyInstaller 找不到 `utils` 包的问题

## 2024-08-11

### 修复
- 修复统计结果时，判断错误。

## 2024-08-10

### 修复
- 修复了电脑截图的情况下，打开文件夹按钮失效的问题。
