import threading
import time
import queue
import wx
from .config import Config
from .hotkey_manager import HotkeyManager
from .logger_manager import LoggerManager
from .app_states import AppState
from .activity_detector import ActivityDetector
from .statistics_manager import StatisticsManager
from .process_checker import remove_lock_file

class EyeRestCore:
    """护眼助手核心业务逻辑 - 纯事件驱动架构"""
    
    def __init__(self):
        """初始化核心逻辑"""
        self.logger = LoggerManager.get_logger()
        self.config = Config()
        self.hotkey_manager = HotkeyManager()
        self.statistics = StatisticsManager()
        
        # 状态机
        self.current_state = AppState.IDLE
        self.state_start_time = time.time()
        
        # 工作相关
        self.work_start_time = 0
        self.work_end_time = 0
        self.remaining_work_time = 0  # 用于暂停/恢复工作计时
        
        # 离开状态相关
        self.away_start_time = 0
        
        # 临时暂停相关
        self.temp_pause_start_time = 0
        self.saved_rest_time = 0  # 暂停时保存的剩余休息时间
        
        # 活动检测
        self.activity_detector = ActivityDetector()
        self.idle_threshold = self.config.idle_threshold_minutes * 60
        
        # 事件队列和控制
        self.event_queue = queue.Queue()
        self.running = True
        
        # 定时器管理
        self.timers = {}  # 存储活动的定时器
        
        # 回调函数
        self.on_status_change = None    # 状态变化回调
        self.on_start_rest = None       # 开始休息回调
        self.on_work_complete = None    # 工作完成回调
        self.on_temp_pause = None       # 临时暂停回调
        self.on_temp_resume = None      # 恢复休息回调
        
        # 启动事件循环线程
        self.event_loop_thread = threading.Thread(target=self._event_loop)
        self.event_loop_thread.daemon = True
        self.event_loop_thread.start()
        
        # 初始化热键
        self._init_hotkey()
        
        self.logger.info("纯事件驱动状态机启动")
    
    def _event_loop(self):
        """纯事件驱动的主循环 - 阻塞等待事件"""
        self.logger.info("事件循环开始")
        
        while self.running:
            try:
                # 阻塞等待事件（1秒超时用于优雅退出）
                try:
                    event = self.event_queue.get(timeout=1.0)
                    self._handle_event(event)
                    self.event_queue.task_done()
                except queue.Empty:
                    # 超时是正常的，用于检查运行状态
                    continue
                    
            except Exception as e:
                self.logger.error(f"事件处理异常: {str(e)}")
        
        self.logger.info("事件循环退出")
    
    def _handle_event(self, event):
        """事件分发器"""
        event_type = event.get('type')
        event_data = event.get('data', {})
        
        # 高频事件使用DEBUG级别，重要事件使用INFO级别
        high_frequency_events = {'UPDATE_DISPLAY', 'CHECK_IDLE', 'CHECK_ACTIVITY'}
        
        if event_type in high_frequency_events:
            self.logger.debug(f"处理事件: {event_type}")
        else:
            self.logger.info(f"处理事件: {event_type}")
        
        # 用户操作事件
        if event_type == 'START_WORK':
            self._handle_start_work_event(event_data)
        elif event_type == 'STOP_WORK':
            self._handle_stop_work_event()
        elif event_type == 'FORCE_REST':
            self._handle_force_rest_event()
        elif event_type == 'REST_COMPLETE':
            self._handle_rest_complete_event()
        elif event_type == 'REST_CANCEL':
            self._handle_rest_cancel_event()
        elif event_type == 'TEMP_PAUSE':
            self._handle_temp_pause_event()
        elif event_type == 'TEMP_RESUME':
            self._handle_temp_resume_event()
        
        # 定时器事件
        elif event_type == 'WORK_TIMEOUT':
            self._handle_work_timeout_event()
        elif event_type == 'TEMP_PAUSE_TIMEOUT':
            self._handle_temp_pause_timeout_event()
        elif event_type == 'CHECK_IDLE':
            self._handle_check_idle_event()
        elif event_type == 'CHECK_ACTIVITY':
            self._handle_check_activity_event()
        elif event_type == 'UPDATE_DISPLAY':
            self._handle_update_display_event()
        
        # 配置事件
        elif event_type == 'UPDATE_CONFIG':
            self._handle_update_config_event(event_data)
    
    def _handle_start_work_event(self, data):
        """处理开始工作事件"""
        if self.current_state != AppState.IDLE:
            self.logger.warning("当前不是空闲状态，无法开始工作")
            return
        
        # 更新配置
        self.config.work_time = data['work_time']
        self.config.rest_time = data['rest_time']
        self.config.play_sound_after_rest = data['play_sound']
        self.config.allow_password_skip = data['allow_password']
        self.config.idle_detection_enabled = data.get('idle_detection_enabled', False)
        self.config.idle_threshold_minutes = data.get('idle_threshold_minutes', 5)
        self.config.temp_pause_enabled = data.get('temp_pause_enabled', True)
        self.config.temp_pause_duration = data.get('temp_pause_duration', 20)
        self.config.save()
        
        # 更新空闲检测阈值
        self.idle_threshold = self.config.idle_threshold_minutes * 60
        
        # 转换到工作状态
        self._transition_to(AppState.WORKING)
        
        # 启动工作相关定时器
        self._start_work_timers()
        
        self.logger.info(f"开始工作会话: {data['work_time']}分钟工作, {data['rest_time']}分钟休息")
    
    def _handle_stop_work_event(self):
        """处理停止工作事件"""
        if self.current_state == AppState.IDLE:
            return
        
        # 取消所有定时器
        self._cancel_all_timers()
        
        # 转换到空闲状态
        self._transition_to(AppState.IDLE)
        self.logger.info("停止工作会话")
    
    def _handle_force_rest_event(self):
        """处理强制休息事件"""
        if self.current_state == AppState.IDLE:
            self.logger.info("程序未运行，强制休息无效")
            return
        
        if self.current_state == AppState.RESTING:
            # 如果当前正在休息，增加1分钟休息时间
            self.logger.info("当前正在休息，增加休息时间")
            if self.on_work_complete:
                wx.CallAfter(self.on_work_complete, "add_time")
        elif self.current_state == AppState.TEMP_PAUSED:
            # 从临时暂停状态立即恢复到休息状态
            self.logger.info("临时暂停中，强制恢复休息")
            self._cancel_timer('temp_pause_timer')
            self._transition_to(AppState.RESTING)
            if self.on_temp_resume:
                wx.CallAfter(self.on_temp_resume)
        elif self.current_state in [AppState.WORKING, AppState.AWAY]:
            # 开始新的休息
            self.logger.info("强制开始休息")
            self._cancel_all_timers()
            self._start_rest()
    
    def _handle_work_timeout_event(self):
        """处理工作时间到期事件"""
        if self.current_state == AppState.WORKING:
            self._cancel_all_timers()
            self._start_rest()
    
    def _handle_check_idle_event(self):
        """处理检查用户空闲事件"""
        if self.current_state == AppState.WORKING:
            if (self.config.idle_detection_enabled and 
                self.activity_detector.is_user_idle(self.idle_threshold)):
                # 用户空闲，暂停工作计时器并转换状态
                self._pause_work_timer()
                self._transition_to(AppState.AWAY)
                # 启动活动检测定时器
                self._start_timer('activity_check', 2, 'CHECK_ACTIVITY')
            else:
                # 用户活跃，继续检查
                self._start_timer('idle_check', 5, 'CHECK_IDLE')
    
    def _handle_check_activity_event(self):
        """处理检查用户活动事件"""
        if self.current_state == AppState.AWAY:
            if not self.activity_detector.is_user_idle(self.idle_threshold):
                # 用户回来了，恢复工作
                self._cancel_timer('activity_check')
                self._resume_work_timer()
                self._transition_to(AppState.WORKING)
                # 重新启动相关定时器
                if self.config.idle_detection_enabled:
                    self._start_timer('idle_check', 5, 'CHECK_IDLE')
                self._start_timer('display_update', 1, 'UPDATE_DISPLAY')
            else:
                # 用户仍然离开，继续检查
                self._start_timer('activity_check', 2, 'CHECK_ACTIVITY')
    
    def _handle_update_display_event(self):
        """处理更新显示事件"""
        if self.current_state == AppState.WORKING:
            self._notify_status_change()
            # 继续定时更新显示
            self._start_timer('display_update', 1, 'UPDATE_DISPLAY')
        elif self.current_state == AppState.AWAY:
            self._notify_status_change()
    
    def _handle_rest_complete_event(self):
        """处理休息完成事件"""
        if self.current_state == AppState.RESTING:
            # 记录统计数据 - 休息正常完成
            self.statistics.record_completed_rest()
            
            # 转换到工作状态，开始新的工作周期
            self._transition_to(AppState.WORKING)
            self._start_work_timers()
            self.logger.info("休息完成，开始新的工作周期")
    
    def _handle_rest_cancel_event(self):
        """处理休息取消事件"""
        if self.current_state == AppState.RESTING:
            # 转换到工作状态，重置工作计时
            self._transition_to(AppState.WORKING)
            self._start_work_timers()
            self.logger.info("休息被取消，重新开始工作")
    
    def _handle_temp_pause_event(self):
        """处理临时暂停事件"""
        if self.current_state == AppState.RESTING and self.config.temp_pause_enabled:
            # 保存当前休息剩余时间 - 使用默认值，实际时间由UI层处理
            self.saved_rest_time = self.config.rest_time * 60
            
            # 转换到临时暂停状态
            self._transition_to(AppState.TEMP_PAUSED)
            
            # 启动临时暂停定时器
            self._start_timer('temp_pause_timer', self.config.temp_pause_duration, 'TEMP_PAUSE_TIMEOUT')
            
            # 通知UI隐藏休息屏幕（UI层会保存实际剩余时间）
            if self.on_temp_pause:
                wx.CallAfter(self.on_temp_pause)
            
            self.logger.info(f"临时暂停休息 {self.config.temp_pause_duration} 秒")
    
    def _handle_temp_resume_event(self):
        """处理恢复休息事件"""
        if self.current_state == AppState.TEMP_PAUSED:
            # 取消暂停定时器
            self._cancel_timer('temp_pause_timer')
            
            # 转换回休息状态
            self._transition_to(AppState.RESTING)
            
            # 通知UI恢复休息屏幕（不传递时间，由UI层自己管理）
            if self.on_temp_resume:
                wx.CallAfter(self.on_temp_resume)
            
            self.logger.info("恢复休息状态")
    
    def _handle_temp_pause_timeout_event(self):
        """处理临时暂停超时事件"""
        if self.current_state == AppState.TEMP_PAUSED:
            # 自动恢复休息
            self._handle_temp_resume_event()
    
    def _handle_update_config_event(self, data):
        """处理配置更新事件"""
        for key, value in data.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        self.config.save()
        
        # 更新空闲检测阈值
        if 'idle_threshold_minutes' in data:
            self.idle_threshold = self.config.idle_threshold_minutes * 60
    
    def _start_work_timers(self):
        """启动工作相关的定时器"""
        # 工作倒计时定时器
        work_seconds = self.config.work_time * 60
        self._start_timer('work_countdown', work_seconds, 'WORK_TIMEOUT')
        
        # 用户活动检测定时器（如果启用）
        if self.config.idle_detection_enabled:
            self._start_timer('idle_check', 5, 'CHECK_IDLE')
        
        # 显示更新定时器
        self._start_timer('display_update', 1, 'UPDATE_DISPLAY')
    
    def _start_timer(self, timer_id, delay_seconds, event_type):
        """启动定时器
        Args:
            timer_id: 定时器唯一标识
            delay_seconds: 延迟秒数
            event_type: 超时后发送的事件类型
        """
        # 取消同名的已存在定时器
        self._cancel_timer(timer_id)
        
        def timer_callback():
            if timer_id in self.timers:  # 检查定时器是否被取消
                # 发送定时器事件
                event = {'type': event_type}
                self.event_queue.put(event)
                # 从活动定时器中移除
                self.timers.pop(timer_id, None)
        
        # 创建并启动定时器
        timer = threading.Timer(delay_seconds, timer_callback)
        timer.daemon = True
        self.timers[timer_id] = timer
        timer.start()
        
        self.logger.debug(f"启动定时器: {timer_id}, 延迟: {delay_seconds}秒")
    
    def _cancel_timer(self, timer_id):
        """取消指定定时器"""
        if timer_id in self.timers:
            self.timers[timer_id].cancel()
            del self.timers[timer_id]
            self.logger.debug(f"取消定时器: {timer_id}")
    
    def _cancel_all_timers(self):
        """取消所有定时器"""
        for timer_id in list(self.timers.keys()):
            self._cancel_timer(timer_id)
        self.logger.debug("取消所有定时器")
    
    def _pause_work_timer(self):
        """暂停工作定时器，保存剩余时间"""
        if 'work_countdown' in self.timers:
            self.remaining_work_time = max(0, self.work_end_time - time.time())
            self._cancel_timer('work_countdown')
            self.logger.debug(f"暂停工作计时器，剩余时间: {self.remaining_work_time}秒")
    
    def _resume_work_timer(self):
        """恢复工作定时器"""
        if hasattr(self, 'remaining_work_time') and self.remaining_work_time > 0:
            self.work_end_time = time.time() + self.remaining_work_time
            self._start_timer('work_countdown', self.remaining_work_time, 'WORK_TIMEOUT')
            self.logger.debug(f"恢复工作计时器，剩余时间: {self.remaining_work_time}秒")
        else:
            # 如果没有剩余时间，开始新的工作周期
            self.work_end_time = time.time() + self.config.work_time * 60
            self._start_timer('work_countdown', self.config.work_time * 60, 'WORK_TIMEOUT')
    
    def _start_rest(self):
        """开始休息"""
        self._transition_to(AppState.RESTING)
        if self.on_start_rest:
            wx.CallAfter(self.on_start_rest, self.config.rest_time)

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
            if not hasattr(self, 'remaining_work_time') or self.remaining_work_time <= 0:
                self.work_start_time = time.time()
                self.work_end_time = self.work_start_time + self.config.work_time * 60
        elif state == AppState.AWAY:
            self.away_start_time = time.time()
        elif state == AppState.TEMP_PAUSED:
            self.temp_pause_start_time = time.time()
        elif state == AppState.IDLE:
            self._reset_timers()

    def _reset_timers(self):
        """重置计时器"""
        self.work_start_time = 0
        self.work_end_time = 0
        self.remaining_work_time = 0
        self.away_start_time = 0
        self.temp_pause_start_time = 0
        self.saved_rest_time = 0

    def _init_hotkey(self):
        """初始化全局热键"""
        try:
            # 收集所有需要注册的热键
            hotkeys_to_register = [
                (self.config.hotkey, self.force_rest)
            ]
            
            # 添加临时暂停热键
            if self.config.temp_pause_enabled:
                hotkeys_to_register.append((self.config.temp_pause_hotkey, self.temp_pause))
            
            # 批量注册所有热键
            self._batch_register_hotkeys(hotkeys_to_register)
                
            self.logger.info("热键初始化成功")
        except Exception as e:
            self.logger.error(f"热键初始化失败: {str(e)}")
    
    def _batch_register_hotkeys(self, hotkey_list):
        """批量注册热键，避免重复注册问题"""
        try:
            # 停止现有监听
            if self.hotkey_manager.is_running:
                self.hotkey_manager.stop()
            
            # 清空现有绑定
            self.hotkey_manager._bindings.clear()
            
            # 批量添加所有热键绑定
            for hotkey_str, callback in hotkey_list:
                normalized_hotkey = self.hotkey_manager._normalize_hotkey(hotkey_str)
                self.hotkey_manager._bindings[normalized_hotkey] = callback
                self.logger.debug(f"添加热键绑定: {normalized_hotkey}")
            
            # 构建绑定列表
            from global_hotkeys import register_hotkeys, start_checking_hotkeys
            bindings = [
                [key, None, func, True]
                for key, func in self.hotkey_manager._bindings.items()
            ]
            
            # 一次性注册所有热键
            register_hotkeys(bindings)
            
            # 开始监听
            start_checking_hotkeys()
            self.hotkey_manager.is_running = True
            
            self.logger.info(f"批量注册热键成功，共 {len(hotkey_list)} 个热键")
            
        except Exception as e:
            self.logger.error(f"批量注册热键失败: {str(e)}")
            raise
    
    # 公共API - 发送事件到状态机
    def start_work_session(self, work_time, rest_time, play_sound, allow_password, **kwargs):
        """发送开始工作事件"""
        event = {
            'type': 'START_WORK',
            'data': {
                'work_time': work_time,
                'rest_time': rest_time,
                'play_sound': play_sound,
                'allow_password': allow_password,
                **kwargs
            }
        }
        self.event_queue.put(event)
    
    def stop_work_session(self):
        """发送停止工作事件"""
        event = {'type': 'STOP_WORK'}
        self.event_queue.put(event)
    
    def force_rest(self, event=None):
        """发送强制休息事件"""
        event = {'type': 'FORCE_REST'}
        self.event_queue.put(event)
        return True  # 总是返回True，因为事件已发送
    
    def temp_pause(self, event=None):
        """发送临时暂停事件 - 只在休息状态时响应"""
        if self.current_state == AppState.RESTING:
            event = {'type': 'TEMP_PAUSE'}
            self.event_queue.put(event)
        return True  # 总是返回True，因为热键需要
    
    def on_rest_complete(self):
        """休息完成回调 - 发送事件"""
        event = {'type': 'REST_COMPLETE'}
        self.event_queue.put(event)
    
    def on_rest_cancel(self):
        """休息取消回调 - 发送事件"""
        event = {'type': 'REST_CANCEL'}
        self.event_queue.put(event)
    
    def update_config(self, **kwargs):
        """更新配置 - 发送事件"""
        event = {
            'type': 'UPDATE_CONFIG',
            'data': kwargs
        }
        self.event_queue.put(event)
    
    def update_hotkey(self, new_hotkey):
        """更新热键设置"""
        try:
            # 标准化新热键格式进行比较
            normalized_new_hotkey = self.hotkey_manager._normalize_hotkey(new_hotkey)
            normalized_current_hotkey = self.hotkey_manager._normalize_hotkey(self.config.hotkey)
            
            # 如果新热键和当前热键相同，跳过设置
            if normalized_new_hotkey == normalized_current_hotkey:
                self.logger.info(f"热键未改变，跳过设置: {new_hotkey}")
                return True
            
            # 收集所有需要重新注册的热键
            hotkeys_to_register = [
                (new_hotkey, self.force_rest)
            ]
            
            # 添加临时暂停热键
            if self.config.temp_pause_enabled:
                hotkeys_to_register.append((self.config.temp_pause_hotkey, self.temp_pause))
            
            # 批量重新注册热键
            self._batch_register_hotkeys(hotkeys_to_register)
            
            self.config.hotkey = new_hotkey
            self.config.save()
            self.logger.info(f"热键更新成功: {new_hotkey}")
            return True
        except Exception as e:
            self.logger.error(f"热键更新失败: {str(e)}")
            return False
    
    def get_remaining_time(self):
        """获取剩余工作时间"""
        if self.current_state != AppState.WORKING:
            return 0
        
        remaining = int(self.work_end_time - time.time())
        return max(0, remaining)
    
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
            if hasattr(self, 'away_start_time') and self.away_start_time > 0:
                away_duration = int(time.time() - self.away_start_time)
                return f"检测到用户离开 ({away_duration//60}:{away_duration%60:02d})"
            return "用户离开"
        elif self.current_state == AppState.TEMP_PAUSED:
            if hasattr(self, 'temp_pause_start_time') and self.temp_pause_start_time > 0:
                pause_duration = int(time.time() - self.temp_pause_start_time)
                remaining = max(0, self.config.temp_pause_duration - pause_duration)
                return f"临时暂停 (还剩 {remaining} 秒)"
            return "临时暂停"
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
    
    # 统计相关接口
    def get_statistics_manager(self):
        """获取统计管理器"""
        return self.statistics
    
    def cleanup(self):
        """清理资源"""
        self._cancel_all_timers()
        self.running = False  # 设置退出标志
        if self.hotkey_manager:
            self.hotkey_manager.stop()
            self.hotkey_manager = None
        # 删除锁文件
        remove_lock_file()
        self.logger.info("核心逻辑清理完成") 