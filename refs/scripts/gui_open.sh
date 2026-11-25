#!/usr/bin/env bash
# 在当前 SolidCraft GUI 窗口中打开模型并 View Fit，然后截图。
# 用法: ./gui_open.sh <design.sc 文件名> [截图输出名]
set -u
CTRL="${LOCALAPPDATA:-/c/Users/jack/AppData/Local}/SolidCraft/control"
PORT=$(cat "$CTRL/current.port" 2>/dev/null)
TOKEN=$(cat "$CTRL/$PORT.token" 2>/dev/null)
if [ -z "$PORT" ] || [ -z "$TOKEN" ]; then
  echo "no live SolidCraft control port" >&2
  exit 1
fi
DESIGN="${1:-X_Axis_Slide.sc}"
SHOT="${2:-}"
CLI="/d/Program Files/SolidCraft/solidcraft-cli.exe"
REQ=$(mktemp)
{
  echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"gui-open","version":"0"}}}'
  echo '{"jsonrpc":"2.0","method":"notifications/initialized"}'
  echo "{\"jsonrpc\":\"2.0\",\"id\":2,\"method\":\"tools/call\",\"params\":{\"name\":\"open\",\"arguments\":{\"path\":\"D:/mydocuments/SolidCraft/$DESIGN\"}}}"
  echo '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"execute","arguments":{"command":"view.fit","params":{}}}}'
  if [ -n "$SHOT" ]; then
    echo "{\"jsonrpc\":\"2.0\",\"id\":4,\"method\":\"tools/call\",\"params\":{\"name\":\"screenshot\",\"arguments\":{\"source\":\"model\",\"view\":\"fit\",\"width\":1400,\"height\":900,\"grid\":false,\"axes\":false,\"path\":\"D:/mydocuments/SolidCraft/$SHOT\"}}}"
  fi
} > "$REQ"
echo "port $PORT"
SOLIDCRAFT_CONTROL_TOKEN="$TOKEN" timeout 180 "$CLI" mcp \
  --connect "127.0.0.1:$PORT" --allow-path "D:\\mydocuments\\SolidCraft" \
  < "$REQ" 2>&1 | grep -o '"id":[0-9].\{0,220\}' | head -6
rm -f "$REQ"
