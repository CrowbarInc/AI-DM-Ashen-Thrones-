"""Stdlib-only offline Windows process experiment; no game imports or sockets."""
import ctypes
from ctypes import wintypes as w
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).parent
K = ctypes.WinDLL('kernel32', use_last_error=True)

class Entry(ctypes.Structure):
    _fields_ = [('dwSize', w.DWORD), ('cntUsage', w.DWORD), ('th32ProcessID', w.DWORD),
                ('th32DefaultHeapID', ctypes.c_size_t), ('th32ModuleID', w.DWORD),
                ('cntThreads', w.DWORD), ('th32ParentProcessID', w.DWORD),
                ('pcPriClassBase', w.LONG), ('dwFlags', w.DWORD), ('szExeFile', w.WCHAR * 260)]

K.CreateToolhelp32Snapshot.argtypes = [w.DWORD, w.DWORD]
K.CreateToolhelp32Snapshot.restype = w.HANDLE
K.Process32FirstW.argtypes = K.Process32NextW.argtypes = [w.HANDLE, ctypes.POINTER(Entry)]
K.CloseHandle.argtypes = [w.HANDLE]
K.OpenProcess.argtypes = [w.DWORD, w.BOOL, w.DWORD]
K.OpenProcess.restype = w.HANDLE
K.TerminateProcess.argtypes = [w.HANDLE, w.UINT]
K.WaitForSingleObject.argtypes = [w.HANDLE, w.DWORD]

def processes():
    handle = K.CreateToolhelp32Snapshot(2, 0)
    if handle == ctypes.c_void_p(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    result = {}
    try:
        entry = Entry()
        entry.dwSize = ctypes.sizeof(entry)
        more = K.Process32FirstW(handle, ctypes.byref(entry))
        if not more:
            raise ctypes.WinError(ctypes.get_last_error())
        while more:
            result[entry.th32ProcessID] = dict(pid=entry.th32ProcessID,
                parent_pid=entry.th32ParentProcessID, image=entry.szExeFile)
            more = K.Process32NextW(handle, ctypes.byref(entry))
    finally:
        K.CloseHandle(handle)
    return result

def save(name, value):
    (OUT/name).write_text(json.dumps(value, indent=2)+'\n', encoding='utf-8')

def hashes():
    return {str(p.relative_to(ROOT)).replace('\\', '/'): hashlib.sha256(p.read_bytes()).hexdigest()
            for folder in ('game', 'tools', 'tests', 'artifacts/pr_play_29', 'artifacts/pr_play_31', 'artifacts/pr_play_32')
            for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts}

def main():
    save('baseline_hashes.json', hashes())
    (OUT/'git_status_before.txt').write_bytes(subprocess.check_output(['git', 'status', '--short'], cwd=ROOT))
    rows = []
    for label, exe in [('sys.executable', sys.executable), ('sys._base_executable', sys._base_executable)]:
        for shutdown in ('normal', 'terminate'):
            folder = OUT/(label.replace('.', '_')+'_'+shutdown)
            folder.mkdir(exist_ok=False)
            report = folder/'worker.json'
            # No imports of the application, provider SDK or network libraries.
            code = "import os,sys,json; from pathlib import Path; Path(sys.argv[1]).write_text(json.dumps(dict(pid=os.getpid(),parent_pid=os.getppid(),executable=sys.executable,base_executable=sys._base_executable))); sys.stdin.readline()"
            env = {k: v for k, v in os.environ.items() if k.upper() in {'SYSTEMROOT', 'WINDIR', 'TEMP', 'TMP', 'PATH'}}
            proc = subprocess.Popen([exe, '-u', '-c', code, str(report)], env=env,
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW)
            worker_handle = None
            try:
                deadline = time.monotonic()+10
                while not report.exists() and proc.poll() is None and time.monotonic()<deadline:
                    time.sleep(.02)
                worker = json.loads(report.read_text())
                table = processes()
                chain, pid = [], worker['pid']
                while pid in table and pid not in {r['pid'] for r in chain}:
                    chain.append(table[pid])
                    pid = table[pid]['parent_pid']
                assert any(r['pid'] == proc.pid for r in chain)
                # Open the observed worker while it is alive, before any termination.
                # Retain its handle so cleanup cannot target a reused PID.
                worker_handle = K.OpenProcess(0x100001, False, worker['pid'])
                if not worker_handle:
                    raise ctypes.WinError(ctypes.get_last_error())
                row = dict(selection=label, executable=exe, controller_pid=os.getpid(),
                    controller_parent_pid=os.getppid(), popen_pid=proc.pid, worker=worker,
                    ancestry=chain, shutdown=shutdown)
                if shutdown == 'normal':
                    proc.stdin.write(b'\n'); proc.stdin.flush()
                else:
                    proc.terminate()
                proc.wait(timeout=5)
                row['exit_code'] = proc.returncode
                row['worker_exited_after_controller_cleanup'] = K.WaitForSingleObject(worker_handle, 1000) == 0
                if not row['worker_exited_after_controller_cleanup']:
                    assert K.TerminateProcess(worker_handle, 1)
                    assert K.WaitForSingleObject(worker_handle, 5000) == 0
                    row['diagnostic_descendant_cleanup'] = True
                row['remaining_observed_pids'] = [pid for pid in {proc.pid, worker['pid']} if pid in processes()]
                assert not row['remaining_observed_pids']
                rows.append(row)
                save('process_reproduction.json', rows)
            finally:
                if worker_handle:
                    if K.WaitForSingleObject(worker_handle, 0) != 0:
                        K.TerminateProcess(worker_handle, 1)
                        K.WaitForSingleObject(worker_handle, 5000)
                    K.CloseHandle(worker_handle)
                if proc.poll() is None:
                    proc.kill(); proc.wait(timeout=5)
                for stream in (proc.stdin, proc.stdout, proc.stderr):
                    stream.close()
    print(json.dumps(rows, indent=2))

if __name__ == '__main__':
    main()
