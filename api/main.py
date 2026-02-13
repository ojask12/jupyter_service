from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional
import subprocess, json, os, signal, psutil, secrets
from datetime import datetime, timedelta, timezone 

STATE_FILE = "/home/ubuntu/jupyter_service/instances/jupyter_instances.json"
MAX_RAM_USAGE_PER_INSTANCE_MB = 1024
MIN_RAM_FREE_MB = 1024

JUPYTER_BIN = "/home/ubuntu/.venv/bin/jupyter"
START_SCRIPT = "/home/ubuntu/jupyter_service/scripts/start_jupyter.sh"

app = FastAPI(title="Jupyter Manager")


# ------------------------
# Utilities
# ------------------------
def load_state():
    if not os.path.exists(STATE_FILE):
        return {}
    with open(STATE_FILE) as f:
        return json.load(f)


def save_state(data):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(data, f, indent=2)


def is_running(pid: int) -> bool:
    """Check if process is running, works across users"""
    try:
        # Try using psutil first (works across users)
        psutil.Process(pid)
        return True
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        # Fallback to os.kill (may fail for different users)
        try:
            os.kill(pid, 0)
            return True
        except (OSError, ProcessLookupError):
            return False


def cleanup_dead_and_expired():
    data = load_state()
    if not data:
        return  # Don't write empty dict if state file is empty
    
    now = datetime.now(timezone.utc)
    changed = False

    for port, info in list(data.items()):
        pid = info.get("pid")
        if not pid:
            del data[port]
            changed = True
            continue

        # Check if process is running (using improved is_running that works across users)
        if not is_running(pid):
            # Process is dead, remove from state
            del data[port]
            changed = True
            continue

        # ⬇️ HANDLE OLD ENTRIES SAFELY
        expires_at_str = info.get("expires_at")
        if not expires_at_str:
            # Old instance → expire immediately
            try:
                os.kill(pid, signal.SIGTERM)
            except (OSError, ProcessLookupError):
                pass  # Process already dead
            del data[port]
            changed = True
            continue

        expires_at = datetime.fromisoformat(expires_at_str)
        
        # Check if expiration is set to far future (timer disabled) - 50+ years indicates disabled timer
        # This allows sessions with disabled timers to never expire
        years_until_expiry = (expires_at - now).total_seconds() / (365.25 * 24 * 3600)
        if years_until_expiry > 50:
            # Timer disabled - skip expiration check
            continue

        if now >= expires_at:
            try:
                os.kill(pid, signal.SIGTERM)
            except (OSError, ProcessLookupError):
                pass  # Process already dead
            del data[port]
            changed = True

    if changed:
        save_state(data)


def get_free_ram_mb():
    return psutil.virtual_memory().available // 1024 // 1024


def get_total_estimated_ram_usage_mb():
    data = load_state()
    usage = 0
    for info in data.values():
        pid = info["pid"]
        if is_running(pid):
            try:
                p = psutil.Process(pid)
                usage += p.memory_info().rss // 1024 // 1024
            except psutil.NoSuchProcess:
                pass
    return usage


@app.on_event("startup")
async def startup_event():
    cleanup_dead_and_expired()

from argon2 import PasswordHasher

ph = PasswordHasher()

def generate_jupyter_password(password: str) -> str:
    """
    Returns a Jupyter-compatible Argon2 hash
    """
    return ph.hash(password)
# ------------------------
# START JUPYTER
# ------------------------
from jupyter_server.auth import passwd


@app.post("/api/jupyter")
def start_jupyter(session_minutes: Optional[int] = None, user_port: Optional[int] = None, password: str = "", disable_timer: bool = False):
    print(f"Starting Jupyter with session_minutes: {session_minutes}, user_port: {user_port}, password: {password}, disable_timer: {disable_timer}")
    free_ram = get_free_ram_mb()
    estimated_usage = get_total_estimated_ram_usage_mb()

    if free_ram - MIN_RAM_FREE_MB < MAX_RAM_USAGE_PER_INSTANCE_MB:
        raise HTTPException(
            status_code=503,
            detail="Not enough free RAM"
        )

    # 🔐 Generate password
    if password == "":
        password = secrets.token_urlsafe(10)
    password_hash = passwd(password)       # pass this to Jupyter

    # Handle timer: if disabled, set far future expiration; otherwise use session_minutes (default 60 if not provided)
    if disable_timer:
        # Set expiration to 100 years in the future (effectively never expires)
        expires_at = datetime.now(timezone.utc) + timedelta(days=365 * 100)
        ttl_minutes = ""  # Empty string tells shell script not to set up auto-expire
    else:
        if session_minutes is None:
            session_minutes = 60  # Default value
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=session_minutes)
        ttl_minutes = str(session_minutes)
    
    print(f"Expires at: {expires_at}")
    try:
        result = subprocess.run(
            [
                "/home/ubuntu/jupyter_service/scripts/start_jupyter.sh",
                password,
                password_hash,
                expires_at.isoformat(),
                ttl_minutes,
                str(user_port) if user_port else ""
            ],
            text=True,
            capture_output=True,
            timeout=60,
            bufsize=1  # Line buffered
        )
        
        # Debug output
        print(f"Script return code: {result.returncode}")
        print(f"Script stdout: {result.stdout}")
        print(f"Script stderr: {result.stderr}")
        
        if result.returncode != 0:
            error_msg = result.stderr or result.stdout or "Unknown error"
            print(f"Script error: {error_msg}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to start Jupyter: {error_msg}"
            )
        
        output = result.stdout.strip()
        if not output:
            # If no stdout but state file was updated, try to read from state file
            data = load_state()
            if user_port and str(user_port) in data:
                info = data[str(user_port)]
                port = user_port
                pid = info.get("pid")
                print(f"Recovered from state file: port={port}, pid={pid}")
            else:
                raise HTTPException(
                    status_code=500,
                    detail="Script returned no output and state file not updated"
                )
        else:
            parts = output.split()
            if len(parts) < 2:
                raise HTTPException(
                    status_code=500,
                    detail=f"Unexpected script output format: {output}"
                )
            port, pid = parts[0], parts[1]

        return {
            "status": "started",
            "port": int(port),
            "pid": int(pid),
            "url": f"http://13.232.82.145:{port}",
            "password": password,              # 👈 shown ONCE
            "expires_at": expires_at.isoformat() if not disable_timer else None
        }

    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=str(e))



# ------------------------
# STOP JUPYTER
# ------------------------
@app.delete("/api/jupyter/{port}")
def stop_jupyter(port: int):
    data = load_state()

    if str(port) not in data:
        raise HTTPException(status_code=404, detail="Instance not found")

    pid = data[str(port)]["pid"]

    try:
        os.kill(pid, signal.SIGTERM)
    except:
        pass

    del data[str(port)]
    save_state(data)

    return {"status": "stopped", "port": port}


# ------------------------
# LIST JUPYTER
# ------------------------
@app.get("/api/jupyter")
def list_jupyter():
    cleanup_dead_and_expired()
    data = load_state()

    instances = []
    for port, info in data.items():
        expires_at_str = info.get("expires_at")
        # Check if expiration is set to far future (timer disabled)
        expires_at = None
        if expires_at_str:
            expires_at_dt = datetime.fromisoformat(expires_at_str)
            years_until_expiry = (expires_at_dt - datetime.now(timezone.utc)).total_seconds() / (365.25 * 24 * 3600)
            if years_until_expiry <= 50:
                expires_at = expires_at_str
        
        instances.append({
            "port": int(port),
            "pid": info["pid"],
            "started_at": info["started_at"],
            "expires_at": expires_at,  # None if timer is disabled
            "password": info.get("password"),
            "running": is_running(info["pid"]),
            "url": f"http://13.232.82.145:{port}",
        })

    return JSONResponse(instances)
