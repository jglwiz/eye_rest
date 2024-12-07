import wx
import time
from datetime import datetime

class RestScreen(wx.Frame):
    def __init__(self, rest_minutes=20, on_early_exit=None):
        # 创建全屏无边框窗口，始终置顶
        style = (wx.FRAME_NO_TASKBAR | wx.STAY_ON_TOP | wx.BORDER_NONE)
        super().__init__(None, style=style)
        
        # 保存回调函数
        self.on_early_exit = on_early_exit
        
        # 获取屏幕大小并设置窗口
        self.screen = wx.Display().GetGeometry()
        self.SetSize(self.screen)
        self.SetPosition((0, 0))
        
        # 设置黑色背景
        self.SetBackgroundColour(wx.BLACK)
        
        # 初始化休息时间
        self.rest_seconds = rest_minutes * 60
        self.remaining_seconds = self.rest_seconds
        
        # 添加重置保护标志
        self.last_reset_time = 0
        self.reset_cooldown = 2  # 重置冷却时间(秒)
        
        # 创建主面板
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        # 添加当前时间显示
        self.time_text = wx.StaticText(panel, label="", style=wx.ALIGN_CENTER)
        self.time_text.SetForegroundColour(wx.WHITE)
        time_font = wx.Font(48, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        self.time_text.SetFont(time_font)
        
        # 添加倒计时显示
        self.countdown_text = wx.StaticText(panel, label="", style=wx.ALIGN_CENTER)
        self.countdown_text.SetForegroundColour(wx.WHITE)
        countdown_font = wx.Font(48, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        self.countdown_text.SetFont(countdown_font)
        
        # 添加提示文本
        self.hint = wx.StaticText(panel, label="请输入123456789以解锁\n按快捷键可重置休息时间", style=wx.ALIGN_CENTER)
        self.hint.SetForegroundColour(wx.WHITE)
        hint_font = wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        self.hint.SetFont(hint_font)
        
        # 添加输入框
        self.input = wx.TextCtrl(panel, style=wx.TE_PASSWORD|wx.TE_PROCESS_ENTER)
        self.input.Bind(wx.EVT_TEXT_ENTER, self.on_enter)
        self.input.Bind(wx.EVT_TEXT, self.on_text)
        
        # 布局
        vbox.AddStretchSpacer(1)  # 上方弹性空间
        vbox.Add(self.time_text, 0, wx.ALL|wx.ALIGN_CENTER, 5)
        vbox.AddSpacer(30)  # 时间和倒计时之间的间距
        vbox.Add(self.countdown_text, 0, wx.ALL|wx.ALIGN_CENTER, 5)
        vbox.AddStretchSpacer(2)  # 下方弹性空间
        vbox.Add(self.hint, 0, wx.ALL|wx.ALIGN_CENTER, 5)
        vbox.Add(self.input, 0, wx.ALL|wx.ALIGN_CENTER, 5)
        vbox.AddSpacer(50)
        panel.SetSizer(vbox)
        
        # 绑定事件
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.Bind(wx.EVT_MOVING, self.on_moving)
        self.Bind(wx.EVT_SHOW, self.on_show)
        self.Bind(wx.EVT_CHAR_HOOK, self.on_key)
        
        # 创建定时器
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_timer)
        self.timer.Start(1000)  # 每秒更新一次
        
        # 初始更新显示
        self.update_display()
        
    def update_display(self):
        # 更新当前时间
        current_time = datetime.now().strftime("%H:%M:%S")
        self.time_text.SetLabel("当前时间: " + current_time)
        
        # 更新倒计时
        minutes = self.remaining_seconds // 60
        seconds = self.remaining_seconds % 60
        self.countdown_text.SetLabel(f"休息时间还剩: {minutes:02d}:{seconds:02d}")
        
    def on_timer(self, event):
        if self.remaining_seconds > 0:
            self.remaining_seconds -= 1
        self.update_display()
        
    def on_key(self, event):
        # 禁用Alt+F4和其他快捷键
        if event.AltDown():
            return
        event.Skip()
        
    def on_show(self, event):
        if event.IsShown():
            self.Maximize(True)
            self.input.SetFocus()
            # 重置倒计时
            self.remaining_seconds = self.rest_seconds
            # 重置上次重置时间
            self.last_reset_time = time.time()
        event.Skip()
        
    def on_close(self, event):
        # 阻止窗口关闭
        pass
        
    def on_moving(self, event):
        # 阻止窗口移动
        self.SetPosition((0, 0))

    def on_text(self, event):
        # 检查输入是否正确
        if self.input.GetValue() == "123456789":
            self.Hide()
            self.input.SetValue("")
            # 调用回调函数通知提前退出
            if self.on_early_exit:
                self.on_early_exit()
            
    def on_enter(self, event):
        # 回车时检查输入
        if self.input.GetValue() != "123456789":
            self.input.SetValue("")
            self.hint.SetLabel("输入错误,请重试")
            
    def reset_timer(self):
        """重置休息时间，带有冷却保护"""
        current_time = time.time()
        # 检查是否在冷却时间内
        if current_time - self.last_reset_time < self.reset_cooldown:
            self.hint.SetLabel(f"请等待{self.reset_cooldown}秒后再重置\n请输入123456789以解锁")
            return False
            
        # 重置时间
        self.remaining_seconds = self.rest_seconds
        self.last_reset_time = current_time
        self.update_display()
        self.hint.SetLabel("休息时间已重置\n请输入123456789以解锁")
        return True
