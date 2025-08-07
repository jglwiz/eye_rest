from enum import Enum

class AppState(Enum):
    """应用程序状态枚举"""
    IDLE = "idle"           # 初始状态 - 程序启动但未开始工作
    WORKING = "working"     # 工作状态 - 正在工作计时
    RESTING = "resting"     # 休息状态 - 正在休息
    AWAY = "away"          # 离开状态 - 用户离开电脑 
    TEMP_PAUSED = "temp_paused"  # 临时暂停状态 - 休息期间的短暂暂停 