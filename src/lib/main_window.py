import wx
import wx.adv
from .rest_screen import RestScreen
from .taskbar import TaskBarIcon
from .app_core import EyeRestCore

class MainFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="护眼助手", size=(350, 300))
        
        # 创建核心业务逻辑
        self.core = EyeRestCore()
        
        # 创建休息窗口
        self.rest_screen = RestScreen()
        self.real_close = False
        
        # 创建系统托盘图标
        self.taskbar_icon = TaskBarIcon(self)
        
        # 设置核心逻辑的回调
        self.core.on_status_change = self.on_status_change
        self.core.on_start_rest = self.on_start_rest
        self.core.on_work_complete = self.on_work_complete
        
        self._init_ui()
        
        # 绑定关闭事件
        self.Bind(wx.EVT_CLOSE, self.on_close)
        
        # 居中显示
        self.Center()

    def _init_ui(self):
        """初始化UI界面"""
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        # 添加配置控件
        grid = wx.FlexGridSizer(7, 2, 5, 5)
        grid.Add(wx.StaticText(panel, label="工作时间(分钟):"))
        self.work_spin = wx.SpinCtrl(panel, value=str(self.core.config.work_time))
        grid.Add(self.work_spin)
        
        grid.Add(wx.StaticText(panel, label="休息时间(分钟):"))
        self.rest_spin = wx.SpinCtrl(panel, value=str(self.core.config.rest_time))
        grid.Add(self.rest_spin)
        
        # 添加空闲检测配置
        grid.Add(wx.StaticText(panel, label="启用离开检测:"))
        self.idle_detection_checkbox = wx.CheckBox(panel)
        self.idle_detection_checkbox.SetValue(self.core.config.idle_detection_enabled)
        grid.Add(self.idle_detection_checkbox)
        
        grid.Add(wx.StaticText(panel, label="离开检测时间(分钟):"))
        self.idle_threshold_spin = wx.SpinCtrl(panel, value=str(self.core.config.idle_threshold_minutes), min=1, max=30)
        grid.Add(self.idle_threshold_spin)
        
        # 添加快捷键配置
        grid.Add(wx.StaticText(panel, label="提前休息快捷键:"))
        hotkey_box = wx.BoxSizer(wx.HORIZONTAL)
        self.hotkey_text = wx.TextCtrl(panel, value=self.core.config.hotkey)
        self.hotkey_btn = wx.Button(panel, label="确定", size=(50, -1))
        self.hotkey_btn.Bind(wx.EVT_BUTTON, self.on_set_hotkey)
        hotkey_box.Add(self.hotkey_text, 1, wx.RIGHT, 5)
        hotkey_box.Add(self.hotkey_btn, 0)
        grid.Add(hotkey_box)

        # 添加声音和密码选项
        grid.Add(wx.StaticText(panel, label="休息结束时播放声音:"))
        self.sound_checkbox = wx.CheckBox(panel)
        self.sound_checkbox.SetValue(self.core.config.play_sound_after_rest)
        grid.Add(self.sound_checkbox)

        grid.Add(wx.StaticText(panel, label="允许密码提前结束休息:"))
        self.password_checkbox = wx.CheckBox(panel)
        self.password_checkbox.SetValue(self.core.config.allow_password_skip)
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

    def on_status_change(self, status):
        """状态变化回调 - 更新UI显示"""
        self.status.SetLabel(status)
        # 更新托盘图标状态
        if hasattr(self.core, 'current_state'):
            self.taskbar_icon.update_icon_by_state(self.core.current_state)

    def on_start_rest(self, rest_minutes):
        """开始休息回调 - 显示休息界面"""
        self.rest_screen.start_rest(
            minutes=rest_minutes,
            config=self.core.config,
            on_complete=self.core.on_rest_complete,
            on_cancel=self.core.on_rest_cancel
        )

    def on_work_complete(self, action):
        """工作完成回调"""
        if action == "add_time":
            # 增加休息时间
            self.rest_screen.add_rest_time()

    def on_force_rest(self, event=None):
        """处理提前休息按钮"""
        success = self.core.force_rest()
        if not success:
            # 如果程序未运行，自动启动
            work_time = self.work_spin.GetValue()
            rest_time = self.rest_spin.GetValue()
            play_sound = self.sound_checkbox.GetValue()
            allow_password = self.password_checkbox.GetValue()
            
            # 保存空闲检测配置
            self.core.config.idle_detection_enabled = self.idle_detection_checkbox.GetValue()
            self.core.config.idle_threshold_minutes = self.idle_threshold_spin.GetValue()
            
            self.core.start_work_session(work_time, rest_time, play_sound, allow_password)
            self.toggle_btn.SetLabel("停止")
            self.Hide()
            
            # 再次尝试强制休息
            self.core.force_rest()
            
    def on_toggle(self, event):
        """处理开始/停止按钮"""
        if not self.core.is_running:
            # 开始工作会话
            work_time = self.work_spin.GetValue()
            rest_time = self.rest_spin.GetValue()
            play_sound = self.sound_checkbox.GetValue()
            allow_password = self.password_checkbox.GetValue()
            
            # 保存空闲检测配置
            self.core.config.idle_detection_enabled = self.idle_detection_checkbox.GetValue()
            self.core.config.idle_threshold_minutes = self.idle_threshold_spin.GetValue()
            
            self.core.start_work_session(work_time, rest_time, play_sound, allow_password)
            self.toggle_btn.SetLabel("停止")
            self.Hide()  # 隐藏主窗口
        else:
            # 停止工作会话
            self.core.stop_work_session()
            self.toggle_btn.SetLabel("开始")
            self.rest_screen.stop_rest(cancelled=True)

    def on_set_hotkey(self, event):
        """处理设置热键"""
        new_hotkey = self.hotkey_text.GetValue().strip()
        if new_hotkey:
            success = self.core.update_hotkey(new_hotkey)
            if success:
                wx.MessageBox("快捷键设置成功", "提示")
            else:
                wx.MessageBox("快捷键设置失败，请检查格式", "错误")
                # 恢复原来的热键
                self.hotkey_text.SetValue(self.core.config.hotkey)
                
    def on_close(self, event):
        """处理窗口关闭事件"""
        if self.real_close:  # 如果是真正的关闭操作
            self.core.cleanup()  # 清理核心逻辑资源
            self.taskbar_icon.Destroy()
            self.rest_screen.Destroy()
            event.Skip()
        else:  # 如果是点击关闭按钮
            self.Hide()
            wx.adv.NotificationMessage(
                "护眼助手",
                "程序已最小化到系统托盘，双击图标可以重新打开主窗口",
                parent=None).Show()
