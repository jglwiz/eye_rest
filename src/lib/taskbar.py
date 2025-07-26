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
        
        # 添加状态显示
        status_text = self.get_current_status()
        status_item = menu.Append(wx.ID_ANY, f"状态: {status_text}")
        status_item.Enable(False)  # 只显示，不可点击
        menu.AppendSeparator()
        
        # 核心功能
        show_item = menu.Append(wx.ID_ANY, "打开设置界面")
        
        # 根据当前状态显示不同操作
        if self.frame.core.is_running:
            pause_item = menu.Append(wx.ID_ANY, "停止工作")
            force_rest_item = menu.Append(wx.ID_ANY, "立即休息")
            self.Bind(wx.EVT_MENU, self.on_pause, pause_item)
            self.Bind(wx.EVT_MENU, self.on_force_rest, force_rest_item)
        else:
            start_item = menu.Append(wx.ID_ANY, "开始工作")
            self.Bind(wx.EVT_MENU, self.on_start, start_item)
        
        menu.AppendSeparator()
        exit_item = menu.Append(wx.ID_ANY, "退出程序")
        
        self.Bind(wx.EVT_MENU, self.on_show, show_item)
        self.Bind(wx.EVT_MENU, self.on_exit, exit_item)
        return menu

    def get_current_status(self):
        """获取当前状态文本"""
        state = self.frame.core.current_state
        if state == AppState.WORKING:
            remaining = self.frame.core.get_remaining_time()
            return f"工作中 ({remaining//60}:{remaining%60:02d})"
        elif state == AppState.RESTING:
            return "休息中"
        elif state == AppState.AWAY:
            return "用户离开"
        else:
            return "就绪"

    def on_double_click(self, event):
        self.frame.Show()
        
    def on_show(self, event):
        self.frame.Show()
        
    def on_start(self, event):
        """从托盘开始工作"""
        self.frame.on_toggle(None)
        
    def on_pause(self, event):
        """从托盘停止工作"""
        self.frame.on_toggle(None)
        
    def on_force_rest(self, event):
        """从托盘立即休息"""
        self.frame.on_force_rest(None)
        
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
