# 开发服务器启动说明

## 前置条件

在启动开发服务器之前，请确保已完成以下步骤：

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 初始化数据库（首次启动时执行）
```bash
python init_db.py
```

## 使用方法

### 1. 基本启动
```bash
python dev_server.py
```

### 2. 指定主机和端口
```bash
python dev_server.py --host 0.0.0.0 --port 8001
```

### 3. 禁用自动重载（模拟生产环境）
```bash
python dev_server.py --reload=False
```

### 4. 调试模式
```bash
python dev_server.py --debug --log-level debug
```

### 5. 完整配置启动
```bash
python dev_server.py --host 127.0.0.1 --port 8001 --reload --debug --log-level info
```

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--host` | 绑定的主机地址 | 127.0.0.1 |
| `--port` | 监听的端口号 | 8000 |
| `--reload` | 启用自动重载（代码修改后自动重启） | True |
| `--workers` | 工作进程数 | 1 |
| `--debug` | 启用调试模式 | True |
| `--log-level` | 日志级别 | debug |

**日志级别可选值**：critical, error, warning, info, debug

## 在IDE中调试

您可以在支持Python调试的IDE（如PyCharm、VS Code等）中直接运行或调试 `dev_server.py` 文件。
只需要在IDE中打开该文件并点击"运行"或"调试"按钮即可。

## 访问服务

服务启动成功后，可以访问：
- **API 文档**：http://localhost:8000/docs
- **健康检查**：http://localhost:8000/health

## 注意事项

1. 确保已安装所有依赖包：`pip install -r requirements.txt`
2. 确保数据库文件存在，如不存在请先运行初始化脚本：`python init_db.py`
3. 在生产环境中不要使用 `--reload` 参数
4. 默认端口为 8000，如需修改请使用 `--port` 参数
5. 详细的配置说明请参考：[配置指南](CONFIG_GUIDE.md)
