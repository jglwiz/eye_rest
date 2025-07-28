import wx
import threading
import time
import os
import sys

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.main_window import MainFrame
from lib.process_checker import check_duplicate_process

class EyeRestApp(wx.App):
    def OnInit(self):
        # 检查是否已有程序实例在运行
        if check_duplicate_process():
            wx.MessageBox(
                "护眼助手已在运行中！\n\n请检查系统托盘图标，双击可打开设置界面。",
                "护眼助手",
                wx.OK | wx.ICON_INFORMATION
            )
            return False  # 退出应用
        
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
