import wx
import threading
import time
import os
import sys

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.main_window import MainFrame

class EyeRestApp(wx.App):
    def OnInit(self):
        frame = MainFrame()
        
        # 检查是否有配置文件
        config_exists = os.path.exists("eye_rest_config.json")
        
        if config_exists:
            # 静默启动：不显示窗口，直接开始工作
            frame.start_silent_mode()
        else:
            # 首次使用：显示配置界面
            frame.Show()
            
        return True

if __name__ == "__main__":
    app = EyeRestApp()
    app.MainLoop()
