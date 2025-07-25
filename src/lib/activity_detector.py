import ctypes
import ctypes.wintypes
import time

class ActivityDetector:
    """用户活动检测器，使用Windows API检测键盘鼠标活动"""
    
    def __init__(self):
        self.user32 = ctypes.windll.user32
        
    def get_last_input_time(self):
        """获取最后一次输入时间（毫秒）"""
        class LASTINPUTINFO(ctypes.Structure):
            _fields_ = [("cbSize", ctypes.wintypes.UINT),
                       ("dwTime", ctypes.wintypes.DWORD)]
        
        lii = LASTINPUTINFO()
        lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
        
        if self.user32.GetLastInputInfo(ctypes.byref(lii)):
            return lii.dwTime
        return 0
    
    def get_idle_seconds(self):
        """获取空闲秒数"""
        last_input_time = self.get_last_input_time()
        current_time = ctypes.windll.kernel32.GetTickCount()
        return (current_time - last_input_time) // 1000
    
    def is_user_idle(self, threshold_seconds):
        """检查用户是否空闲超过阈值"""
        return self.get_idle_seconds() >= threshold_seconds 