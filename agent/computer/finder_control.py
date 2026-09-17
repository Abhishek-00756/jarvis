"""Expanded file management beyond basic read/write/delete."""
import shutil
import subprocess
from pathlib import Path

def find_file(name_pattern: str, limit: int = 20) -> str:
    result=subprocess.run(["mdfind","-name",name_pattern],capture_output=True,text=True,timeout=15)
    paths=result.stdout.strip().split("\n") if result.stdout.strip() else []
    return "\n".join(paths[:limit]) if paths else f"No files found matching '{name_pattern}'."

def search_file_content(query: str, limit: int = 20) -> str:
    result=subprocess.run(["mdfind",query],capture_output=True,text=True,timeout=20)
    paths=result.stdout.strip().split("\n") if result.stdout.strip() else []
    return "\n".join(paths[:limit]) if paths else f"No files found containing '{query}'."

def get_recent_files(directory: str = "~/Downloads", limit: int = 10) -> str:
    path=Path(directory).expanduser()
    if not path.exists(): return f"Directory not found: {directory}"
    files=sorted((p for p in path.iterdir() if p.is_file()),key=lambda p:p.stat().st_mtime,reverse=True)[:limit]
    return "\n".join(f"{p.name} ({p.stat().st_mtime})" for p in files) or "(no files)"

def get_file_info(path: str) -> str:
    p=Path(path).expanduser()
    if not p.exists(): return f"Not found: {path}"
    stat=p.stat()
    return f"Path: {p}\nSize: {stat.st_size} bytes\nModified: {stat.st_mtime}\nType: {'directory' if p.is_dir() else 'file'}"

def move_file(source: str,destination: str)->str:
    src,dst=Path(source).expanduser(),Path(destination).expanduser(); dst.parent.mkdir(parents=True,exist_ok=True); shutil.move(str(src),str(dst)); return f"Moved {source} to {destination}."

def copy_file(source: str,destination: str)->str:
    src,dst=Path(source).expanduser(),Path(destination).expanduser(); dst.parent.mkdir(parents=True,exist_ok=True)
    if src.is_dir(): shutil.copytree(str(src),str(dst))
    else: shutil.copy2(str(src),str(dst))
    return f"Copied {source} to {destination}."

def rename_file(path: str,new_name: str)->str:
    p=Path(path).expanduser(); new_path=p.parent/new_name; p.rename(new_path); return f"Renamed {path} to {new_path}."

def create_folder(path: str)->str:
    Path(path).expanduser().mkdir(parents=True,exist_ok=True); return f"Created folder {path}."

def trash_file(path: str)->str:
    p=Path(path).expanduser(); script=f'tell application "Finder" to delete POSIX file "{p}"'; result=subprocess.run(["osascript","-e",script],capture_output=True,text=True,timeout=10)
    return f"Error trashing file: {result.stderr.strip()}" if result.returncode!=0 else f"Moved {path} to Trash."

def reveal_in_finder(path: str)->str:
    subprocess.run(["open","-R",str(Path(path).expanduser())],timeout=10); return f"Revealed {path} in Finder."

def open_file(path: str)->str:
    subprocess.run(["open",str(Path(path).expanduser())],timeout=10); return f"Opened {path} with its default application."

def compress_file(path: str,output_path: str="")->str:
    src=Path(path).expanduser(); out=Path(output_path).expanduser() if output_path else src.with_suffix(".zip"); subprocess.run(["ditto","-c","-k","--sequesterRsrc",str(src),str(out)],timeout=60); return f"Compressed {path} to {out}."

def extract_archive(path: str,destination: str="")->str:
    src=Path(path).expanduser(); dest=Path(destination).expanduser() if destination else src.parent; dest.mkdir(parents=True,exist_ok=True); subprocess.run(["ditto","-x","-k",str(src),str(dest)],timeout=60); return f"Extracted {path} to {dest}."
