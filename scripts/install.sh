#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="${WORKSPACE:-$HOME/ros2_delatometry}"
ROS_SETUP="${ROS_SETUP:-/opt/ros/jazzy/setup.bash}"
VENV_DIR="${VENV_DIR:-$HOME/venvs/ros2_delatometry_webui}"
PACKAGE_NAME="${PACKAGE_NAME:-measure_device}"
USER_NAME="${USER_NAME:-$(id -un)}"

log() {
  echo "[measure_device install] $*"
}

source_safe() {
  local setup_file="$1"
  if [ ! -f "$setup_file" ]; then
    echo "ERROR: setup file not found: $setup_file" >&2
    exit 1
  fi
  set +u
  # shellcheck disable=SC1090
  source "$setup_file"
  set -u
}

if [ ! -d "$WORKSPACE" ]; then
  echo "ERROR: workspace not found: $WORKSPACE" >&2
  exit 1
fi

if [ ! -d "$WORKSPACE/src/$PACKAGE_NAME" ]; then
  echo "ERROR: package not found: $WORKSPACE/src/$PACKAGE_NAME" >&2
  exit 1
fi

log "workspace: $WORKSPACE"
log "ROS setup:  $ROS_SETUP"
log "venv:       $VENV_DIR"

log "installing system dependencies"
sudo apt update
sudo apt install -y \
  python3-venv \
  python3-pip \
  python3-serial

if command -v usermod >/dev/null 2>&1; then
  if id -nG "$USER_NAME" | tr ' ' '\n' | grep -qx dialout; then
    log "user '$USER_NAME' is already in dialout group"
  else
    log "adding user '$USER_NAME' to dialout group for /dev/ttyUSB* access"
    sudo usermod -aG dialout "$USER_NAME"
    log "NOTE: logout/login or reboot may be required before serial permissions update"
  fi
fi

log "creating/updating venv"
python3 -m venv --system-site-packages "$VENV_DIR"
# shellcheck disable=SC1090
source "$VENV_DIR/bin/activate"
python3 -m pip install --upgrade pip setuptools wheel

REQ_FILE="$WORKSPACE/src/$PACKAGE_NAME/requirements.txt"
if [ -f "$REQ_FILE" ]; then
  log "installing Python requirements from $REQ_FILE"
  python3 -m pip install -r "$REQ_FILE"
else
  log "requirements.txt not found, installing pyserial directly"
  python3 -m pip install 'pyserial>=3.5'
fi

log "checking source for known E720 field-name issue"
NODE_FILE="$WORKSPACE/src/$PACKAGE_NAME/$PACKAGE_NAME/node.py"
if [ -f "$NODE_FILE" ]; then
  if grep -qE 'msg\.(OffSet|Level|Freq10|Frequency|Limit|ImParam|SecParam|SecValue|SecondValue|ImValue|FirstValue|OnChange|TimeStamp)' "$NODE_FILE"; then
    echo "ERROR: $NODE_FILE still writes uppercase E720 fields." >&2
    echo "Fix node.py to use lowercase fields from msgs/msg/E720.msg before building." >&2
    echo "Example: msg.OffSet -> msg.offset, msg.Level -> msg.level, msg.TimeStamp -> msg.timestamp" >&2
    exit 2
  fi
fi

PKG_INIT="$WORKSPACE/src/$PACKAGE_NAME/$PACKAGE_NAME/__init__.py"
if [ ! -f "$PKG_INIT" ]; then
  log "creating missing Python package marker: $PKG_INIT"
  mkdir -p "$(dirname "$PKG_INIT")"
  printf '%s\n' '"""ROS 2 node package for the E7-20 RS232 measurement device."""' '' '__all__ = []' > "$PKG_INIT"
fi

log "sourcing ROS"
source_safe "$ROS_SETUP"

log "building package: $PACKAGE_NAME"
cd "$WORKSPACE"
colcon build --symlink-install --packages-select "$PACKAGE_NAME"

log "sourcing workspace"
source_safe "$WORKSPACE/install/setup.bash"

log "verifying Python dependencies and ROS interfaces"
python3 -c "import serial; print('pyserial OK')"
python3 -c "from msgs.msg import E720; print('msgs/msg/E720 OK')"
python3 -c "import measure_device.node; print('measure_device.node import OK')"

log "checking ROS executable"
EXECUTABLES="$(ros2 pkg executables "$PACKAGE_NAME" || true)"
echo "$EXECUTABLES"
if ! echo "$EXECUTABLES" | grep -q "measure_device_node"; then
  echo "ERROR: measure_device_node executable was not registered by colcon." >&2
  exit 3
fi

log "OK"
echo
echo "Start manually:"
echo "  cd $WORKSPACE"
echo "  source $ROS_SETUP"
echo "  source $WORKSPACE/install/setup.bash"
echo "  source $VENV_DIR/bin/activate"
echo "  ros2 launch measure_device measure_device.launch.py port:=/dev/ttyUSB0 speed:=9600"
echo
echo "Verify topic:"
echo "  ros2 topic echo /measure_device"
