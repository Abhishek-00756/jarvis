"""Structured audit log for gated actions."""
import json,os
from datetime import datetime,timezone
from pathlib import Path
from agent import config
AUDIT_LOG_PATH=os.path.join(config.MEMORY_PATH,"audit.jsonl")
def log_action(tool_name:str,description:str,approved:bool,result:str="")->None:
    Path(config.MEMORY_PATH).mkdir(parents=True,exist_ok=True)
    entry={"timestamp":datetime.now(timezone.utc).isoformat(),"tool":tool_name,"description":description,"approved":approved,"result":result[:500] if result else ""}
    with open(AUDIT_LOG_PATH,"a") as f:f.write(json.dumps(entry)+"\n")
def read_recent_actions(limit:int=20)->list[dict]:
    if not os.path.exists(AUDIT_LOG_PATH):return []
    with open(AUDIT_LOG_PATH) as f: lines=f.readlines()
    return [json.loads(line) for line in lines[-limit:]]
def search_actions(keyword:str,limit:int=20)->list[dict]:
    if not os.path.exists(AUDIT_LOG_PATH):return []
    with open(AUDIT_LOG_PATH) as f: lines=f.readlines()
    matches=[]; key=keyword.lower()
    for line in reversed(lines):
        entry=json.loads(line)
        if key in json.dumps(entry).lower():matches.append(entry)
        if len(matches)>=limit:break
    return matches
