import threading
import time
import wx
from .config import Config
from .hotkey_manager import HotkeyManager
from .logger_manager import LoggerManager
from .app_states import AppState
from .activity_detector import ActivityDetector

class EyeRestCore:
    """护眼助手核心业务逻辑，不涉及UI"""
    
    def __init__(self):
        """初始化核心逻辑"""
        self.logger = LoggerManager.get_logger()
        self.config = Config()
        self.hotkey_manager = HotkeyManager()
        
        # 状态机
        self.current_state = AppState.IDLE
        self.state_start_time = time.time()
        
        # 工作相关
        self.work_start_time = 0
        self.work_end_time = 0
        self.accumulated_work_time = 0  # 累计工作时间
        
        # 离开状态相关
        self.away_start_time = 0
        
        # 活动检测
        self.activity_detector = ActivityDetector()
        self.idle_threshold = self.config.idle_threshold_minutes * 60  # 转换为秒
        
        # 回调函数
        self.on_status_change = None    # 状态变化回调
        self.on_start_rest = None       # 开始休息回调
        self.on_work_complete = None    # 工作完成回调
        
        # 创建定时器线程
        self.timer_thread = threading.Thread(target=self._timer_func)
        self.timer_thread.daemon = True
        self.thread_lock = threading.Lock()
        
        # 初始化热键
        self._init_hotkey()
    
    def _transition_to(self, new_state):
        """安全的状态转换"""
        old_state = self.current_state
        self.current_state = new_state
        self.state_start_time = time.time()
        
        # 状态进入处理
        self._on_state_enter(new_state)
        
        # 日志记录
        self.logger.info(f"状态转换: {old_state.value} → {new_state.value}")
        
        # 通知UI更新
        self._notify_status_change()

    def _on_state_enter(self, state):
        """状态进入处理"""
        if state == AppState.WORKING:
            self.work_start_time = time.time()
            self.work_end_time = self.work_start_time + self.config.work_time * 60
        elif state == AppState.AWAY:
            self.away_start_time = time.time()
        elif state == AppState.IDLE:
            self._reset_timers()

    def _reset_timers(self):
        """重置计时器"""
        self.work_start_time = 0
        self.work_end_time = 0
        self.accumulated_work_time = 0
        self.away_start_time = 0

    def _init_hotkey(self):
        """初始化全局热键"""
        try:
            self.hotkey_manager.register_hotkey(self.config.hotkey, self.force_rest)
            self.logger.info("热键初始化成功")
        except Exception as e:
            self.logger.error(f"热键初始化失败: {str(e)}")
    
    def start_work_session(self, work_time, rest_time, play_sound, allow_password):
        """开始工作会话
        Args:
            work_time: 工作时间(分钟)
            rest_time: 休息时间(分钟) 
            play_sound: 是否播放声音
            allow_password: 是否允许密码跳过
        """
        with self.thread_lock:
            # 更新配置
            self.config.work_time = work_time
            self.config.rest_time = rest_time
            self.config.play_sound_after_rest = play_sound
            self.config.allow_password_skip = allow_password
            self.config.save()
            
            # 启动定时器线程
            if not self.timer_thread.is_alive():
                self.timer_thread.start()
                
            # 转换到工作状态
            self._transition_to(AppState.WORKING)
            
            # 更新空闲检测阈值
            self.idle_threshold = self.config.idle_threshold_minutes * 60
            
            self.logger.info(f"开始工作会话: {work_time}分钟工作, {rest_time}分钟休息")
    
    def stop_work_session(self):
        """停止工作会话"""
        with self.thread_lock:
            self._transition_to(AppState.IDLE)
            self.logger.info("停止工作会话")
    
    def force_rest(self, event=None):
        """强制开始休息"""
        with self.thread_lock:
            if self.current_state == AppState.IDLE:
                # 如果程序未运行，先启动程序
                self.logger.info("程序未运行，先启动工作会话")
                return False
            
            if self.current_state == AppState.RESTING:
                # 如果当前正在休息，增加1分钟休息时间
                self.logger.info("当前正在休息，增加休息时间")
                if self.on_work_complete:
                    wx.CallAfter(self.on_work_complete, "add_time")
            elif self.current_state in [AppState.WORKING, AppState.AWAY]:
                # 开始新的休息
                self.logger.info("强制开始休息")
                self._start_rest()
            return True
    
    def _start_rest(self):
        """内部方法：开始休息"""
        self._transition_to(AppState.RESTING)
        if self.on_start_rest:
            wx.CallAfter(self.on_start_rest, self.config.rest_time)
    
    def on_rest_complete(self):
        """休息完成回调"""
        with self.thread_lock:
            # 转换到工作状态，开始新的工作周期
            self._transition_to(AppState.WORKING)
            self.logger.info("休息完成，开始新的工作周期")
    
    def on_rest_cancel(self):
        """休息取消回调"""
        with self.thread_lock:
            # 转换到工作状态，重置工作计时
            self._transition_to(AppState.WORKING)
            self.logger.info("休息被取消，重新开始工作")
    
    def update_hotkey(self, new_hotkey):
        """更新热键设置
        Args:
            new_hotkey: 新的热键字符串
        Returns:
            bool: 是否更新成功
        """
        try:
            self.hotkey_manager.register_hotkey(new_hotkey, self.force_rest)
            self.config.hotkey = new_hotkey
            self.config.save()
            self.logger.info(f"热键更新成功: {new_hotkey}")
            return True
        except Exception as e:
            self.logger.error(f"热键更新失败: {str(e)}")
            return False
    
    def get_remaining_time(self):
        """获取剩余工作时间
        Returns:
            int: 剩余秒数，如果不在工作状态返回0
        """
        if self.current_state != AppState.WORKING:
            return 0
        
        remaining = int(self.work_end_time - time.time())
        return max(0, remaining)
    
    def _timer_func(self):
        """状态机驱动的定时器函数"""
        while True:
            with self.thread_lock:
                if self.current_state == AppState.IDLE:
                    time.sleep(0.5)
                    continue
                    
                # 根据当前状态执行不同逻辑
                if self.current_state == AppState.WORKING:
                    self._handle_working_state()
                elif self.current_state == AppState.AWAY:
                    self._handle_away_state()
                # RESTING状态由RestManager处理
                    
            time.sleep(1)

    def _handle_working_state(self):
        """处理工作状态逻辑"""
        current_time = time.time()
        
        # 检查是否空闲（如果启用了空闲检测）
        if (self.config.idle_detection_enabled and 
            self.activity_detector.is_user_idle(self.idle_threshold)):
            self._transition_to(AppState.AWAY)
            return
        
        # 检查工作时间是否到达
        if current_time >= self.work_end_time:
            self._start_rest()
            return
        
        # 更新剩余时间显示
        self._update_work_display()

    def _handle_away_state(self):
        """处理离开状态逻辑"""
        if not self.activity_detector.is_user_idle(self.idle_threshold):
            # 用户回来了，重新开始工作
            self._transition_to(AppState.WORKING)

    def _update_work_display(self):
        """更新工作状态显示"""
        remaining = int(self.work_end_time - time.time())
        if remaining > 0:
            self._notify_status_change()
    
    def _notify_status_change(self, custom_status=None):
        """通知状态变化"""
        if self.on_status_change:
            status = custom_status if custom_status else self._get_status_text()
            wx.CallAfter(self.on_status_change, status)

    def _get_status_text(self):
        """根据当前状态返回显示文案"""
        if self.current_state == AppState.IDLE:
            return "就绪"
        elif self.current_state == AppState.WORKING:
            remaining = int(self.work_end_time - time.time())
            if remaining > 0:
                return f"工作中: 还剩 {remaining//60}:{remaining%60:02d}"
            return "工作中"
        elif self.current_state == AppState.RESTING:
            return "休息时间"
        elif self.current_state == AppState.AWAY:
            away_duration = int(time.time() - self.away_start_time)
            return f"检测到用户离开 ({away_duration//60}:{away_duration%60:02d})"
        return "未知状态"

    # 向后兼容性属性
    @property
    def is_running(self):
        """兼容性属性：是否正在运行"""
        return self.current_state != AppState.IDLE

    @property  
    def is_working(self):
        """兼容性属性：是否在工作状态"""
        return self.current_state == AppState.WORKING
    
    def cleanup(self):
        """清理资源"""
        with self.thread_lock:
            self._transition_to(AppState.IDLE)
        if self.hotkey_manager:
            self.hotkey_manager.stop()
            self.hotkey_manager = None
        self.logger.info("核心逻辑清理完成") 