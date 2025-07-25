import wx
import wx.adv
from .app_states import AppState

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

    def update_icon_by_state(self, state):
        """根据状态更新托盘图标"""
        status_map = {
            AppState.IDLE: "就绪",
            AppState.WORKING: "工作中", 
            AppState.RESTING: "休息中",
            AppState.AWAY: "用户离开"
        }
        status_text = status_map.get(state, "未知状态")
        self.SetIcon(wx.Icon(wx.ArtProvider.GetBitmap(wx.ART_TIP, size=(16, 16))), f"护眼助手 - {status_text}")
