from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

command_queue = []
bans = []

class Command(BaseModel):
    type: str
    username: str
    reason: Optional[str] = ""
    days: Optional[int] = 0
    adminId: Optional[int] = 0

@app.post("/command")
async def add_command(cmd: Command):
    if not cmd.type or not cmd.username:
        raise HTTPException(status_code=400, detail="Missing data")
    command_queue.append({"type": cmd.type, "username": cmd.username, "reason": cmd.reason, "days": cmd.days, "adminId": cmd.adminId, "sent": False})
    if cmd.type == "ban":
        bans.append({"username": cmd.username, "unbanDate": datetime.utcnow() + timedelta(days=cmd.days), "reason": cmd.reason})
    if cmd.type == "permaban":
        bans.append({"username": cmd.username, "unbanDate": None, "reason": cmd.reason})
    return {"ok": True}

@app.get("/get-commands")
async def get_commands():
    unsent = [c for c in command_queue if not c["sent"]]
    for c in unsent:
        c["sent"] = True
    return unsent

@app.get("/banlist")
async def get_banlist():
    now = datetime.utcnow()
    result = []
    for b in bans:
        days_left = "PERMA" if b["unbanDate"] is None else max(0, (b["unbanDate"] - now).days + 1)
        result.append({"username": b["username"], "daysLeft": days_left, "reason": b["reason"]})
    return result

@app.get("/")
async def root():
    return "Server is running ✅"