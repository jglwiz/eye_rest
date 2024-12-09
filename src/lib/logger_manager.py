import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime

class LoggerManager:
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LoggerManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if LoggerManager._initialized:
            return
            
        LoggerManager._initialized = True
        self.logger = logging.getLogger('ChatApp')
        self.logger.setLevel(logging.DEBUG)
        
        # 创建logs目录
        logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)
            
        # 日志文件路径
        log_file = os.path.join(logs_dir, f'chat_app_{datetime.now().strftime("%Y%m%d")}.log')
        
        # 创建文件处理器(最大10MB,保留5个备份)
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        
        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 设置日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # 添加处理器
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    @staticmethod
    def get_logger():
        """获取logger实例"""
        return LoggerManager().logger

# 使用示例:
# from logger_manager import LoggerManager
# logger = LoggerManager.get_logger()
# logger.debug('调试信息')
# logger.info('普通信息')
# logger.warning('警告信息')
# logger.error('错误信息')
