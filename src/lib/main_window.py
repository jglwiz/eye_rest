import wx
import wx.adv
from .rest_screen import RestScreen
from .taskbar import TaskBarIcon
from .app_core import EyeRestCore
from .app_states import AppState
from .statistics_chart import StatisticsChart
from .hourly_chart import HourlyChart
from .process_checker import remove_lock_file

class MainFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="护眼助手", size=(400, 550))
        
        # 创建核心业务逻辑
        self.core = EyeRestCore()
        
        # 创建休息窗口时传入core
        self.rest_screen = RestScreen(core=self.core)
        self.real_close = False
        
        # 创建系统托盘图标
        self.taskbar_icon = TaskBarIcon(self)
        
        # 设置核心逻辑的回调
        self.core.on_status_change = self.on_status_change
        self.core.on_start_rest = self.on_start_rest
        self.core.on_work_complete = self.on_work_complete
        self.core.on_temp_pause = self.on_temp_pause
        self.core.on_temp_resume = self.on_temp_resume
        
        self._init_ui()
        
        # 初始化统计显示
        self.update_statistics_display()
        
        # 绑定关闭事件
        self.Bind(wx.EVT_CLOSE, self.on_close)
        
        # 居中显示
        self.Center()

    def start_silent_mode(self):
        """静默模式启动 - 不显示窗口，直接使用配置文件启动工作会话"""
        if not self.core.is_running:
            # 使用配置文件中的设置启动工作会话
            work_time = self.core.config.work_time
            rest_time = self.core.config.rest_time
            play_sound = self.core.config.play_sound_after_rest
            allow_password = self.core.config.allow_password_skip
            idle_detection_enabled = self.core.config.idle_detection_enabled
            idle_threshold_minutes = self.core.config.idle_threshold_minutes
            
            # 获取临时暂停配置
            temp_pause_enabled = self.temp_pause_checkbox.GetValue()
            temp_pause_duration = self.temp_pause_duration_spin.GetValue()
            
            # 获取工作结束提醒配置
            work_end_reminder_enabled = self.work_end_reminder_checkbox.GetValue()
            
            self.core.start_work_session(
                work_time, rest_time, play_sound, allow_password,
                idle_detection_enabled=idle_detection_enabled,
                idle_threshold_minutes=idle_threshold_minutes,
                temp_pause_enabled=temp_pause_enabled,
                temp_pause_duration=temp_pause_duration,
                work_end_reminder_enabled=work_end_reminder_enabled
            )
            
            # 显示托盘通知
            wx.adv.NotificationMessage(
                "护眼助手",
                "程序已在后台启动，双击托盘图标可打开设置界面",
                parent=None
            ).Show()

    def sync_ui_state(self):
        """同步UI状态与核心逻辑状态"""
        if self.core.is_running:
            self.toggle_btn.SetLabel("停止")
        else:
            self.toggle_btn.SetLabel("开始")

    def Show(self, show=True):
        """重写Show方法，在显示窗口时同步UI状态"""
        result = super().Show(show)
        if show:
            # 同步UI状态
            self.sync_ui_state()
        return result

    def _init_ui(self):
        """初始化UI界面"""
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        # 创建标签页控件
        self.notebook = wx.Notebook(panel)
        
        # 创建设置标签页
        settings_panel = self._create_settings_panel()
        self.notebook.AddPage(settings_panel, "设置")
        
        # 创建统计标签页
        statistics_panel = self._create_statistics_panel()
        self.notebook.AddPage(statistics_panel, "统计")
        
        # 状态显示
        self.status = wx.StaticText(panel, label="就绪")
        
        # 主布局
        vbox.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
        vbox.Add(self.status, 0, wx.ALL|wx.CENTER, 5)
        
        panel.SetSizer(vbox)
        
    def _create_settings_panel(self):
        """创建设置标签页"""
        panel = wx.Panel(self.notebook)
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        # 添加配置控件
        grid = wx.FlexGridSizer(11, 2, 5, 5)
        grid.Add(wx.StaticText(panel, label="工作时间(分钟):"))
        self.work_spin = wx.SpinCtrl(panel, value=str(self.core.config.work_time))
        grid.Add(self.work_spin)
        
        grid.Add(wx.StaticText(panel, label="休息时间(分钟):"))
        self.rest_spin = wx.SpinCtrl(panel, value=str(self.core.config.rest_time))
        grid.Add(self.rest_spin)
        
        # 添加快捷键配置
        grid.Add(wx.StaticText(panel, label="提前休息快捷键:"))
        hotkey_box = wx.BoxSizer(wx.HORIZONTAL)
        self.hotkey_text = wx.TextCtrl(panel, value=self.core.config.hotkey)
        self.hotkey_btn = wx.Button(panel, label="确定", size=(50, -1))
        self.hotkey_btn.Bind(wx.EVT_BUTTON, self.on_set_hotkey)
        hotkey_box.Add(self.hotkey_text, 1, wx.RIGHT, 5)
        hotkey_box.Add(self.hotkey_btn, 0)
        grid.Add(hotkey_box)

        # 添加空闲检测配置
        grid.Add(wx.StaticText(panel, label="启用离开检测:"))
        self.idle_detection_checkbox = wx.CheckBox(panel)
        self.idle_detection_checkbox.SetValue(self.core.config.idle_detection_enabled)
        grid.Add(self.idle_detection_checkbox)
        
        grid.Add(wx.StaticText(panel, label="离开检测时间(分钟):"))
        self.idle_threshold_spin = wx.SpinCtrl(panel, value=str(self.core.config.idle_threshold_minutes), min=1, max=30)
        grid.Add(self.idle_threshold_spin)

        # 添加声音和密码选项
        grid.Add(wx.StaticText(panel, label="休息结束时播放声音:"))
        self.sound_checkbox = wx.CheckBox(panel)
        self.sound_checkbox.SetValue(self.core.config.play_sound_after_rest)
        grid.Add(self.sound_checkbox)

        grid.Add(wx.StaticText(panel, label="允许密码提前结束休息:"))
        self.password_checkbox = wx.CheckBox(panel)
        self.password_checkbox.SetValue(self.core.config.allow_password_skip)
        grid.Add(self.password_checkbox)

        # 添加临时暂停配置
        grid.Add(wx.StaticText(panel, label="启用临时暂停功能:"))
        self.temp_pause_checkbox = wx.CheckBox(panel)
        self.temp_pause_checkbox.SetValue(self.core.config.temp_pause_enabled)
        grid.Add(self.temp_pause_checkbox)
        
        grid.Add(wx.StaticText(panel, label="临时暂停时长(秒):"))
        self.temp_pause_duration_spin = wx.SpinCtrl(panel, value=str(self.core.config.temp_pause_duration), min=5, max=300)
        grid.Add(self.temp_pause_duration_spin)
        
        grid.Add(wx.StaticText(panel, label="临时暂停快捷键:"))
        temp_pause_hotkey_box = wx.BoxSizer(wx.HORIZONTAL)
        self.temp_pause_hotkey_text = wx.TextCtrl(panel, value=self.core.config.temp_pause_hotkey)
        self.temp_pause_hotkey_btn = wx.Button(panel, label="确定", size=(50, -1))
        self.temp_pause_hotkey_btn.Bind(wx.EVT_BUTTON, self.on_set_temp_pause_hotkey)
        temp_pause_hotkey_box.Add(self.temp_pause_hotkey_text, 1, wx.RIGHT, 5)
        temp_pause_hotkey_box.Add(self.temp_pause_hotkey_btn, 0)
        grid.Add(temp_pause_hotkey_box)

        # 添加工作结束前提醒配置
        grid.Add(wx.StaticText(panel, label="工作结束前40秒提醒:"))
        self.work_end_reminder_checkbox = wx.CheckBox(panel)
        self.work_end_reminder_checkbox.SetValue(self.core.config.work_end_reminder_enabled)
        grid.Add(self.work_end_reminder_checkbox)
        
        # 布局
        vbox.Add(grid, 0, wx.ALL|wx.CENTER, 10)
        
        # 添加控制按钮
        button_box = wx.BoxSizer(wx.HORIZONTAL)
        self.toggle_btn = wx.Button(panel, label="开始")
        self.toggle_btn.Bind(wx.EVT_BUTTON, self.on_toggle)
        
        self.force_rest_btn = wx.Button(panel, label="提前休息")
        self.force_rest_btn.Bind(wx.EVT_BUTTON, self.on_force_rest)
        
        self.exit_btn = wx.Button(panel, label="退出程序")
        self.exit_btn.Bind(wx.EVT_BUTTON, self.on_exit_program)
        
        button_box.Add(self.toggle_btn, 1, wx.ALL|wx.EXPAND, 5)
        button_box.Add(self.force_rest_btn, 1, wx.ALL|wx.EXPAND, 5)
        button_box.Add(self.exit_btn, 1, wx.ALL|wx.EXPAND, 5)
        
        vbox.Add(button_box, 0, wx.ALL|wx.EXPAND, 10)
        
        # 添加小时统计图表
        hourly_title = wx.StaticText(panel, label="今日每小时休息统计:")
        self.hourly_chart = HourlyChart(panel)
        self.hourly_chart.SetMinSize((400, 120))
        
        vbox.Add(hourly_title, 0, wx.ALL|wx.LEFT, 10)
        vbox.Add(self.hourly_chart, 0, wx.ALL|wx.EXPAND, 10)
        
        panel.SetSizer(vbox)
        return panel
        
    def _create_statistics_panel(self):
        """创建统计标签页"""
        panel = wx.Panel(self.notebook)
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        # 统计数字显示区域
        stats_grid = wx.FlexGridSizer(1, 4, 10, 20)
        
        # 单行显示：今日完成 | 本周完成 | 总计完成 | 平均每日
        today_box = wx.BoxSizer(wx.VERTICAL)
        today_box.Add(wx.StaticText(panel, label="今日完成:"), 0, wx.CENTER)
        self.today_count_label = wx.StaticText(panel, label="0次")
        today_box.Add(self.today_count_label, 0, wx.CENTER)
        stats_grid.Add(today_box, 0, wx.ALL|wx.CENTER, 5)
        
        week_box = wx.BoxSizer(wx.VERTICAL)
        week_box.Add(wx.StaticText(panel, label="本周完成:"), 0, wx.CENTER)
        self.week_count_label = wx.StaticText(panel, label="0次")
        week_box.Add(self.week_count_label, 0, wx.CENTER)
        stats_grid.Add(week_box, 0, wx.ALL|wx.CENTER, 5)
        
        total_box = wx.BoxSizer(wx.VERTICAL)
        total_box.Add(wx.StaticText(panel, label="总计完成:"), 0, wx.CENTER)
        self.total_count_label = wx.StaticText(panel, label="0次")
        total_box.Add(self.total_count_label, 0, wx.CENTER)
        stats_grid.Add(total_box, 0, wx.ALL|wx.CENTER, 5)
        
        average_box = wx.BoxSizer(wx.VERTICAL)
        average_box.Add(wx.StaticText(panel, label="平均每日:"), 0, wx.CENTER)
        self.average_count_label = wx.StaticText(panel, label="0.0次")
        average_box.Add(self.average_count_label, 0, wx.CENTER)
        stats_grid.Add(average_box, 0, wx.ALL|wx.CENTER, 5)
        
        # 图表区域
        self.statistics_chart = StatisticsChart(panel)
        self.statistics_chart.SetMinSize((300, 150))
        
        # 重置按钮
        self.reset_stats_btn = wx.Button(panel, label="重置统计")
        self.reset_stats_btn.Bind(wx.EVT_BUTTON, self.on_reset_statistics)
        
        # 布局
        vbox.Add(stats_grid, 0, wx.ALL|wx.CENTER, 10)
        vbox.Add(self.statistics_chart, 1, wx.ALL|wx.EXPAND, 10)
        vbox.Add(self.reset_stats_btn, 0, wx.ALL|wx.CENTER, 5)
        
        panel.SetSizer(vbox)
        return panel

    def on_status_change(self, status):
        """状态变化回调 - 更新UI显示"""
        self.status.SetLabel(status)
        # 更新托盘图标状态
        if hasattr(self.core, 'current_state'):
            self.taskbar_icon.update_icon_by_state(self.core.current_state)
        # 更新统计显示（可能有新的完成记录）
        self.update_statistics_display()

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

    def on_temp_pause(self):
        """临时暂停回调 - 隐藏休息屏幕"""
        self.rest_screen.temp_pause()
    
    def on_temp_resume(self):
        """恢复休息回调 - 重新显示休息屏幕"""
        self.rest_screen.temp_resume()

    def on_force_rest(self, event=None):
        """处理提前休息按钮"""
        success = self.core.force_rest()
        if not success:
            # 如果程序未运行，自动启动
            work_time = self.work_spin.GetValue()
            rest_time = self.rest_spin.GetValue()
            play_sound = self.sound_checkbox.GetValue()
            allow_password = self.password_checkbox.GetValue()
            idle_detection_enabled = self.idle_detection_checkbox.GetValue()
            idle_threshold_minutes = self.idle_threshold_spin.GetValue()
            
            # 获取工作结束提醒配置
            work_end_reminder_enabled = self.work_end_reminder_checkbox.GetValue()
            
            self.core.start_work_session(
                work_time, rest_time, play_sound, allow_password,
                idle_detection_enabled=idle_detection_enabled,
                idle_threshold_minutes=idle_threshold_minutes,
                temp_pause_enabled=self.core.config.temp_pause_enabled,
                temp_pause_duration=self.core.config.temp_pause_duration,
                work_end_reminder_enabled=work_end_reminder_enabled
            )
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
            idle_detection_enabled = self.idle_detection_checkbox.GetValue()
            idle_threshold_minutes = self.idle_threshold_spin.GetValue()
            
            # 获取临时暂停配置
            temp_pause_enabled = self.temp_pause_checkbox.GetValue()
            temp_pause_duration = self.temp_pause_duration_spin.GetValue()
            
            # 获取工作结束提醒配置
            work_end_reminder_enabled = self.work_end_reminder_checkbox.GetValue()
            
            self.core.start_work_session(
                work_time, rest_time, play_sound, allow_password,
                idle_detection_enabled=idle_detection_enabled,
                idle_threshold_minutes=idle_threshold_minutes,
                temp_pause_enabled=temp_pause_enabled,
                temp_pause_duration=temp_pause_duration,
                work_end_reminder_enabled=work_end_reminder_enabled
            )
            self.toggle_btn.SetLabel("停止")
            self.Hide()  # 隐藏主窗口
        else:
            # 停止工作会话
            self.core.stop_work_session()
            self.toggle_btn.SetLabel("开始")
            # 只有在休息状态时才调用stop_rest，避免错误的回调
            if self.core.current_state == AppState.RESTING:
                self.rest_screen.stop_rest(cancelled=True)
            else:
                # 如果不在休息状态，直接隐藏休息界面
                self.rest_screen.Hide()

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
    
    def on_set_temp_pause_hotkey(self, event):
        """处理设置临时暂停热键"""
        new_hotkey = self.temp_pause_hotkey_text.GetValue().strip()
        if new_hotkey:
            try:
                # 收集所有需要重新注册的热键
                hotkeys_to_register = [
                    (self.core.config.hotkey, self.core.force_rest)
                ]
                
                # 添加新的临时暂停热键
                if self.core.config.temp_pause_enabled:
                    hotkeys_to_register.append((new_hotkey, self.core.temp_pause))
                
                # 批量重新注册热键
                self.core._batch_register_hotkeys(hotkeys_to_register)
                
                # 保存配置
                self.core.config.temp_pause_hotkey = new_hotkey
                self.core.config.save()
                
                wx.MessageBox("临时暂停快捷键设置成功", "提示")
            except Exception as e:
                wx.MessageBox(f"临时暂停快捷键设置失败: {str(e)}", "错误")
                # 恢复原来的热键
                self.temp_pause_hotkey_text.SetValue(self.core.config.temp_pause_hotkey)
                
    def on_exit_program(self, event):
        """处理退出程序按钮"""
        dlg = wx.MessageDialog(self, "确定要退出护眼助手程序吗？", 
                              "确认退出", wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
        if dlg.ShowModal() == wx.ID_YES:
            self.real_close = True  # 设置为真正关闭
            self.Close()  # 关闭主窗口
        dlg.Destroy()
                
    def on_close(self, event):
        """处理窗口关闭事件"""
        if self.real_close:  # 如果是真正的关闭操作
            self.core.cleanup()  # 清理核心逻辑资源
            self.taskbar_icon.Destroy()
            self.rest_screen.Destroy()
            # 删除锁文件
            remove_lock_file()
            event.Skip()
        else:  # 如果是点击关闭按钮
            self.Hide()
            wx.adv.NotificationMessage(
                "护眼助手",
                "程序已最小化到系统托盘，双击图标可以重新打开主窗口",
                parent=None).Show()
    
    def update_statistics_display(self):
        """更新统计显示"""
        try:
            stats = self.core.get_statistics_manager()
            self.today_count_label.SetLabel(f"{stats.get_today_count()}次")
            self.week_count_label.SetLabel(f"{stats.get_week_count()}次")
            self.total_count_label.SetLabel(f"{stats.get_total_count()}次")
            self.average_count_label.SetLabel(f"{stats.get_average_daily_count()}次")
            
            # 更新图表数据
            daily_records = stats.get_daily_records(7)  # 获取最近7天数据
            self.statistics_chart.set_data(daily_records)
            
            # 更新小时图表数据
            hourly_records = stats.get_today_hourly_records()
            self.hourly_chart.set_data(hourly_records)
        except Exception as e:
            self.core.logger.error(f"更新统计显示失败: {str(e)}")
    
    def on_reset_statistics(self, event):
        """处理重置统计按钮"""
        dlg = wx.MessageDialog(self, "确定要重置所有统计数据吗？此操作不可撤销。", 
                              "确认重置", wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
        if dlg.ShowModal() == wx.ID_YES:
            try:
                self.core.get_statistics_manager().reset_statistics()
                self.update_statistics_display()
                wx.MessageBox("统计数据已成功重置", "提示", wx.OK | wx.ICON_INFORMATION)
            except Exception as e:
                wx.MessageBox(f"重置统计数据失败: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)
                self.core.logger.error(f"重置统计数据失败: {str(e)}")
        dlg.Destroy()
