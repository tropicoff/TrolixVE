from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pymongo import MongoClient
import os
import uuid
from datetime import datetime
from typing import List, Optional
import json

app = FastAPI(title="TrolixVE API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = MongoClient(MONGO_URL)
db = client.trollixve_db
sandboxes_collection = db.sandboxes
sessions_collection = db.sessions

# Pydantic models
class SandboxConfig(BaseModel):
    name: str
    os_type: str
    cpu_cores: int = 2
    ram_gb: int = 4
    disk_gb: int = 20
    network_isolated: bool = True
    
class Sandbox(BaseModel):
    id: str
    name: str
    os_type: str
    status: str  # "running", "stopped", "saved", "creating"
    cpu_cores: int
    ram_gb: int
    disk_gb: int
    network_isolated: bool
    created_at: str
    last_accessed: str
    uptime: int = 0

class TerminalCommand(BaseModel):
    sandbox_id: str
    command: str

class TerminalSession(BaseModel):
    sandbox_id: str
    history: List[dict]

# Available OS templates
OS_TEMPLATES = {
    "kali": {"name": "Kali Linux", "icon": "🐲", "color": "#00ff41"},
    "ubuntu": {"name": "Ubuntu Server", "icon": "🐧", "color": "#ff6600"},
    "windows": {"name": "Windows 10", "icon": "🪟", "color": "#0078d4"},
    "centos": {"name": "CentOS", "icon": "🔴", "color": "#red"},
    "debian": {"name": "Debian", "icon": "🌀", "color": "#d70a53"},
    "arch": {"name": "Arch Linux", "icon": "⚡", "color": "#1793d1"},
}

# Simulated command responses
COMMAND_RESPONSES = {
    "ls": "bin  boot  dev  etc  home  lib  media  mnt  opt  proc  root  run  sbin  srv  sys  tmp  usr  var",
    "whoami": "root",
    "pwd": "/root",
    "uname -a": "Linux sandbox-{id} 5.15.0-kali3-amd64 #1 SMP Debian 5.15.15-2kali1 x86_64 GNU/Linux",
    "ps aux": "USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND\nroot         1  0.0  0.1  19312  1604 ?        Ss   12:00   0:00 /sbin/init",
    "ip a": "1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN\n    inet 127.0.0.1/8 scope host lo",
    "df -h": "Filesystem      Size  Used Avail Use% Mounted on\n/dev/sda1        20G  2.1G   17G  12% /",
    "free -h": "               total        used        free      shared  buff/cache   available\nMem:           4.0Gi       234Mi       3.4Gi        12Mi       356Mi       3.5Gi",
    "netstat": "Active Internet connections (only servers)\nProto Recv-Q Send-Q Local Address           Foreign Address         State",
    "help": "Available commands: ls, pwd, whoami, uname, ps, ip, df, free, netstat, nmap, metasploit, sqlmap, hashcat, john, aircrack-ng"
}

@app.get("/api/health")
async def health_check():
    return {"status": "online", "service": "TrolixVE"}

@app.get("/api/os-templates")
async def get_os_templates():
    return OS_TEMPLATES

@app.get("/api/sandboxes")
async def get_sandboxes():
    sandboxes = []
    for doc in sandboxes_collection.find():
        doc['_id'] = str(doc['_id'])
        sandboxes.append(doc)
    return sandboxes

@app.post("/api/sandboxes")
async def create_sandbox(config: SandboxConfig):
    sandbox = {
        "id": str(uuid.uuid4()),
        "name": config.name,
        "os_type": config.os_type,
        "status": "creating",
        "cpu_cores": config.cpu_cores,
        "ram_gb": config.ram_gb,
        "disk_gb": config.disk_gb,
        "network_isolated": config.network_isolated,
        "created_at": datetime.now().isoformat(),
        "last_accessed": datetime.now().isoformat(),
        "uptime": 0
    }
    
    result = sandboxes_collection.insert_one(sandbox)
    
    # Simulate creation delay
    import time
    time.sleep(2)
    
    # Update status to running
    sandboxes_collection.update_one(
        {"id": sandbox["id"]}, 
        {"$set": {"status": "running"}}
    )
    
    return {"message": "Sandbox created successfully", "sandbox_id": sandbox["id"]}

@app.post("/api/sandboxes/{sandbox_id}/start")
async def start_sandbox(sandbox_id: str):
    result = sandboxes_collection.update_one(
        {"id": sandbox_id},
        {"$set": {"status": "running", "last_accessed": datetime.now().isoformat()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Sandbox not found")
    return {"message": "Sandbox started"}

@app.post("/api/sandboxes/{sandbox_id}/stop")
async def stop_sandbox(sandbox_id: str):
    result = sandboxes_collection.update_one(
        {"id": sandbox_id},
        {"$set": {"status": "stopped"}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Sandbox not found")
    return {"message": "Sandbox stopped"}

@app.post("/api/sandboxes/{sandbox_id}/save")
async def save_sandbox(sandbox_id: str):
    result = sandboxes_collection.update_one(
        {"id": sandbox_id},
        {"$set": {"status": "saved"}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Sandbox not found")
    return {"message": "Sandbox saved successfully"}

@app.delete("/api/sandboxes/{sandbox_id}")
async def delete_sandbox(sandbox_id: str):
    result = sandboxes_collection.delete_one({"id": sandbox_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Sandbox not found")
    return {"message": "Sandbox deleted"}

@app.post("/api/terminal/execute")
async def execute_command(cmd: TerminalCommand):
    # Get sandbox info
    sandbox = sandboxes_collection.find_one({"id": cmd.sandbox_id})
    if not sandbox:
        raise HTTPException(status_code=404, detail="Sandbox not found")
    
    command = cmd.command.strip().lower()
    
    # Handle special commands
    if command.startswith("nmap"):
        output = "Starting Nmap scan...\nHosts discovered: 192.168.1.1, 192.168.1.100\nOpen ports: 22/tcp, 80/tcp, 443/tcp"
    elif command.startswith("metasploit") or command == "msfconsole":
        output = "      =[ metasploit v6.2.23-dev                         ]\n+ -- --=[ 2230 exploits - 1177 auxiliary - 398 post       ]\n+ -- --=[ 867 payloads - 45 encoders - 11 nops            ]\nmsf6 > "
    elif command.startswith("sqlmap"):
        output = "sqlmap/1.6.12#stable\n[12:34:56] [INFO] testing connection to target URL\n[12:34:57] [INFO] target appears to be MySQL"
    elif command.startswith("hashcat"):
        output = "hashcat (v6.2.5) starting...\nDevice #1: NVIDIA GeForce GTX 1080, 8192 MB"
    elif command.startswith("john"):
        output = "John the Ripper 1.9.0-jumbo-1\nLoaded 1 password hash (md5crypt, crypt(3) $1$ [MD5 128/128 AVX 4x3])"
    elif command.startswith("aircrack-ng"):
        output = "Aircrack-ng 1.6\nReading packets, please wait...\nOpening wpa.cap\nRead 12345 packets."
    elif command in COMMAND_RESPONSES:
        output = COMMAND_RESPONSES[command]
        if "{id}" in output:
            output = output.replace("{id}", cmd.sandbox_id[:8])
    else:
        output = f"bash: {cmd.command}: command not found"
    
    # Store command in session history
    timestamp = datetime.now().isoformat()
    session_entry = {
        "sandbox_id": cmd.sandbox_id,
        "command": cmd.command,
        "output": output,
        "timestamp": timestamp
    }
    
    sessions_collection.insert_one(session_entry)
    
    return {
        "command": cmd.command,
        "output": output,
        "timestamp": timestamp,
        "exit_code": 0
    }

@app.get("/api/terminal/{sandbox_id}/history")
async def get_terminal_history(sandbox_id: str):
    history = []
    for doc in sessions_collection.find({"sandbox_id": sandbox_id}).sort("timestamp", 1):
        doc['_id'] = str(doc['_id'])
        history.append(doc)
    return history

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)