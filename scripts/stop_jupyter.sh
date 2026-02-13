#!/bin/bash
STATE_FILE="/home/ubuntu/jupyter_service/instances/jupyter_instances.json"
PORT="$1"

python3 - <<EOF
import json, os, signal, shutil, sys

f="$STATE_FILE"
port="$PORT"

data=json.load(open(f))
if port not in data:
    print("ERROR Not found")
    sys.exit(1)

pid=data[port]["pid"]
path=data[port].get("path")

try:
    os.kill(pid, signal.SIGTERM)
except ProcessLookupError:
    pass

del data[port]
json.dump(data, open(f,"w"), indent=2)

print("STOPPED", port)
EOF
