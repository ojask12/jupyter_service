#!/bin/bash

PASSWORD="$1"
PASSWORD_HASH="$2"
EXPIRES_AT="$3"   # now correctly assigned
TTL_MINUTES="$4"  # optional, for auto-stop
USER_PORT="$5"

STATE_FILE="/home/ubuntu/jupyter_service/instances/jupyter_instances.json"
BASE_DIR="/home/ubuntu/jupyter_service/instances"
COMMON_DIR="$BASE_DIR/common"
JUPYTER_BIN="/home/ubuntu/.venv/bin/jupyter"

if [ -z "$PASSWORD_HASH" ] || [ -z "$EXPIRES_AT" ]; then
  echo "ERROR Missing password hash or expiry"
  exit 1
fi

# -------------------------
# Find free port if not provided
# -------------------------
if [ -n "$USER_PORT" ]; then
    PORT="$USER_PORT"
    # Check if the port is already in use
    if ss -lnt | awk '{print $4}' | sed 's/.*://' | grep -q "^$PORT\$"; then
        echo "ERROR: Port $PORT is already in use"
        exit 1
    fi
else
    PORT=$(/usr/bin/comm -23 \
        <(/usr/bin/seq 9000 9100 | /usr/bin/sort) \
        <(/usr/bin/ss -lnt | /usr/bin/awk '{print $4}' | /usr/bin/sed 's/.*://' | /usr/bin/sort -u) \
        | /usr/bin/head -n 1)
fi

[ -z "$PORT" ] && echo "ERROR No free ports" && exit 1

# -------------------------
# Directories
# -------------------------
INSTANCE_DIR="$BASE_DIR/$PORT"
NOTEBOOK_DIR="$INSTANCE_DIR/notebooks"

USER_NAME="jupyter-$PORT"
ADMIN_GROUP="jupyter-admins"

# Create notebook dir as root first
sudo mkdir -p "$NOTEBOOK_DIR"

# -------------------------
# Fix parent directory traversal (CRITICAL)
# -------------------------
sudo chmod 711 /home/ubuntu
sudo chmod 755 /home/ubuntu/jupyter_service
sudo chmod 755 /home/ubuntu/jupyter_service/instances

# =========================
# Ensure admin group exists
# =========================
if ! getent group "$ADMIN_GROUP" >/dev/null; then
  sudo groupadd "$ADMIN_GROUP"
fi

# Ensure ubuntu is in admin group
sudo usermod -aG "$ADMIN_GROUP" ubuntu

# =========================
# Create user if missing
# =========================
if ! cut -d: -f1 /etc/passwd | grep -q "^${USER_NAME}$"; then
  # If directory exists but user doesn't, remove it first to avoid warning
  if [ -d "$INSTANCE_DIR" ]; then
    echo "Directory $INSTANCE_DIR exists but user $USER_NAME doesn't. Cleaning up..."
    sudo rm -rf "$INSTANCE_DIR"
  fi
  
  sudo useradd \
    --create-home \
    --home-dir "$INSTANCE_DIR" \
    --shell /bin/bash \
    "$USER_NAME"
fi

# Add Jupyter user to admin group
sudo usermod -aG "$ADMIN_GROUP" "$USER_NAME"

# =========================
# Directory setup
# =========================
sudo mkdir -p "$NOTEBOOK_DIR"
sudo chown -R "$USER_NAME:$ADMIN_GROUP" "$INSTANCE_DIR"
sudo chmod -R 777 "$INSTANCE_DIR"

# Ensure new files inherit group
sudo chmod g+s "$INSTANCE_DIR"

# =========================
# Start Jupyter
# =========================
echo "Starting Jupyter on port $PORT as $USER_NAME..."

# Escape password hash for safe passing through nested shells
ESCAPED_PASSWORD_HASH=$(printf '%q' "$PASSWORD_HASH")

sudo -u "$USER_NAME" -H bash -c "
cd \"$NOTEBOOK_DIR\"
nohup \"$JUPYTER_BIN\" lab \
  --ip=0.0.0.0 \
  --port=$PORT \
  --no-browser \
  --ServerApp.token='' \
  --ServerApp.password=$ESCAPED_PASSWORD_HASH \
  --notebook-dir=\"$NOTEBOOK_DIR\" \
  > \"$INSTANCE_DIR/jupyter.log\" 2>&1 &
" &

# Wait for Jupyter to start and find PID (simplified)
# Wait a moment for Jupyter to bind to port
sleep 3

# Find PID - try lsof first (fastest), then ss
PID=$(sudo lsof -ti:$PORT 2>/dev/null | head -n 1)

if [ -z "$PID" ]; then
  # Fallback to ss
  PID=$(sudo ss -lntp 2>/dev/null | grep ":$PORT " | sed -n 's/.*pid=\([0-9]*\).*/\1/p' | head -n 1)
fi

# Retry up to 8 times if PID not found (max 11 seconds total)
RETRY=0
while [ -z "$PID" ] && [ $RETRY -lt 8 ]; do
  sleep 1
  PID=$(sudo lsof -ti:$PORT 2>/dev/null | head -n 1)
  [ -z "$PID" ] && PID=$(sudo ss -lntp 2>/dev/null | grep ":$PORT " | sed -n 's/.*pid=\([0-9]*\).*/\1/p' | head -n 1)
  RETRY=$((RETRY + 1))
done

if [ -z "$PID" ]; then
  echo "ERROR: Failed to find PID on port $PORT" >&2
  exit 1
fi

# -------------------------
# Auto-expire (if TTL set)
# -------------------------
if [ ! -z "$TTL_MINUTES" ]; then
(
  sleep $((TTL_MINUTES * 60))
  # Kill the Jupyter process (use sudo since it runs as jupyter user)
  sudo kill "$PID" 2>/dev/null || kill "$PID" 2>/dev/null
) &
fi

# -------------------------
# Persist state
# -------------------------
# Validate PID before writing
if [ -z "$PID" ] || ! [[ "$PID" =~ ^[0-9]+$ ]]; then
  echo "ERROR: Invalid PID: $PID" >&2
  exit 1
fi

# Write state file with error handling
python3 - <<EOF
import json, datetime, os, sys

try:
    f="$STATE_FILE"
    os.makedirs(os.path.dirname(f), exist_ok=True)
    data = json.load(open(f)) if os.path.exists(f) else {}
    
    data["$PORT"] = {
        "pid": int("$PID"),
        "started_at": datetime.datetime.utcnow().isoformat(),
        "expires_at": "$EXPIRES_AT",
        "path": "$INSTANCE_DIR",
        "common": "$COMMON_DIR",
        "password": "$PASSWORD"
    }
    
    with open(f, "w") as outfile:
        json.dump(data, outfile, indent=2)
except Exception as e:
    print(f"ERROR writing state file: {e}", file=sys.stderr)
    sys.exit(1)
EOF

# Output PORT and PID (required by API)
echo "$PORT $PID"
