#!/usr/bin/env bash
# y-sso-system 生产启停。只管理本目录的 API 进程。
# 不管理 nginx，也不管理其他目录里的 Python 服务。
#
#   sudo bash start_server.sh start
#   sudo bash start_server.sh stop
#   sudo bash start_server.sh restart
#   sudo bash start_server.sh status
#
# 警告: 现有生产进程没有 pid 文件。
# start 和 restart 会先停止本目录中监听 8000 的 uvicorn，再启动新进程。
# 生产服务仍需保持当前进程时，不要执行 start、stop、restart。
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${ROOT}"

PY="/root/conda/envs/yafo_sso/bin/python"
RUN_DIR="${ROOT}/run"
API_PID_FILE="${RUN_DIR}/y-sso-api.pid"
PORT=8000
HOST="0.0.0.0"

usage() {
  echo "用法: sudo bash start_server.sh {start|stop|restart|status}" >&2
  exit 1
}

require_root() {
  if [[ "${EUID}" -ne 0 ]]; then
    echo "错误: 当前用户不是 root。" >&2
    echo "原因: 部署目录和 conda 环境属于 root，现有进程也以 root 运行。" >&2
    echo "处理: 使用 sudo bash start_server.sh ${1:-status}。" >&2
    exit 1
  fi
}

require_python() {
  if [[ ! -x "${PY}" ]]; then
    echo "错误: 未找到可执行文件 ${PY}。" >&2
    echo "原因: 当前生产进程使用这个 conda 解释器。" >&2
    echo "处理: 确认解释器存在后，再执行本脚本。" >&2
    exit 1
  fi
}

require_pgrep() {
  if ! command -v pgrep >/dev/null 2>&1; then
    echo "错误: 未找到 pgrep。" >&2
    echo "原因: 本脚本用 pgrep 识别 uvicorn 进程。" >&2
    echo "处理: 安装 procps 后再执行本脚本。" >&2
    exit 1
  fi
}

is_running() {
  local pid="$1"
  [[ -n "${pid}" ]] && kill -0 "${pid}" 2>/dev/null
}

wait_stopped() {
  local pid="$1"
  local i
  for i in $(seq 1 20); do
    is_running "${pid}" || return 0
    sleep 0.5
  done
  kill -9 "${pid}" 2>/dev/null || true
}

api_cmdline_matches() {
  local pid="$1"
  local cmd cwd
  cmd="$(tr '\0' ' ' < "/proc/${pid}/cmdline" 2>/dev/null || true)"
  [[ "${cmd}" == *"uvicorn app.main:app"* ]] || return 1
  [[ "${cmd}" == *"--port ${PORT}"* || "${cmd}" == *"--port=${PORT}"* ]] || return 1
  [[ "${cmd}" == *"pgrep"* ]] && return 1
  [[ "${cmd}" == *"start_server.sh"* ]] && return 1
  cwd="$(readlink "/proc/${pid}/cwd" 2>/dev/null || true)"
  [[ "${cwd}" == "${ROOT}" ]]
}

list_api_pids() {
  local pid
  for pid in $(pgrep -f "uvicorn app.main:app" 2>/dev/null || true); do
    if api_cmdline_matches "${pid}"; then
      echo "${pid}"
    fi
  done
}

stop_pid_file() {
  local pid_file="$1"
  local label="$2"
  if [[ ! -f "${pid_file}" ]]; then
    return 0
  fi
  local pid
  pid="$(cat "${pid_file}")"
  if is_running "${pid}"; then
    echo "[stop] ${label} PID=${pid}"
    kill "${pid}" 2>/dev/null || true
    wait_stopped "${pid}"
  fi
  rm -f "${pid_file}"
}

stop_matching_processes() {
  local pid
  local pids
  pids="$(list_api_pids || true)"
  if [[ -z "${pids}" ]]; then
    return 0
  fi
  echo "[stop] 清理本目录 uvicorn: ${pids}"
  for pid in ${pids}; do
    kill "${pid}" 2>/dev/null || true
  done
  sleep 1
  pids="$(list_api_pids || true)"
  if [[ -n "${pids}" ]]; then
    for pid in ${pids}; do
      kill -9 "${pid}" 2>/dev/null || true
    done
  fi
}

ensure_port_free() {
  if command -v ss >/dev/null 2>&1; then
    if ss -tlnH "sport = :${PORT}" 2>/dev/null | grep -q .; then
      echo "错误: 端口 ${PORT} 仍被占用。" >&2
      echo "原因: 停止命令没有释放该端口。" >&2
      echo "处理: 执行 sudo bash start_server.sh status，确认没有残留进程后再 start。" >&2
      exit 1
    fi
  fi
}

cmd_stop() {
  require_root
  require_pgrep
  stop_pid_file "${API_PID_FILE}" "y-sso-api"
  stop_matching_processes
  echo "[stop] 完成"
}

cmd_status() {
  require_root
  require_pgrep
  local pid
  local api_count=0
  echo "=== y-sso-system 服务状态 ==="
  if [[ -f "${API_PID_FILE}" ]] && is_running "$(cat "${API_PID_FILE}")"; then
    echo "y-sso-api: 运行中 PID=$(cat "${API_PID_FILE}")"
  else
    echo "y-sso-api: pid 文件未记录存活进程（${API_PID_FILE}）"
  fi
  while IFS= read -r pid; do
    [[ -z "${pid}" ]] && continue
    api_count=$((api_count + 1))
    echo "匹配进程: PID=${pid} cwd=${ROOT} port=${PORT}"
  done < <(list_api_pids || true)
  if [[ "${api_count}" -eq 0 ]]; then
    echo "匹配进程: 无"
  fi
  echo "进程计数: api=${api_count}"
  if [[ "${api_count}" -gt 1 ]]; then
    echo "警告: 检测到 ${api_count} 个 API 进程。执行 sudo bash start_server.sh restart 清理重复实例。" >&2
  fi
}

cmd_start() {
  require_root
  require_python
  require_pgrep
  mkdir -p "${RUN_DIR}" "${ROOT}/logs"
  export PYTHONUNBUFFERED=1

  if [[ -f "${API_PID_FILE}" ]] && is_running "$(cat "${API_PID_FILE}")"; then
    echo "错误: y-sso-api 已在运行，PID=$(cat "${API_PID_FILE}")。" >&2
    echo "原因: ${API_PID_FILE} 中的进程仍存活。" >&2
    echo "处理: 执行 sudo bash start_server.sh restart，或先 stop 再 start。" >&2
    exit 1
  fi

  cmd_stop
  ensure_port_free

  nohup "${PY}" -m uvicorn app.main:app --host "${HOST}" --port "${PORT}" \
    >> "${ROOT}/logs/y-sso-api.stdout.log" 2>&1 &
  echo $! > "${API_PID_FILE}"

  sleep 1
  if ! is_running "$(cat "${API_PID_FILE}")"; then
    echo "错误: y-sso-api 启动后进程已退出，PID=$(cat "${API_PID_FILE}")。" >&2
    echo "原因: uvicorn 没有保持运行。日志在 ${ROOT}/logs/y-sso-api.stdout.log。" >&2
    echo "处理: 阅读该日志末尾的错误，修正后再执行 start。" >&2
    exit 1
  fi

  echo "[start] y-sso-api PID=$(cat "${API_PID_FILE}")  http://${HOST}:${PORT}"
  echo "[start] 业务日志: ${ROOT}/logs/app_*.log"
  echo "[start] 标准输出: ${ROOT}/logs/y-sso-api.stdout.log"
  cmd_status
}

cmd_restart() {
  require_root
  cmd_stop
  sleep 1
  cmd_start
}

ACTION="${1:-}"
case "${ACTION}" in
  start) cmd_start ;;
  stop) cmd_stop ;;
  restart) cmd_restart ;;
  status) cmd_status ;;
  *) usage ;;
esac
