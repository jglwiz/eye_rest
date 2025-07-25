import threading
import time
import wx
from .config import Config
from .hotkey_manager import HotkeyManager
from .logger_manager import LoggerManager

class EyeRestCore:
    """护眼助手核心业务逻辑，不涉及UI"""
    
    def __init__(self):
        """初始化核心逻辑"""
        self.logger = LoggerManager.get_logger()
        self.config = Config()
        self.hotkey_manager = HotkeyManager()
        
        # 状态管理
        self.is_running = False     # 是否开启提醒
        self.is_working = True      # 是否在工作状态
        self.work_end_time = 0      # 工作结束时间
        
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
            
            # 开始工作状态
            self.is_running = True
            self.is_working = True
            self.work_end_time = time.time() + work_time * 60
            
            # 启动定时器线程
            if not self.timer_thread.is_alive():
                self.timer_thread.start()
            
            self.logger.info(f"开始工作会话: {work_time}分钟工作, {rest_time}分钟休息")
            self._notify_status_change("工作中")
    
    def stop_work_session(self):
        """停止工作会话"""
        with self.thread_lock:
            self.is_running = False
            self.is_working = True
            self.logger.info("停止工作会话")
            self._notify_status_change("就绪")
    
    def force_rest(self, event=None):
        """强制开始休息"""
        with self.thread_lock:
            if not self.is_running:
                # 如果程序未运行，先启动程序
                self.logger.info("程序未运行，先启动工作会话")
                return False
            
            if not self.is_working:
                # 如果当前正在休息，增加1分钟休息时间
                self.logger.info("当前正在休息，增加休息时间")
                if self.on_work_complete:
                    wx.CallAfter(self.on_work_complete, "add_time")
            else:
                # 开始新的休息
                self.logger.info("强制开始休息")
                self._start_rest()
            return True
    
    def _start_rest(self):
        """内部方法：开始休息"""
        self.is_working = False
        self._notify_status_change("休息时间")
        if self.on_start_rest:
            wx.CallAfter(self.on_start_rest, self.config.rest_time)
    
    def on_rest_complete(self):
        """休息完成回调"""
        with self.thread_lock:
            self.is_working = True
            # 设置下一个工作结束时间
            self.work_end_time = time.time() + self.config.work_time * 60
            self.logger.info("休息完成，开始新的工作周期")
            self._notify_status_change("工作中")
    
    def on_rest_cancel(self):
        """休息取消回调"""
        with self.thread_lock:
            self.is_working = True
            # 重置工作计时
            self.work_end_time = time.time() + self.config.work_time * 60
            self.logger.info("休息被取消，重新开始工作")
            self._notify_status_change("工作中")
    
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
        if not self.is_running or not self.is_working:
            return 0
        
        remaining = int(self.work_end_time - time.time())
        return max(0, remaining)
    
    def _timer_func(self):
        """定时器线程函数"""
        while True:
            with self.thread_lock:
                if not self.is_running:
                    time.sleep(0.5)
                    continue
                    
                if self.is_working:
                    current_time = time.time()
                    if current_time >= self.work_end_time:
                        # 工作结束，开始休息
                        self._start_rest()
                    else:
                        # 更新剩余时间显示
                        remaining = int(self.work_end_time - current_time)
                        if remaining > 0:
                            status = f"工作中: 还剩 {remaining//60}:{remaining%60:02d}"
                            self._notify_status_change(status)
                
            time.sleep(1)
    
    def _notify_status_change(self, status):
        """通知状态变化"""
        if self.on_status_change:
            wx.CallAfter(self.on_status_change, status)
    
    def cleanup(self):
        """清理资源"""
        self.is_running = False
        if self.hotkey_manager:
            self.hotkey_manager.stop()
            self.hotkey_manager = None
        self.logger.info("核心逻辑清理完成") 