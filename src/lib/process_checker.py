import subprocess
import sys
import os

def check_duplicate_process():
    """
    检测是否已有eye.exe进程运行
    返回: True表示有重复进程，False表示无重复进程
    """
    try:
        # 在Windows上使用tasklist命令检测进程
        if sys.platform == "win32":
            # 执行tasklist命令，过滤eye.exe进程
            result = subprocess.run(
                ['tasklist', '/FI', 'IMAGENAME eq eye.exe'],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW  # 不显示命令行窗口
            )
            
            # 检查命令是否成功执行
            if result.returncode == 0:
                output = result.stdout.lower()
                # 如果输出中包含eye.exe，说明进程存在
                if 'eye.exe' in output and 'no tasks are running' not in output:
                    return True
            
        # 对于非Windows系统，可以使用ps命令（如果需要的话）
        else:
            # 这里可以添加Linux/Mac的进程检测逻辑
            # 目前主要针对Windows，所以暂时返回False
            pass
            
    except Exception as e:
        # 如果检测过程出现异常，为了安全起见返回False（允许启动）
        print(f"进程检测出现异常: {e}")
        return False
    
    return False

def get_current_process_count():
    """
    获取当前eye.exe进程的数量（用于调试）
    """
    try:
        if sys.platform == "win32":
            result = subprocess.run(
                ['tasklist', '/FI', 'IMAGENAME eq eye.exe'],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                count = 0
                for line in lines:
                    if 'eye.exe' in line.lower():
                        count += 1
                return count
                
    except Exception as e:
        print(f"获取进程数量时出现异常: {e}")
        
    return 0 