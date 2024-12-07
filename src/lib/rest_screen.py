import wx

class RestScreen(wx.Frame):
    def __init__(self):
        # 创建全屏无边框窗口，始终置顶
        style = (wx.FRAME_NO_TASKBAR | wx.STAY_ON_TOP | wx.BORDER_NONE)
        super().__init__(None, style=style)
        
        # 获取屏幕大小并设置窗口
        self.screen = wx.Display().GetGeometry()
        self.SetSize(self.screen)
        self.SetPosition((0, 0))
        
        # 设置黑色背景
        self.SetBackgroundColour(wx.BLACK)
        
        # 创建解锁面板
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        # 添加提示文本
        self.hint = wx.StaticText(panel, label="请输入123456789以解锁", style=wx.ALIGN_CENTER)
        self.hint.SetForegroundColour(wx.WHITE)
        font = wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        self.hint.SetFont(font)
        
        # 添加输入框
        self.input = wx.TextCtrl(panel, style=wx.TE_PASSWORD|wx.TE_PROCESS_ENTER)
        self.input.Bind(wx.EVT_TEXT_ENTER, self.on_enter)
        self.input.Bind(wx.EVT_TEXT, self.on_text)
        
        # 布局
        vbox.Add((-1, self.screen.height - 100))  # 底部空白
        vbox.Add(self.hint, 0, wx.ALL|wx.ALIGN_CENTER, 5)
        vbox.Add(self.input, 0, wx.ALL|wx.ALIGN_CENTER, 5)
        panel.SetSizer(vbox)
        
        # 绑定事件，阻止窗口关闭和移动
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.Bind(wx.EVT_MOVING, self.on_moving)
        
        # 显示时自动获取焦点
        self.Bind(wx.EVT_SHOW, self.on_show)
        
        # 禁用Alt+F4
        self.Bind(wx.EVT_CHAR_HOOK, self.on_key)
        
    def on_key(self, event):
        # 禁用Alt+F4和其他快捷键
        if event.AltDown():
            return
        event.Skip()
        
    def on_show(self, event):
        if event.IsShown():
            self.Maximize(True)
            self.input.SetFocus()
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
            
    def on_enter(self, event):
        # 回车时检查输入
        if self.input.GetValue() != "123456789":
            self.input.SetValue("")
            self.hint.SetLabel("输入错误,请重试")
