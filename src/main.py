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
        frame.Show()
        
        # 如果存在配置文件，等待3秒后自动开始
        if os.path.exists("eye_rest_config.json"):
            def auto_start():
                time.sleep(3)
                # 模拟点击开始按钮
                frame.on_toggle(None)
            
            auto_start_thread = threading.Thread(target=auto_start)
            auto_start_thread.daemon = True
            auto_start_thread.start()
            
        return True

if __name__ == "__main__":
    app = EyeRestApp()
    app.MainLoop()
