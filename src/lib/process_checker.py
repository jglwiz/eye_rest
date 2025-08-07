import json
import os
import sys
import time
import psutil
from pathlib import Path

# 锁文件路径
LOCK_FILE_PATH = os.path.join(os.path.expanduser("~"), ".eye_rest_lock.json")

def check_duplicate_process():
    """
    使用文件锁定方式检测是否已有程序实例运行
    返回: True表示有重复进程，False表示无重复进程
    """
    try:
        if os.path.exists(LOCK_FILE_PATH):
            # 读取锁文件内容
            with open(LOCK_FILE_PATH, 'r', encoding='utf-8') as f:
                lock_data = json.load(f)
            
            pid = lock_data.get('pid')
            if pid:
                # 检查进程是否仍在运行
                if is_process_running(pid):
                    # 进一步验证是否是同一个程序
                    if is_same_program(pid):
                        print(f"检测到重复进程，PID: {pid}")
                        return True
                    else:
                        print(f"PID {pid} 存在但不是同一个程序，清理锁文件")
                        _remove_lock_file()
                else:
                    print(f"锁文件中的进程 {pid} 已不存在，清理僵尸锁文件")
                    _remove_lock_file()
        
        return False
        
    except Exception as e:
        print(f"检测重复进程时出现异常: {e}")
        # 出现异常时清理可能损坏的锁文件
        _remove_lock_file()
        return False

def create_lock_file():
    """
    创建锁文件，记录当前进程信息
    """
    try:
        current_pid = os.getpid()
        current_time = time.strftime("%Y-%m-%d %H:%M:%S")
        exe_path = sys.executable if hasattr(sys, 'executable') else ""
        
        lock_data = {
            "pid": current_pid,
            "start_time": current_time,
            "exe_path": exe_path,
            "program_name": "eye_rest"
        }
        
        # 确保目录存在
        os.makedirs(os.path.dirname(LOCK_FILE_PATH), exist_ok=True)
        
        with open(LOCK_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(lock_data, f, ensure_ascii=False, indent=2)
        
        print(f"创建锁文件成功，PID: {current_pid}")
        return True
        
    except Exception as e:
        print(f"创建锁文件失败: {e}")
        return False

def remove_lock_file():
    """
    删除锁文件（程序退出时调用）
    """
    return _remove_lock_file()

def _remove_lock_file():
    """
    内部方法：删除锁文件
    """
    try:
        if os.path.exists(LOCK_FILE_PATH):
            os.remove(LOCK_FILE_PATH)
            print("删除锁文件成功")
            return True
        return True
    except Exception as e:
        print(f"删除锁文件失败: {e}")
        return False

def is_process_running(pid):
    """
    检查指定PID的进程是否正在运行
    """
    try:
        return psutil.pid_exists(pid)
    except Exception:
        # 如果psutil不可用，使用系统特定的方法
        try:
            if sys.platform == "win32":
                import subprocess
                result = subprocess.run(
                    ['tasklist', '/FI', f'PID eq {pid}'],
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                return str(pid) in result.stdout
            else:
                # Linux/Mac
                os.kill(pid, 0)
                return True
        except (OSError, subprocess.SubprocessError):
            return False

def is_same_program(pid):
    """
    检查指定PID的进程是否是同一个程序
    """
    try:
        process = psutil.Process(pid)
        process_name = process.name().lower()
        
        # 检查进程名是否包含eye相关关键词
        return any(keyword in process_name for keyword in ['eye', 'python', 'pythonw'])
    except Exception:
        # 如果无法获取进程信息，保守地认为是同一个程序
        return True

def get_lock_info():
    """
    获取当前锁文件信息（用于调试）
    """
    try:
        if os.path.exists(LOCK_FILE_PATH):
            with open(LOCK_FILE_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    except Exception as e:
        print(f"读取锁文件信息失败: {e}")
        return None 