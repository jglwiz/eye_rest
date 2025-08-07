import wx
import win32gui
import win32con
import win32api
import win32com.client
from .rest_manager import RestManager
from .hourly_chart import DarkHourlyChart
from .statistics_manager import StatisticsManager
import threading

class PasswordDialog(wx.Dialog):
    """密码输入对话框"""
    
    def __init__(self, parent, rest_manager):
        super().__init__(parent, title="解锁休息屏幕", style=wx.DEFAULT_DIALOG_STYLE)
        self.rest_manager = rest_manager
        self.SetSize((400, 150))
        self.SetBackgroundColour(wx.Colour(40, 40, 40))  # 深灰色背景
        
        # 创建UI
        panel = wx.Panel(self)
        panel.SetBackgroundColour(wx.Colour(40, 40, 40))
        
        # 密码输入框
        self.password_input = wx.TextCtrl(panel, style=wx.TE_PASSWORD|wx.TE_PROCESS_ENTER)
        self.password_input.Bind(wx.EVT_TEXT_ENTER, self.on_enter)
        
        # 按钮
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ok_btn = wx.Button(panel, wx.ID_OK, "确定")
        ok_btn.SetBackgroundColour(wx.Colour(60, 60, 60))
        ok_btn.SetForegroundColour(wx.WHITE)
        cancel_btn = wx.Button(panel, wx.ID_CANCEL, "取消")
        cancel_btn.SetBackgroundColour(wx.Colour(60, 60, 60))
        cancel_btn.SetForegroundColour(wx.WHITE)
        btn_sizer.Add(ok_btn, 0, wx.ALL, 5)
        btn_sizer.Add(cancel_btn, 0, wx.ALL, 5)
        
        # 布局
        sizer = wx.BoxSizer(wx.VERTICAL)
        hint_label = wx.StaticText(panel, label="请输入三遍123456789解锁", style=wx.ALIGN_CENTER)
        hint_label.SetForegroundColour(wx.WHITE)
        sizer.Add(hint_label, 0, wx.ALL|wx.ALIGN_CENTER, 10)
        sizer.Add(self.password_input, 0, wx.ALL|wx.EXPAND, 10)
        sizer.Add(btn_sizer, 0, wx.ALL|wx.ALIGN_CENTER, 10)
        
        panel.SetSizer(sizer)
        
        # 绑定事件
        ok_btn.Bind(wx.EVT_BUTTON, self.on_ok)
        cancel_btn.Bind(wx.EVT_BUTTON, self.on_cancel)
        
        # 设置焦点
        self.password_input.SetFocus()
        
        # 居中显示
        self.CenterOnParent()
        
    def on_enter(self, event):
        """回车键处理"""
        self.on_ok(event)
        
    def on_ok(self, event):
        """确定按钮处理"""
        password = self.password_input.GetValue()
        is_correct, message = self.rest_manager.check_password(password)
        
        if is_correct:
            self.EndModal(wx.ID_OK)
        else:
            # 密码错误，显示提示并清空输入框
            wx.MessageBox("密码错误，请重试", "错误", wx.OK | wx.ICON_ERROR)
            self.password_input.SetValue("")
            self.password_input.SetFocus()
            
    def on_cancel(self, event):
        """取消按钮处理"""
        self.EndModal(wx.ID_CANCEL)

class RestScreen(wx.Frame):
    """休息界面，只负责UI显示"""
    
    def __init__(self, core=None):
        """初始化休息界面"""
        style = (wx.FRAME_NO_TASKBAR | wx.STAY_ON_TOP | wx.BORDER_NONE)
        super().__init__(None, style=style)
        
        # 创建休息管理器
        self.rest_manager = RestManager()
        
        # 使用传入的core获取统计管理器，而不是创建新实例
        self.core = core
        
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
        panel.SetBackgroundColour(wx.BLACK)
        
        # 创建垂直布局（两列）
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 1. 休息倒计时区域
        time_panel = wx.Panel(panel)
        time_panel.SetBackgroundColour(wx.BLACK)
        time_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 添加当前时间显示
        self.time_text = wx.StaticText(time_panel, label="                  ", style=wx.ALIGN_CENTER)
        self.time_text.SetForegroundColour(wx.WHITE)
        time_font = wx.Font(36, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        self.time_text.SetFont(time_font)
        
        # 添加倒计时显示
        self.countdown_text = wx.StaticText(time_panel, label="                  ", style=wx.ALIGN_CENTER) 
        self.countdown_text.SetForegroundColour(wx.WHITE)
        countdown_font = wx.Font(48, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        self.countdown_text.SetFont(countdown_font)
        
        # 时间面板布局
        time_sizer.Add(self.time_text, 0, wx.ALL|wx.ALIGN_CENTER, 5)
        time_sizer.AddSpacer(20)
        time_sizer.Add(self.countdown_text, 0, wx.ALL|wx.ALIGN_CENTER, 5)
        time_panel.SetSizer(time_sizer)
        
        # 2. 小时统计图区域 - 设置固定高度40%
        chart_panel = wx.Panel(panel)
        chart_panel.SetBackgroundColour(wx.BLACK)
        chart_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 设置图表区域高度为屏幕高度的40%
        chart_height = int(self.screen.height * 0.4)
        chart_panel.SetMinSize((-1, chart_height))
        chart_panel.SetMaxSize((-1, chart_height))
        
        # 统计图标题
        chart_title = wx.StaticText(chart_panel, label="今日小时统计", style=wx.ALIGN_CENTER)
        chart_title.SetForegroundColour(wx.WHITE)
        title_font = wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        chart_title.SetFont(title_font)
        
        # 创建图表容器，用于控制图表宽度
        chart_container = wx.Panel(chart_panel)
        chart_container.SetBackgroundColour(wx.BLACK)
        chart_container_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # 创建小时统计图
        self.hourly_chart = DarkHourlyChart(chart_container)
        
        # 图表容器布局：左右留空，图表居中，增加图表宽度
        chart_container_sizer.AddStretchSpacer(1)  # 左侧弹性空间
        chart_container_sizer.Add(self.hourly_chart, 3, wx.EXPAND)  # 图表占3份，增加宽度
        chart_container_sizer.AddStretchSpacer(1)  # 右侧弹性空间
        chart_container.SetSizer(chart_container_sizer)
        
        # 图表面板布局
        chart_sizer.Add(chart_title, 0, wx.ALL|wx.ALIGN_CENTER, 10)
        chart_sizer.Add(chart_container, 1, wx.ALL|wx.EXPAND, 20)
        chart_panel.SetSizer(chart_sizer)
        
        # 3. 右下角解锁按钮
        self.unlock_btn = wx.Button(panel, label="解锁", size=(80, 35))
        self.unlock_btn.SetBackgroundColour(wx.Colour(60, 60, 60))
        self.unlock_btn.SetForegroundColour(wx.WHITE)
        self.unlock_btn.Bind(wx.EVT_BUTTON, self.on_unlock_click)
        
        # 主布局：垂直排列，图表靠近底部但留出按钮空间
        main_sizer.AddSpacer(50)  # 顶部间距
        main_sizer.Add(time_panel, 0, wx.ALL|wx.EXPAND, 20)  # 倒计时区域
        main_sizer.AddStretchSpacer(1)  # 中间弹性空间
        main_sizer.Add(chart_panel, 0, wx.ALL|wx.EXPAND, 20)  # 图表区域（固定高度40%）
        main_sizer.AddSpacer(80)  # 底部留出空间给解锁按钮
        
        panel.SetSizer(main_sizer)
        
        # 使用绝对定位将按钮放在右下角
        def position_unlock_button():
            panel_size = panel.GetSize()
            btn_size = self.unlock_btn.GetSize()
            x = panel_size.width - btn_size.width - 20  # 右边距20像素
            y = panel_size.height - btn_size.height - 20  # 下边距20像素
            self.unlock_btn.SetPosition((x, y))
        
        # 绑定尺寸变化事件来重新定位按钮
        panel.Bind(wx.EVT_SIZE, lambda event: (position_unlock_button(), event.Skip()))
        wx.CallAfter(position_unlock_button)  # 初始定位
    
    def on_unlock_click(self, event):
        """解锁按钮点击事件"""
        # 创建并显示密码对话框
        dialog = PasswordDialog(self, self.rest_manager)
        result = dialog.ShowModal()
        
        if result == wx.ID_OK:
            # 密码正确，结束休息
            self.rest_manager.stop_rest(cancelled=True)
        
        dialog.Destroy()
    
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
            if on_complete:
                on_complete()
        
        def on_rest_cancel():
            wx.CallAfter(self.Hide)
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
        
        # 更新小时统计图 - 使用共享的统计管理器
        if self.core:
            hourly_data = self.core.get_statistics_manager().get_today_hourly_records()
        else:
            # 如果没有core，创建临时实例作为后备
            from .statistics_manager import StatisticsManager
            temp_stats = StatisticsManager()
            hourly_data = temp_stats.get_today_hourly_records()
        
        wx.CallAfter(self.hourly_chart.set_data, hourly_data)
        
        # 显示窗口
        def show_and_setup():
            self.Show()
            self.Maximize(True)
            self._set_window_style()
        
        wx.CallAfter(show_and_setup)
        
    def stop_rest(self, cancelled=False):
        """停止休息
        Args:
            cancelled: 是否是被取消的（True表示提前退出，False表示正常完成）
        """
        self.rest_manager.stop_rest(cancelled=cancelled)
        wx.CallAfter(self.Hide)
    
    def add_rest_time(self):
        """增加休息时间"""
        success, message = self.rest_manager.add_rest_time()
        return success
    
    def temp_pause(self):
        """临时暂停休息屏幕"""
        # 暂停休息管理器的计时
        if hasattr(self, 'rest_manager') and self.rest_manager:
            self.rest_manager.timer_running = False
            # 等待计时器线程结束
            if self.rest_manager.timer_thread and self.rest_manager.timer_thread.is_alive():
                self.rest_manager.timer_thread.join(timeout=1)
        
        wx.CallAfter(self.Hide)
    
    def temp_resume(self):
        """恢复休息屏幕"""
        # 恢复休息管理器的计时
        if hasattr(self, 'rest_manager') and self.rest_manager and self.rest_manager.is_resting:
            # 重新启动计时器线程
            self.rest_manager.timer_running = True
            self.rest_manager.timer_thread = threading.Thread(target=self.rest_manager._timer_func)
            self.rest_manager.timer_thread.daemon = True
            self.rest_manager.timer_thread.start()
            
            # 立即更新一次显示
            self.rest_manager._update_display()
        
        # 重新显示窗口
        def show_and_setup():
            self.Show()
            self.Maximize(True)
            self._set_window_style()
        
        wx.CallAfter(show_and_setup)
        
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
