import time
import winsound
import threading
from .logger_manager import LoggerManager

class RestManager:
    """休息管理器，处理休息相关的业务逻辑"""
    
    def __init__(self):
        """初始化休息管理器"""
        self.logger = LoggerManager.get_logger()
        
        # 状态管理
        self.is_resting = False
        self.rest_seconds = 0           # 总休息时间（秒）
        self.remaining_seconds = 0      # 剩余时间（秒）
        self.last_add_time = 0          # 上次增加时间的时间戳
        self.add_cooldown = 0.1         # 增加时间的冷却时间（秒）
        
        # 配置
        self.config = None
        
        # 回调函数
        self.on_complete = None         # 休息完成回调
        self.on_cancel = None           # 休息取消回调
        self.on_update_display = None   # 更新显示回调
        
        # 计时器
        self.timer = None
        self.timer_thread = None
        self.timer_running = False
    
    def start_rest(self, minutes, config=None, on_complete=None, on_cancel=None, on_update_display=None):
        """开始休息
        Args:
            minutes: 休息时间（分钟）
            config: 配置对象
            on_complete: 休息完成时的回调函数
            on_cancel: 休息被取消时的回调函数 
            on_update_display: 更新显示的回调函数
        """
        self.config = config
        self.rest_seconds = minutes * 60
        self.remaining_seconds = self.rest_seconds
        self.on_complete = on_complete
        self.on_cancel = on_cancel
        self.on_update_display = on_update_display
        self.is_resting = True
        
        self.logger.info(f"开始休息: {minutes}分钟")
        
        # 启动计时器线程
        self._start_timer()
        
        # 立即更新一次显示
        self._update_display()
    
    def stop_rest(self, cancelled=False):
        """停止休息
        Args:
            cancelled: 是否是被取消的（True表示提前退出，False表示正常完成）
        """
        self.is_resting = False
        self._stop_timer()
        
        if cancelled:
            self.logger.info("休息被取消")
            if self.on_cancel:
                self.on_cancel()
        else:
            self.logger.info("休息正常完成")
            if self.on_complete:
                self.on_complete()
    
    def add_rest_time(self):
        """增加休息时间，带有冷却保护
        Returns:
            tuple: (是否成功, 提示信息)
        """
        if not self.is_resting:
            return False, "当前不在休息状态"
            
        current_time = time.time()
        # 检查是否在冷却时间内
        if current_time - self.last_add_time < self.add_cooldown:
            return False, f"请等待{self.add_cooldown}秒后再增加时间"
            
        # 增加1分钟
        self.remaining_seconds += 60
        self.last_add_time = current_time
        self.logger.info("增加1分钟休息时间")
        
        # 更新显示
        self._update_display()
        
        return True, "已增加1分钟休息时间"
    
    def check_password(self, password):
        """验证密码
        Args:
            password: 输入的密码
        Returns:
            tuple: (是否正确, 提示信息)
        """
        if not self.config or not self.config.allow_password_skip:
            return False, "当前不允许使用密码提前结束休息"
        
        correct_password = "123456789123456789123456789"
        if password == correct_password:
            self.logger.info("密码验证成功，提前结束休息")
            return True, "密码正确"
        else:
            return False, "密码错误，请重试"
    
    def get_display_data(self):
        """获取显示数据
        Returns:
            dict: 包含当前时间、剩余时间等信息的字典
        """
        from datetime import datetime
        
        current_time = datetime.now().strftime("%H:%M:%S")
        minutes = self.remaining_seconds // 60
        seconds = self.remaining_seconds % 60
        
        return {
            'current_time': current_time,
            'remaining_minutes': minutes,
            'remaining_seconds': seconds,
            'remaining_display': f"{minutes:02d}:{seconds:02d}",
            'is_resting': self.is_resting
        }
    
    def get_hint_message(self, password_error=False):
        """获取提示信息
        Args:
            password_error: 是否是密码错误
        Returns:
            str: 提示信息
        """
        if not self.config or not self.config.allow_password_skip:
            return "按快捷键可增加1分钟休息时间"
        
        if password_error:
            return "密码错误，请重试\n按快捷键可增加1分钟休息时间"
        else:
            return "请输入三遍123456789以解锁\n按快捷键可增加1分钟休息时间"
    
    def _start_timer(self):
        """启动计时器线程"""
        self.timer_running = True
        self.timer_thread = threading.Thread(target=self._timer_func)
        self.timer_thread.daemon = True
        self.timer_thread.start()
    
    def _stop_timer(self):
        """停止计时器线程"""
        self.timer_running = False
        # 只有在不是当前线程时才join
        if self.timer_thread and self.timer_thread.is_alive() and threading.current_thread() != self.timer_thread:
            self.timer_thread.join(timeout=1)
    
    def _timer_func(self):
        """计时器线程函数"""
        while self.timer_running and self.is_resting:
            if self.remaining_seconds > 0:
                # 在剩余10秒时播放音效
                if self.remaining_seconds == 10 and self.config and self.config.play_sound_after_rest:
                    self._play_end_sound()
                
                self.remaining_seconds -= 1
                self._update_display()
                time.sleep(1)
            else:
                # 时间到，结束休息 - 不直接调用stop_rest避免join当前线程
                self.is_resting = False
                self.timer_running = False
                
                # 使用wx.CallAfter在主线程中执行完成回调
                if self.on_complete:
                    import wx
                    wx.CallAfter(self._finish_rest_from_timer)
                break
    
    def _finish_rest_from_timer(self):
        """从计时器线程安全地完成休息"""
        self.logger.info("休息正常完成")
        if self.on_complete:
            self.on_complete()
    
    def _update_display(self):
        """更新显示"""
        if self.on_update_display:
            self.on_update_display(self.get_display_data())
    
    def _play_end_sound(self):
        """播放结束音效"""
        try:
            def play_sound():
                # 播放do-re-mi音阶
                winsound.Beep(523, 200)  # do (C5)
                time.sleep(0.1)
                winsound.Beep(587, 200)  # re (D5)
                time.sleep(0.1)
                winsound.Beep(659, 200)  # mi (E5)
                time.sleep(0.1)
                winsound.Beep(784, 200)  # G5
                time.sleep(0.1)
                winsound.Beep(659, 200)  # E5
                time.sleep(0.1)
                winsound.Beep(523, 400)  # C5
            
            # 在单独线程中播放音效，避免阻塞
            sound_thread = threading.Thread(target=play_sound)
            sound_thread.daemon = True
            sound_thread.start()
            
            self.logger.info("播放休息结束音效")
        except Exception as e:
            self.logger.error(f"播放音效失败: {str(e)}")
    
    def cleanup(self):
        """清理资源"""
        self.stop_rest(cancelled=True)
        self.logger.info("休息管理器清理完成") 