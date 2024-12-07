import wx
import wx.adv

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
