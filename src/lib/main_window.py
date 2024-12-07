import wx
import wx.adv
import threading
import time
import keyboard
# import sys, pprint; pprint.pprint(sys.path)
from lib.rest_screen import RestScreen
from lib.taskbar import TaskBarIcon
from lib.config import Config

class MainFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="护眼助手", size=(300, 250))
        
        self.config = Config()
        self.is_working = False
        self.is_resting = False
        self.rest_screen = RestScreen()
        self.force_rest_thread = None
        self.real_close = False
        
        # 创建系统托盘图标
        self.taskbar_icon = TaskBarIcon(self)
        
        self._init_ui()
        self._init_hotkey()
        
        # 创建计时器线程
        self.timer_thread = None
        
        # 绑定关闭事件
        self.Bind(wx.EVT_CLOSE, self.on_close)
        
        # 居中显示
        self.Center()

    def _init_ui(self):
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        # 添加配置控件
        grid = wx.FlexGridSizer(3, 2, 5, 5)
        grid.Add(wx.StaticText(panel, label="工作时间(分钟):"))
        self.work_spin = wx.SpinCtrl(panel, value=str(self.config.work_time))
        grid.Add(self.work_spin)
        
        grid.Add(wx.StaticText(panel, label="休息时间(分钟):"))
        self.rest_spin = wx.SpinCtrl(panel, value=str(self.config.rest_time))
        grid.Add(self.rest_spin)
        
        # 添加快捷键配置
        grid.Add(wx.StaticText(panel, label="提前休息快捷键:"))
        hotkey_box = wx.BoxSizer(wx.HORIZONTAL)
        self.hotkey_text = wx.TextCtrl(panel, value=self.config.hotkey)
        self.hotkey_btn = wx.Button(panel, label="确定", size=(50, -1))
        self.hotkey_btn.Bind(wx.EVT_BUTTON, self.on_set_hotkey)
        hotkey_box.Add(self.hotkey_text, 1, wx.RIGHT, 5)
        hotkey_box.Add(self.hotkey_btn, 0)
        grid.Add(hotkey_box)
        
        # 添加开始/停止按钮
        self.toggle_btn = wx.Button(panel, label="开始")
        self.toggle_btn.Bind(wx.EVT_BUTTON, self.on_toggle)
        
        # 添加提前休息按钮
        self.force_rest_btn = wx.Button(panel, label="提前休息")
        self.force_rest_btn.Bind(wx.EVT_BUTTON, self.on_force_rest)
        
        # 添加状态显示
        self.status = wx.StaticText(panel, label="就绪")
        
        # 布局
        vbox.Add(grid, 0, wx.ALL|wx.CENTER, 10)
        vbox.Add(self.toggle_btn, 0, wx.ALL|wx.EXPAND, 5)
        vbox.Add(self.force_rest_btn, 0, wx.ALL|wx.EXPAND, 5)
        vbox.Add(self.status, 0, wx.ALL|wx.CENTER, 5)
        
        panel.SetSizer(vbox)

    def _init_hotkey(self):
        try:
            keyboard.remove_hotkey(self.config.hotkey)
        except:
            pass
        keyboard.add_hotkey(self.config.hotkey, self.on_force_rest)

    def force_rest_timer(self):
        # 设置休息状态
        self.is_resting = True
        
        # 休息时间
        wx.CallAfter(self.rest_screen.Show)
        wx.CallAfter(self.rest_screen.Maximize, True)
        wx.CallAfter(self.status.SetLabel, "休息时间")
        
        # 等待休息时间结束
        time.sleep(self.config.rest_time * 60)
        
        # 自动解锁并重置工作计时器
        if self.is_working:  # 只在程序仍在运行时执行
            wx.CallAfter(self.rest_screen.Hide)
            # 设置为非休息状态
            self.is_resting = False
            # 重新启动工作计时器
            if self.timer_thread and self.timer_thread.is_alive():
                self.timer_thread = threading.Thread(target=self.timer_func)
                self.timer_thread.daemon = True
                self.timer_thread.start()
        
    def on_force_rest(self, event=None):
        # 如果当前正在休息，重置休息计时器
        if self.is_resting:
            if self.force_rest_thread and self.force_rest_thread.is_alive():
                self.force_rest_thread = threading.Thread(target=self.force_rest_timer)
                self.force_rest_thread.daemon = True
                self.force_rest_thread.start()
        else:
            # 如果没有在休息，启动休息计时器
            if not self.force_rest_thread or not self.force_rest_thread.is_alive():
                self.force_rest_thread = threading.Thread(target=self.force_rest_timer)
                self.force_rest_thread.daemon = True
                self.force_rest_thread.start()
        
    def on_toggle(self, event):
        if not self.is_working:
            # 开始计时
            self.config.work_time = self.work_spin.GetValue()
            self.config.rest_time = self.rest_spin.GetValue()
            self.config.save()  # 保存配置
            self.is_working = True
            self.toggle_btn.SetLabel("停止")
            self.timer_thread = threading.Thread(target=self.timer_func)
            self.timer_thread.daemon = True
            self.timer_thread.start()
            self.Hide()  # 隐藏主窗口
        else:
            # 停止计时
            self.is_working = False
            self.is_resting = False  # 重置休息状态
            self.toggle_btn.SetLabel("开始")
            self.status.SetLabel("就绪")
            self.rest_screen.Hide()
            
    def timer_func(self):
        while self.is_working:
            # 工作时间
            for i in range(self.config.work_time * 60, -1, -1):
                if not self.is_working:
                    return
                wx.CallAfter(self.status.SetLabel, f"工作中: 还剩 {i//60}:{i%60:02d}")
                time.sleep(1)
            
            # 休息时间
            if not self.is_working:
                return
                
            self.is_resting = True  # 设置休息状态
            wx.CallAfter(self.rest_screen.Show)
            wx.CallAfter(self.rest_screen.Maximize, True)  # 确保最大化
            wx.CallAfter(self.status.SetLabel, "休息时间")
            
            for i in range(self.config.rest_time * 60, -1, -1):
                if not self.is_working:
                    wx.CallAfter(self.rest_screen.Hide)
                    return
                if i == 0:  # 休息时间结束时自动解锁
                    wx.CallAfter(self.rest_screen.Hide)
                    self.is_resting = False  # 重置休息状态
                time.sleep(1)

    def on_set_hotkey(self, event):
        new_hotkey = self.hotkey_text.GetValue().strip()
        if new_hotkey:
            try:
                # 先移除旧的热键
                keyboard.remove_hotkey(self.config.hotkey)
                # 尝试注册新的热键
                keyboard.add_hotkey(new_hotkey, self.on_force_rest)
                # 注册成功后更新配置
                self.config.hotkey = new_hotkey
                self.config.save()
                wx.MessageBox("快捷键设置成功", "提示")
            except Exception as e:
                wx.MessageBox(f"快捷键设置失败: {str(e)}", "错误")
                # 恢复旧的热键
                keyboard.add_hotkey(self.config.hotkey, self.on_force_rest)
                self.hotkey_text.SetValue(self.config.hotkey)
                
    def on_close(self, event):
        if self.real_close:  # 如果是真正的关闭操作
            self.is_working = False
            self.is_resting = False
            try:
                keyboard.remove_hotkey(self.config.hotkey)  # 移除热键
            except:
                pass
            self.taskbar_icon.Destroy()
            self.rest_screen.Destroy()
            event.Skip()
        else:  # 如果是点击关闭按钮
            self.Hide()
            wx.adv.NotificationMessage(
                "护眼助手",
                "程序已最小化到系统托盘，双击图标可以重新打开主窗口",
                parent=None).Show()
