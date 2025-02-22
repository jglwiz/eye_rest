import wx
import time
import winsound
import win32gui
import win32con
import win32api
import win32com.client
from datetime import datetime

class RestScreen(wx.Frame):
    """休息界面，负责管理休息时间和UI显示"""
    
    def __init__(self):
        """初始化休息界面"""
        style = (wx.FRAME_NO_TASKBAR | wx.STAY_ON_TOP | wx.BORDER_NONE)
        super().__init__(None, style=style)
        
        # 配置对象
        self.config = None
        
        # 设置窗口扩展样式
        self._set_window_style()
        
        # 回调函数
        self.on_rest_complete = None  # 休息完成回调
        self.on_rest_cancel = None    # 休息取消回调
        
        # 状态标志
        self.is_resting = False
        
        # 获取屏幕大小并设置窗口
        self.screen = wx.Display().GetGeometry()
        self.SetSize(self.screen)
        self.SetPosition((0, 0))
        
        # 设置黑色背景
        self.SetBackgroundColour(wx.BLACK)
        
        # 计时相关
        self.rest_seconds = 0      # 总休息时间（秒）
        self.remaining_seconds = 0  # 剩余时间（秒）
        self.last_add_time = 0     # 上次增加时间的时间戳
        self.add_cooldown = 1      # 增加时间的冷却时间（秒）
        
        # 创建主面板
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        # 添加当前时间显示
        self.time_text = wx.StaticText(panel, label="                  ", style=wx.ALIGN_CENTER)
        self.time_text.SetForegroundColour(wx.WHITE)
        time_font = wx.Font(48, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        self.time_text.SetFont(time_font)
        
        # 添加倒计时显示
        self.countdown_text = wx.StaticText(panel, label="                  ", style=wx.ALIGN_CENTER) 
        self.countdown_text.SetForegroundColour(wx.WHITE)
        countdown_font = wx.Font(48, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        self.countdown_text.SetFont(countdown_font)
        
        # 添加提示文本
        self.hint = wx.StaticText(panel, label="按快捷键可增加1分钟休息时间", style=wx.ALIGN_CENTER)
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
    
    def start_rest(self, minutes, on_complete=None, on_cancel=None, config=None):
        """开始休息
        Args:
            minutes: 休息时间（分钟）
            on_complete: 休息完成时的回调函数
            on_cancel: 休息被取消时的回调函数
            config: 配置对象
        """
        self.config = config
        self.rest_seconds = minutes * 60
        self.remaining_seconds = self.rest_seconds
        self.on_rest_complete = on_complete
        self.on_rest_cancel = on_cancel
        self.is_resting = True
        
        def show_and_setup():
            self.Show()
            self.Maximize(True)
            self._set_window_style()  # 确保窗口在所有虚拟桌面上显示
        
        # 确保所有UI操作在主线程中执行
        wx.CallAfter(show_and_setup)
        
        # 根据配置更新提示信息
        if self.config and self.config.allow_password_skip:
            wx.CallAfter(self.hint.SetLabel, "请输入123456789以解锁\n按快捷键可增加1分钟休息时间")
        else:
            wx.CallAfter(self.hint.SetLabel, "按快捷键可增加1分钟休息时间")
            
        wx.CallAfter(self.input.SetFocus)
        wx.CallAfter(self.timer.Start, 1000)
        
    def stop_rest(self, cancelled=False):
        """停止休息
        Args:
            cancelled: 是否是被取消的（True表示提前退出，False表示正常完成）
        """
        self.is_resting = False
        # 确保所有UI操作在主线程中执行
        wx.CallAfter(self.timer.Stop)
        wx.CallAfter(self.Hide)
        wx.CallAfter(self.input.SetValue, "")
        
        # 在主线程中调用回调函数
        if cancelled and self.on_rest_cancel:
            wx.CallAfter(self.on_rest_cancel)
        elif not cancelled and self.on_rest_complete:
            wx.CallAfter(self.on_rest_complete)
            
    def update_display(self):
        """更新显示内容"""
        # 更新当前时间
        current_time = datetime.now().strftime("%H:%M:%S")
        self.time_text.SetLabel("当前时间: " + current_time)
        
        # 更新倒计时
        minutes = self.remaining_seconds // 60
        seconds = self.remaining_seconds % 60
        self.countdown_text.SetLabel(f"剩余时间: {minutes:02d}:{seconds:02d}")
        
    def on_timer(self, event):
        """定时器回调"""
        if not self.is_resting:
            return
            
        if self.remaining_seconds > 0:
            # 在剩余10秒时播放doremi音阶
            if self.remaining_seconds == 10 and self.config and self.config.play_sound_after_rest:
                # 播放do-re-mi音阶
                winsound.Beep(523, 200)  # do (C5)
                time.sleep(0.1)  # 短暂停顿
                winsound.Beep(587, 200)  # re (D5)
                time.sleep(0.1)  # 短暂停顿
                winsound.Beep(659, 200)  # mi (E5)
                time.sleep(0.1)
                winsound.Beep(784, 200)  # G5
                time.sleep(0.1)
                winsound.Beep(659, 200)  # E5
                time.sleep(0.1)
                winsound.Beep(523, 400)  # C5
            self.remaining_seconds -= 1
            self.update_display()
        else:
            self.stop_rest(cancelled=False)
        
    def on_key(self, event):
        """按键事件处理"""
        # 禁用Alt+F4和其他快捷键
        if event.AltDown():
            return
        event.Skip()
        
    def _set_window_style(self):
        """设置窗口扩展样式，使其在所有虚拟桌面上显示"""
        try:
            # 获取窗口句柄
            hwnd = self.GetHandle()
            
            # 获取当前窗口样式
            style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            
            # 添加置顶和工具窗口样式
            style |= win32con.WS_EX_TOPMOST
            style |= win32con.WS_EX_TOOLWINDOW
            
            # 应用新样式
            win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, style)
            
            # 设置窗口位置为顶层
            win32gui.SetWindowPos(
                hwnd,
                win32con.HWND_TOPMOST,
                0, 0, 0, 0,
                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE
            )
            
            # 尝试设置虚拟桌面固定属性
            try:
                # 使用 Windows 10+ 的虚拟桌面 API
                shell = win32com.client.Dispatch("Shell.Application")
                shell.PinToAllVirtualDesktops(hwnd, True)
            except:
                pass  # 如果 API 不可用，静默失败
                
        except Exception as e:
            print(f"设置窗口样式失败: {str(e)}")

    def on_show(self, event):
        """显示事件处理"""
        if event.IsShown():
            self.Maximize(True)
            self._set_window_style()  # 确保窗口样式正确设置
            self.input.SetFocus()
        event.Skip()
        
    def on_close(self, event):
        """关闭事件处理"""
        # 阻止窗口关闭，改为隐藏
        self.Hide()
        
    def on_moving(self, event):
        """移动事件处理"""
        # 获取所有显示器
        displays = [wx.Display(i) for i in range(wx.Display.GetCount())]
        
        # 遍历所有显示器并设置窗口
        for display in displays:
            geometry = display.GetGeometry()
            # 创建一个全屏窗口在每个显示器上
            self.SetPosition((geometry.x, geometry.y))
            self.SetSize(geometry.GetSize())
            
        # 重新应用窗口样式确保置顶和虚拟桌面固定
        self._set_window_style()

    def on_text(self, event):
        """文本输入事件处理"""
        # 如果不允许密码解锁，直接返回
        if not self.config or not self.config.allow_password_skip:
            return
            
        # 检查输入是否正确
        if self.input.GetValue() == "123456789123456789123456789":
            self.stop_rest(cancelled=True)
            
    def on_enter(self, event):
        """回车键事件处理"""
        # 如果不允许密码解锁，显示提示
        if not self.config or not self.config.allow_password_skip:
            self.input.SetValue("")
            self.hint.SetLabel("当前不允许使用密码提前结束休息\n按快捷键可重置休息时间")
            return
            
        # 回车时检查输入
        if self.input.GetValue() != "123456789123456789123456789":
            self.input.SetValue("")
            self.hint.SetLabel("输入错误,请重试\n按快捷键可重置休息时间")
            
    def reset_timer(self):
        """增加休息时间，带有冷却保护"""
        if not self.is_resting:
            return False
            
        current_time = time.time()
        # 检查是否在冷却时间内
        if current_time - self.last_add_time < self.add_cooldown:
            if self.config and self.config.allow_password_skip:
                self.hint.SetLabel(f"请等待{self.add_cooldown}秒后再增加时间\n请输入123456789以解锁")
            else:
                self.hint.SetLabel(f"请等待{self.add_cooldown}秒后再增加时间")
            return False
            
        # 增加1分钟
        self.remaining_seconds += 60
        self.last_add_time = current_time
        self.update_display()
        if self.config and self.config.allow_password_skip:
            self.hint.SetLabel("已增加1分钟休息时间\n请输入三遍123456789以解锁")
        else:
            self.hint.SetLabel("已增加1分钟休息时间")
        return True
