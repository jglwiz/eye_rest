import wx
import win32gui
import win32con
import win32api
import win32com.client
from .rest_manager import RestManager

class RestScreen(wx.Frame):
    """休息界面，只负责UI显示"""
    
    def __init__(self):
        """初始化休息界面"""
        style = (wx.FRAME_NO_TASKBAR | wx.STAY_ON_TOP | wx.BORDER_NONE)
        super().__init__(None, style=style)
        
        # 创建休息管理器
        self.rest_manager = RestManager()
        
        # 设置窗口扩展样式
        self._set_window_style()
        
        # 获取屏幕大小并设置窗口
        self.screen = wx.Display().GetGeometry()
        self.SetSize(self.screen)
        self.SetPosition((0, 0))
        
        # 设置黑色背景
        self.SetBackgroundColour(wx.BLACK)
        
        # 创建UI组件
        self._init_ui()
        
        # 绑定事件
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.Bind(wx.EVT_MOVING, self.on_moving)
        self.Bind(wx.EVT_SHOW, self.on_show)
        self.Bind(wx.EVT_CHAR_HOOK, self.on_key)
        
    def _init_ui(self):
        """初始化UI组件"""
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
    
    def start_rest(self, minutes, config=None, on_complete=None, on_cancel=None):
        """开始休息
        Args:
            minutes: 休息时间（分钟）
            config: 配置对象
            on_complete: 休息完成时的回调函数
            on_cancel: 休息被取消时的回调函数
        """
        # 设置休息管理器的回调
        def on_update_display(data):
            wx.CallAfter(self._update_display, data)
        
        def on_rest_complete():
            wx.CallAfter(self.Hide)
            wx.CallAfter(self.input.SetValue, "")
            if on_complete:
                on_complete()
        
        def on_rest_cancel():
            wx.CallAfter(self.Hide)
            wx.CallAfter(self.input.SetValue, "")
            if on_cancel:
                on_cancel()
        
        # 启动休息管理器
        self.rest_manager.start_rest(
            minutes=minutes,
            config=config,
            on_complete=on_rest_complete,
            on_cancel=on_rest_cancel,
            on_update_display=on_update_display
        )
        
        # 更新提示信息
        hint_msg = self.rest_manager.get_hint_message()
        wx.CallAfter(self.hint.SetLabel, hint_msg)
        
        # 显示窗口
        def show_and_setup():
            self.Show()
            self.Maximize(True)
            self._set_window_style()
            self.input.SetFocus()
        
        wx.CallAfter(show_and_setup)
        
    def stop_rest(self, cancelled=False):
        """停止休息
        Args:
            cancelled: 是否是被取消的（True表示提前退出，False表示正常完成）
        """
        self.rest_manager.stop_rest(cancelled=cancelled)
        wx.CallAfter(self.Hide)
        wx.CallAfter(self.input.SetValue, "")
    
    def add_rest_time(self):
        """增加休息时间"""
        success, message = self.rest_manager.add_rest_time()
        if success:
            # 更新提示信息
            hint_msg = self.rest_manager.get_hint_message()
            wx.CallAfter(self.hint.SetLabel, hint_msg)
        else:
            # 显示错误信息
            wx.CallAfter(self.hint.SetLabel, message)
        return success
        
    def _update_display(self, data):
        """更新显示内容
        Args:
            data: 包含显示数据的字典
        """
        # 更新当前时间
        self.time_text.SetLabel("当前时间: " + data['current_time'])
        
        # 更新倒计时
        self.countdown_text.SetLabel(f"剩余时间: {data['remaining_display']}")
        
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
        password = self.input.GetValue()
        is_correct, message = self.rest_manager.check_password(password)
        
        if is_correct:
            # 密码正确，结束休息
            self.rest_manager.stop_rest(cancelled=True)
            
    def on_enter(self, event):
        """回车键事件处理"""
        password = self.input.GetValue()
        is_correct, message = self.rest_manager.check_password(password)
        
        if not is_correct:
            # 密码错误，清空输入框并显示提示
            self.input.SetValue("")
            if "不允许" in message:
                hint_msg = self.rest_manager.get_hint_message()
            else:
                hint_msg = self.rest_manager.get_hint_message(password_error=True)
            self.hint.SetLabel(hint_msg)
