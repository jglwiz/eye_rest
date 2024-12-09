from .logger_manager import LoggerManager
from global_hotkeys import *

class HotkeyManager:
    """全局热键管理器"""
    
    def __init__(self):
        """初始化热键管理器"""
        self.logger = LoggerManager.get_logger()
        self.is_running = False
        self._bindings = {}  # 存储热键绑定 {hotkey_str: callback}
    
    def _normalize_hotkey(self, hotkey_str):
        """标准化热键字符串格式
        
        Args:
            hotkey_str: 原始热键字符串，如 "ctrl+shift+z" 或 "win+1"
            
        Returns:
            str: 标准化后的热键字符串，如 "control + shift + z" 或 "window + 1"
        """
        # 转换为小写以统一处理
        hotkey_str = hotkey_str.lower()
        
        # 替换常见的缩写
        replacements = {
            'ctrl': 'control',
            'win': 'window'
        }
        
        # 分割并处理每个部分
        parts = [part.strip() for part in hotkey_str.split('+')]
        converted_parts = [replacements.get(part, part) for part in parts]
        
        # 用 " + " 连接所有部分
        return " + ".join(converted_parts)
    
    def register_hotkey(self, hotkey_str, callback):
        """注册全局热键
        
        Args:
            hotkey_str: 热键字符串，如 "ctrl+shift+z"
            callback: 热键触发时的回调函数
            
        Returns:
            bool: 注册是否成功
            
        Raises:
            ValueError: 热键字符串格式无效
            RuntimeError: 热键注册失败
        """
        try:
            if not hotkey_str or not callback:
                raise ValueError("热键字符串和回调函数不能为空")
            
            # 标准化热键字符串
            normalized_hotkey = self._normalize_hotkey(hotkey_str)
            
            # 如果已经在运行，需要先停止当前的热键监听
            if self.is_running:
                self.stop()
            
            # 存储绑定关系
            self._bindings[normalized_hotkey] = callback
            
            # 构建绑定列表
            bindings = [
                [key, None, func, True]
                for key, func in self._bindings.items()
            ]
            
            # 注册热键
            register_hotkeys(bindings)
            
            # 开始监听
            start_checking_hotkeys()
            self.is_running = True
            
            self.logger.info(f"注册热键成功: {normalized_hotkey}")
            return True
            
        except Exception as e:
            self.logger.error(f"注册热键失败: {str(e)}")
            raise RuntimeError(f"注册热键失败: {str(e)}")
    
    def unregister_hotkey(self, hotkey_str):
        """取消注册指定的热键
        
        Args:
            hotkey_str: 要取消注册的热键字符串
            
        Returns:
            bool: 取消注册是否成功
        """
        try:
            normalized_hotkey = self._normalize_hotkey(hotkey_str)
            if normalized_hotkey in self._bindings:
                del self._bindings[normalized_hotkey]
                
                # 如果还有其他热键，重新注册
                if self._bindings:
                    self.stop()
                    bindings = [
                        [key, None, func, True]
                        for key, func in self._bindings.items()
                    ]
                    register_hotkeys(bindings)
                    start_checking_hotkeys()
                    self.is_running = True
                else:
                    self.stop()
                
                self.logger.info(f"取消注册热键成功: {normalized_hotkey}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"取消注册热键失败: {str(e)}")
            return False
    
    def stop(self):
        """停止所有热键监听"""
        if self.is_running:
            stop_checking_hotkeys()
            self.is_running = False
            self.logger.info("停止所有热键监听")
    
    def __del__(self):
        """清理资源"""
        self.stop()
