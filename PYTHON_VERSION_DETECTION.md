# Python 3.10 版本检测优化说明

## 优化内容

`run_project.py` 中的Python版本检测功能，确保系统中存在Python 3.10，以便`uv`能够正确运行服务端程序。

## 设计理念

**重要**: 运行 `run_project.py` 脚本本身使用什么Python版本并不重要，关键是确保系统中存在Python 3.10。因为：

1. `pyproject.toml` 已指定 `requires-python = "==3.10.*"`
2. `uv run` 命令会自动使用Python 3.10来运行服务端程序（api.py, pet.py, gpt_sovits/api_v2.py）
3. 只要系统中有Python 3.10，`uv`就能找到并使用它

## 主要改进

### 1. 智能检测机制

新增 `find_python310()` 函数，会在系统的常见位置搜索Python 3.10：

#### macOS
- `/opt/homebrew/bin/python3.10` (Homebrew ARM64默认路径)
- `/opt/homebrew/opt/python@3.10/bin/python3.10` (Homebrew opt路径)
- `/opt/homebrew/Cellar/python@3.10/*/bin/python3.10` (Homebrew Cellar路径，支持通配符)
- `/usr/local/bin/python3.10` (Homebrew x86_64路径)
- `/usr/local/opt/python@3.10/bin/python3.10`
- `/Library/Frameworks/Python.framework/Versions/3.10/bin/python3.10` (官方安装包路径)

#### Windows
- `C:\Python310\python.exe`
- `C:\Program Files\Python310\python.exe`
- `C:\Program Files (x86)\Python310\python.exe`
- `~\AppData\Local\Programs\Python\Python310\python.exe` (Windows Store安装路径)

#### Linux
- `/usr/bin/python3.10`
- `/usr/local/bin/python3.10`
- `~/.pyenv/versions/3.10.*/bin/python` (pyenv安装路径，支持通配符)

#### 通用
- `python3.10` (环境变量PATH中的python3.10)

### 2. 版本验证

新增 `verify_python310()` 函数，会实际执行Python解释器并验证版本号，确保找到的是真正的Python 3.10（而不只是文件存在）。

### 3. 友好的提示信息

脚本会根据检测结果给出清晰的提示：

- **找到Python 3.10**:
  - 如果当前运行的就是Python 3.10，显示确认信息
  - 如果当前运行的是其他版本，说明找到了Python 3.10，并告知服务将通过`uv`使用Python 3.10运行

- **未找到Python 3.10**: 根据操作系统给出具体的安装指引：

- **macOS**: `brew install python@3.10`
- **Windows**: 提供官方下载链接
- **Linux**: 提示使用系统包管理器安装

## 使用示例

```bash
# 可以使用任何版本的Python运行脚本
python3 run_project.py
# 或
python3.13 run_project.py

# 输出示例（当前Python是3.13，但系统有3.10）:
# ✅ [2025-10-09 23:26:30] [SUCCESS] 系统中找到Python 3.10: /opt/homebrew/bin/python3.10
# ℹ️  [2025-10-09 23:26:30] [INFO] 当前运行版本为 3.13.7，但服务将通过uv使用Python 3.10运行
# (脚本继续运行，并使用uv启动服务，uv会自动使用Python 3.10)

# 如果系统中没有Python 3.10:
# ❌ [2025-10-09 23:26:30] [ERROR] 系统中未找到Python 3.10
# ⚠️  [2025-10-09 23:26:30] [ERROR] 项目依赖需要Python 3.10，请先安装
# 💡 [2025-10-09 23:26:30] [INFO] macOS安装命令: brew install python@3.10
# (脚本退出)
```

## 技术细节

### 通配符支持

检测函数支持路径通配符，可以处理Homebrew Cellar路径中的版本号：

```python
"/opt/homebrew/Cellar/python@3.10/*/bin/python3.10"
# 会匹配如: /opt/homebrew/Cellar/python@3.10/3.10.14/bin/python3.10
```

### 超时保护

版本验证函数设置了5秒超时，防止挂起：

```python
subprocess.run(..., timeout=5)
```

### uv自动选择Python版本

由于 `pyproject.toml` 中指定了：
```toml
[project]
requires-python = "==3.10.*"
```

当执行 `uv run python api.py` 等命令时，`uv` 会自动：
1. 在系统中查找Python 3.10
2. 创建或使用基于Python 3.10的虚拟环境
3. 在该环境中运行服务端程序

## 优势

1. **灵活性强**: 用户可以用任何Python版本运行 `run_project.py`
2. **自动化**: `uv` 自动处理Python版本，无需手动干预
3. **健壮性强**: 支持多种Python 3.10安装方式和路径
4. **跨平台**: 同时支持macOS、Windows、Linux
5. **验证严格**: 不仅检查路径，还实际执行Python验证版本号
6. **错误提示清晰**: 未找到时提供明确的安装指引

## 工作流程

1. 用户运行 `python3 run_project.py`（可以是任何Python版本）
2. 脚本检测系统中是否存在Python 3.10
3. 如果不存在，提示安装并退出
4. 如果存在，继续执行配置和启动流程
5. 执行 `uv run python api.py` 等命令时，`uv` 自动使用Python 3.10

## 测试结果

在macOS上测试通过：

```
当前Python版本: 3.13.7
系统中找到Python 3.10: /opt/homebrew/bin/python3.10
✅ 验证成功
```

脚本能够正确识别系统中的Python 3.10，确保服务端程序能够在正确的Python版本下运行。

