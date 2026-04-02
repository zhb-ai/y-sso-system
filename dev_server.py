#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
开发服务器启动脚本
用于在IDE中直接运行和调试FastAPI应用
支持多种启动参数配置

启动前自动检测并清理占用端口的残留进程，避免端口冲突导致请求 pending。
"""

import uvicorn
import argparse
import subprocess
import signal
import sys
import os
import time

# 获取当前脚本所在目录，并添加到Python路径中
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 确保当前工作目录正确设置为y-sso-system目录
os.chdir(current_dir)


def kill_port_occupants(port: int) -> int:
    """检测并杀掉占用指定端口的所有进程（排除自身），返回杀掉的进程数"""
    my_pid = os.getpid()
    killed = 0

    try:
        result = subprocess.run(
            ["netstat", "-ano"],
            capture_output=True, text=True, timeout=5,
        )
    except Exception:
        return 0

    pids_to_kill = set()
    for line in result.stdout.splitlines():
        # 匹配 LISTENING 状态且端口匹配的行
        if f":{port}" not in line or "LISTENING" not in line:
            continue
        parts = line.split()
        if len(parts) < 5:
            continue
        # 本地地址格式: 127.0.0.1:8000 或 0.0.0.0:8000
        local_addr = parts[1]
        if not local_addr.endswith(f":{port}"):
            continue
        try:
            pid = int(parts[-1])
        except ValueError:
            continue
        if pid > 0 and pid != my_pid:
            pids_to_kill.add(pid)

    for pid in pids_to_kill:
        try:
            # /T 杀掉子进程树，/F 强制终止
            subprocess.run(
                ["taskkill", "/PID", str(pid), "/F", "/T"],
                capture_output=True, timeout=5,
            )
            killed += 1
            print(f"  已终止残留进程 PID={pid}")
        except Exception:
            pass

    return killed


def main():
    parser = argparse.ArgumentParser(description="单点登录系统API开发服务器")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="绑定的主机地址 (默认: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="监听的端口号 (默认: 8000)")
    parser.add_argument("--reload", action="store_true", default=True, help="启用自动重载 (开发模式)")
    parser.add_argument("--workers", type=int, default=1, help="工作进程数 (默认: 1)")
    parser.add_argument("--debug", action="store_true", default=True, help="启用调试模式")
    parser.add_argument("--log-level", type=str, default="debug", choices=["critical", "error", "warning", "info", "debug"], help="日志级别")

    args = parser.parse_args()

    # ---- 启动前清理 ----
    print(f"检查端口 {args.port} 是否被占用...")
    killed = kill_port_occupants(args.port)
    if killed:
        print(f"已清理 {killed} 个残留进程，等待端口释放...")
        time.sleep(1)
    else:
        print(f"端口 {args.port} 空闲")

    # ---- 启动信息 ----
    print("=" * 50)
    print("单点登录系统API开发服务器启动")
    print("=" * 50)
    print(f"主机地址: {args.host}")
    print(f"端口: {args.port}")
    print(f"自动重载: {'是' if args.reload else '否'}")
    print(f"工作进程: {args.workers}")
    print(f"调试模式: {'是' if args.debug else '否'}")
    print(f"日志级别: {args.log_level}")
    print("=" * 50)

    # 设置环境变量
    os.environ.setdefault("DEBUG", str(args.debug).lower())

    try:
        uvicorn.run(
            "app.main:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
            workers=args.workers,
            log_level=args.log_level
        )
    except KeyboardInterrupt:
        print("\n服务器已停止")
    except Exception as e:
        print(f"启动服务器时发生错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()