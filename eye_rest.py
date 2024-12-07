import wx
import wx.adv
import time
import threading
import json
import os
import keyboard

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

class TaskBarIcon(wx.adv.TaskBarIcon):
    def __init__(self, frame):
        super().__init__()
        self.frame = frame
        self.SetIcon(wx.Icon(wx.ArtProvider.GetBitmap(wx.ART_TIP, size=(16, 16))), "护眼助手")
        self.Bind(wx.adv.EVT_TASKBAR_LEFT_DCLICK, self.on_double_click)

    def CreatePopupMenu(self):
        menu = wx.Menu()
        show_item = menu.Append(wx.ID_ANY, "显示主窗口")
        exit_item = menu.Append(wx.ID_ANY, "退出")
        
        self.Bind(wx.EVT_MENU, self.on_show, show_item)
        self.Bind(wx.EVT_MENU, self.on_exit, exit_item)
        return menu

    def on_double_click(self, event):
        self.frame.Show()
        
    def on_show(self, event):
        self.frame.Show()
        
    def on_exit(self, event):
        self.frame.real_close = True
        self.frame.Close()

class HotkeyDialog(wx.Dialog):
    def __init__(self, parent, current_hotkey):
        super().__init__(parent, title="设置快捷键", size=(300, 150))
        self.current_hotkey = current_hotkey
        self.new_hotkey = current_hotkey
        
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        # 添加说明文本
        hint = wx.StaticText(panel, label="请按下新的快捷键组合\n当前快捷键: " + current_hotkey)
        vbox.Add(hint, 0, wx.ALL|wx.CENTER, 10)
        
        # 添加快捷键显示框
        self.hotkey_text = wx.TextCtrl(panel, style=wx.TE_READONLY)
        self.hotkey_text.SetValue(current_hotkey)
        vbox.Add(self.hotkey_text, 0, wx.ALL|wx.EXPAND, 5)
        
        # 添加按钮
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        ok_button = wx.Button(panel, wx.ID_OK, "确定")
        cancel_button = wx.Button(panel, wx.ID_CANCEL, "取消")
        hbox.Add(ok_button, 1, wx.ALL, 5)
        hbox.Add(cancel_button, 1, wx.ALL, 5)
        vbox.Add(hbox, 0, wx.ALL|wx.CENTER, 5)
        
        panel.SetSizer(vbox)
        
        # 绑定键盘事件
        self.hotkey_text.Bind(wx.EVT_KEY_DOWN, self.on_key)
        
    def on_key(self, event):
        modifiers = []
        keycode = event.GetKeyCode()
        
        if event.ControlDown():
            modifiers.append("ctrl")
        if event.ShiftDown():
            modifiers.append("shift")
        if event.AltDown():
            modifiers.append("alt")
            
        key = wx.GetKeyCodeName(keycode).lower()
        if key not in ["ctrl", "shift", "alt"]:
            modifiers.append(key)
            
        self.new_hotkey = "+".join(modifiers)
        self.hotkey_text.SetValue(self.new_hotkey)

class MainFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="护眼助手", size=(300, 250))
        
        self.load_config()  # 加载配置
        self.is_working = False
        self.rest_screen = RestScreen()
        self.force_rest_thread = None
        self.real_close = False  # 添加标志位，用于区分是否真正关闭程序
        
        # 创建系统托盘图标
        self.taskbar_icon = TaskBarIcon(self)
        
        # 创建面板和布局
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        # 添加配置控件
        grid = wx.FlexGridSizer(3, 2, 5, 5)
        grid.Add(wx.StaticText(panel, label="工作时间(分钟):"))
        self.work_spin = wx.SpinCtrl(panel, value=str(self.work_time))
        grid.Add(self.work_spin)
        
        grid.Add(wx.StaticText(panel, label="休息时间(分钟):"))
        self.rest_spin = wx.SpinCtrl(panel, value=str(self.rest_time))
        grid.Add(self.rest_spin)
        
        grid.Add(wx.StaticText(panel, label="提前休息快捷键:"))
        self.hotkey_btn = wx.Button(panel, label=self.hotkey)
        self.hotkey_btn.Bind(wx.EVT_BUTTON, self.on_set_hotkey)
        grid.Add(self.hotkey_btn)
        
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
        
        # 创建计时器线程
        self.timer_thread = None
        
        # 绑定关闭事件
        self.Bind(wx.EVT_CLOSE, self.on_close)
        
        # 注册全局热键
        self.register_hotkey()
        
        # 居中显示
        self.Center()

    def load_config(self):
        config_path = "eye_rest_config.json"
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    config = json.load(f)
                    self.work_time = config.get("work_time", 10)
                    self.rest_time = config.get("rest_time", 1)
                    self.hotkey = config.get("hotkey", "ctrl+shift+r")
            except:
                self.work_time = 10
                self.rest_time = 1
                self.hotkey = "ctrl+shift+r"
        else:
            self.work_time = 10
            self.rest_time = 1
            self.hotkey = "ctrl+shift+r"

    def save_config(self):
        config = {
            "work_time": self.work_time,
            "rest_time": self.rest_time,
            "hotkey": self.hotkey
        }
        with open("eye_rest_config.json", "w") as f:
            json.dump(config, f)
            
    def register_hotkey(self):
        try:
            keyboard.remove_hotkey(self.hotkey)  # 移除旧的热键
        except:
            pass
        keyboard.add_hotkey(self.hotkey, self.on_force_rest)
        
    def on_set_hotkey(self, event):
        dialog = HotkeyDialog(self, self.hotkey)
        if dialog.ShowModal() == wx.ID_OK:
            self.hotkey = dialog.new_hotkey
            self.hotkey_btn.SetLabel(self.hotkey)
            self.save_config()
            self.register_hotkey()
        dialog.Destroy()
        
    def force_rest_timer(self):
        # 休息时间
        wx.CallAfter(self.rest_screen.Show)
        wx.CallAfter(self.rest_screen.Maximize, True)
        wx.CallAfter(self.status.SetLabel, "休息时间")
        
        # 等待休息时间结束
        time.sleep(self.rest_time * 60)
        
        # 自动解锁
        if self.is_working:  # 只在程序仍在运行时执行
            wx.CallAfter(self.rest_screen.Hide)
        
    def on_force_rest(self, event=None):
        if self.is_working:
            # 如果已经有强制休息线程在运行，先停止它
            if self.force_rest_thread and self.force_rest_thread.is_alive():
                return
                
            # 创建新的强制休息线程
            self.force_rest_thread = threading.Thread(target=self.force_rest_timer)
            self.force_rest_thread.daemon = True
            self.force_rest_thread.start()
        
    def on_toggle(self, event):
        if not self.is_working:
            # 开始计时
            self.work_time = self.work_spin.GetValue()
            self.rest_time = self.rest_spin.GetValue()
            self.save_config()  # 保存配置
            self.is_working = True
            self.toggle_btn.SetLabel("停止")
            self.timer_thread = threading.Thread(target=self.timer_func)
            self.timer_thread.daemon = True
            self.timer_thread.start()
            self.Hide()  # 隐藏主窗口
        else:
            # 停止计时
            self.is_working = False
            self.toggle_btn.SetLabel("开始")
            self.status.SetLabel("就绪")
            self.rest_screen.Hide()
            
    def timer_func(self):
        while self.is_working:
            # 工作时间
            for i in range(self.work_time * 60, -1, -1):
                if not self.is_working:
                    return
                wx.CallAfter(self.status.SetLabel, f"工作中: 还剩 {i//60}:{i%60:02d}")
                time.sleep(1)
            
            # 休息时间
            if not self.is_working:
                return
            wx.CallAfter(self.rest_screen.Show)
            wx.CallAfter(self.rest_screen.Maximize, True)  # 确保最大化
            wx.CallAfter(self.status.SetLabel, "休息时间")
            
            for i in range(self.rest_time * 60, -1, -1):
                if not self.is_working:
                    wx.CallAfter(self.rest_screen.Hide)
                    return
                if i == 0:  # 休息时间结束时自动解锁
                    wx.CallAfter(self.rest_screen.Hide)
                time.sleep(1)
                
    def on_close(self, event):
        if self.real_close:  # 如果是真正的关闭操作
            self.is_working = False
            try:
                keyboard.remove_hotkey(self.hotkey)  # 移除热键
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
