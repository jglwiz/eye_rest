import wx
import wx.adv
import threading
import time
from lib.rest_screen import RestScreen
from lib.taskbar import TaskBarIcon
from lib.config import Config
from lib.hotkey_manager import HotkeyManager

class MainFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="护眼助手", size=(300, 250))
        
        self.config = Config()
        self.is_running = False  # 是否开启提醒
        self.is_working = True   # 是否在工作状态
        self.rest_screen = RestScreen()  # 创建休息窗口
        self.real_close = False
        
        # 创建系统托盘图标
        self.taskbar_icon = TaskBarIcon(self)
        
        # 初始化热键管理器
        self.hotkey_manager = HotkeyManager()
        
        self._init_ui()
        self._init_hotkey()
        
        # 创建永久运行的计时器线程
        self.timer_thread = threading.Thread(target=self.timer_func)
        self.timer_thread.daemon = True
        
        # 添加线程锁
        self.thread_lock = threading.Lock()
        
        # 工作结束时间
        self.work_end_time = time.time()
        
        # 绑定关闭事件
        self.Bind(wx.EVT_CLOSE, self.on_close)
        
        # 居中显示
        self.Center()

    def _init_ui(self):
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        # 添加配置控件
        grid = wx.FlexGridSizer(5, 2, 5, 5)
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

        # 添加声音和密码选项
        grid.Add(wx.StaticText(panel, label="休息结束时播放声音:"))
        self.sound_checkbox = wx.CheckBox(panel)
        self.sound_checkbox.SetValue(self.config.play_sound_after_rest)
        grid.Add(self.sound_checkbox)

        grid.Add(wx.StaticText(panel, label="允许密码提前结束休息:"))
        self.password_checkbox = wx.CheckBox(panel)
        self.password_checkbox.SetValue(self.config.allow_password_skip)
        grid.Add(self.password_checkbox)
        
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
        """初始化全局热键"""
        try:
            self.hotkey_manager.register_hotkey(self.config.hotkey, self.on_force_rest)
        except Exception as e:
            wx.MessageBox(f"初始化热键失败: {str(e)}", "错误")

    def on_rest_complete(self):
        """休息完成回调"""
        with self.thread_lock:
            self.is_working = True
            # 设置下一个工作结束时间
            self.work_end_time = time.time() + self.config.work_time * 60
            wx.CallAfter(self.status.SetLabel, "工作中")

    def on_rest_cancel(self):
        """休息取消回调"""
        with self.thread_lock:
            self.is_working = True
            # 重置工作计时
            self.work_end_time = time.time() + self.config.work_time * 60
            wx.CallAfter(self.status.SetLabel, "工作中")

    def start_rest(self):
        """开始休息"""
        self.is_working = False
        # 确保在主线程中执行UI操作
        wx.CallAfter(self.rest_screen.start_rest,
            self.config.rest_time,
            on_complete=self.on_rest_complete,
            on_cancel=self.on_rest_cancel,
            config=self.config
        )
        wx.CallAfter(self.status.SetLabel, "休息时间")

    def on_force_rest(self, event=None):
        """处理提前休息"""
        with self.thread_lock:
            if not self.is_running:
                # 如果程序未运行，先启动程序
                self.is_running = True
                self.toggle_btn.SetLabel("停止")
                if not self.timer_thread.is_alive():
                    self.timer_thread.start()
            
            if not self.is_working:
                # 如果当前正在休息，增加1分钟休息时间
                wx.CallAfter(self.rest_screen.reset_timer)
            else:
                # 开始新的休息
                self.start_rest()
            
    def on_toggle(self, event):
        with self.thread_lock:
            if not self.is_running:
                # 开始计时
                self.config.work_time = self.work_spin.GetValue()
                self.config.rest_time = self.rest_spin.GetValue()
                self.config.play_sound_after_rest = self.sound_checkbox.GetValue()
                self.config.allow_password_skip = self.password_checkbox.GetValue()
                self.config.save()  # 保存配置
                self.is_running = True
                self.is_working = True
                self.toggle_btn.SetLabel("停止")
                # 设置初始工作结束时间
                self.work_end_time = time.time() + self.config.work_time * 60
                if not self.timer_thread.is_alive():
                    self.timer_thread.start()
                self.Hide()  # 隐藏主窗口
            else:
                # 停止计时
                self.is_running = False
                self.is_working = True
                self.toggle_btn.SetLabel("开始")
                self.status.SetLabel("就绪")
                self.rest_screen.stop_rest(cancelled=True)
            
    def timer_func(self):
        """永久运行的计时器线程，只负责工作时间管理"""
        while True:
            with self.thread_lock:
                if not self.is_running:
                    time.sleep(0.5)
                    continue
                    
                if self.is_working:
                    current_time = time.time()
                    if current_time >= self.work_end_time:
                        # 工作结束，开始休息
                        self.start_rest()
                    else:
                        remaining = int(self.work_end_time - current_time)
                        if remaining > 0:
                            wx.CallAfter(self.status.SetLabel, f"工作中: 还剩 {remaining//60}:{remaining%60:02d}")
                
            time.sleep(1)

    def on_set_hotkey(self, event):
        new_hotkey = self.hotkey_text.GetValue().strip()
        if new_hotkey:
            try:
                # 注册新热键
                self.hotkey_manager.register_hotkey(new_hotkey, self.on_force_rest)
                
                # 更新配置
                self.config.hotkey = new_hotkey
                self.config.save()
                
                wx.MessageBox("快捷键设置成功", "提示")
            except Exception as e:
                wx.MessageBox(f"快捷键设置失败: {str(e)}", "错误")
                # 恢复原来的热键
                self.hotkey_text.SetValue(self.config.hotkey)
                
    def on_close(self, event):
        if self.real_close:  # 如果是真正的关闭操作
            self.is_running = False  # 停止计时器线程
            if self.hotkey_manager:
                self.hotkey_manager.stop()  # 停止热键监听
                self.hotkey_manager = None
            self.taskbar_icon.Destroy()
            self.rest_screen.Destroy()
            event.Skip()
        else:  # 如果是点击关闭按钮
            self.Hide()
            wx.adv.NotificationMessage(
                "护眼助手",
                "程序已最小化到系统托盘，双击图标可以重新打开主窗口",
                parent=None).Show()
