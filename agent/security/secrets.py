"""API credentials via macOS Keychain (using the built-in `security` CLI)."""
import subprocess
_SERVICE_PREFIX="jarvis-agent"
def store_secret(name:str,value:str)->str:
    subprocess.run(["security","add-generic-password","-a",name,"-s",f"{_SERVICE_PREFIX}-{name}","-w",value,"-U"],capture_output=True,text=True,timeout=10)
    return f"Stored '{name}' in Keychain."
def get_secret(name:str)->str|None:
    result=subprocess.run(["security","find-generic-password","-a",name,"-s",f"{_SERVICE_PREFIX}-{name}","-w"],capture_output=True,text=True,timeout=10)
    return result.stdout.strip() if result.returncode==0 else None
def delete_secret(name:str)->str:
    subprocess.run(["security","delete-generic-password","-a",name,"-s",f"{_SERVICE_PREFIX}-{name}"],capture_output=True,text=True,timeout=10)
    return f"Deleted '{name}' from Keychain (if it existed)."
