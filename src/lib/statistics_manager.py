import json
import os
from datetime import datetime, date, timedelta
from .logger_manager import LoggerManager

class StatisticsManager:
    """统计管理器，处理休息完成次数的统计"""
    
    def __init__(self):
        """初始化统计管理器"""
        self.logger = LoggerManager.get_logger()
        self.stats_path = "statistics.json"
        self.data = {
            "total_completed": 0,
            "daily_records": []  # [{"date": "2024-01-15", "completed": 5}, ...]
        }
        self.load()
    
    def load(self):
        """从文件加载统计数据"""
        if os.path.exists(self.stats_path):
            try:
                with open(self.stats_path, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
                self.logger.info("统计数据加载成功")
            except Exception as e:
                self.logger.error(f"统计数据加载失败: {str(e)}")
                self._init_default_data()
        else:
            self._init_default_data()
    
    def _init_default_data(self):
        """初始化默认数据"""
        self.data = {
            "total_completed": 0,
            "daily_records": []
        }
        self.save()
    
    def save(self):
        """保存统计数据到文件"""
        try:
            with open(self.stats_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            self.logger.info("统计数据保存成功")
        except Exception as e:
            self.logger.error(f"统计数据保存失败: {str(e)}")
    
    def record_completed_rest(self, timestamp=None):
        """记录一次完成的休息
        Args:
            timestamp: 时间戳，如果不提供则使用当前时间
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        today_str = timestamp.strftime("%Y-%m-%d")
        
        # 增加总计数
        self.data["total_completed"] += 1
        
        # 查找或创建今日记录
        today_record = None
        for record in self.data["daily_records"]:
            if record["date"] == today_str:
                today_record = record
                break
        
        if today_record:
            today_record["completed"] += 1
        else:
            self.data["daily_records"].append({
                "date": today_str,
                "completed": 1
            })
        
        # 按日期排序
        self.data["daily_records"].sort(key=lambda x: x["date"])
        
        # 清理过老的记录（保留最近30天）
        self._cleanup_old_records()
        
        # 保存数据
        self.save()
        
        self.logger.info(f"记录休息完成: {today_str}")
    
    def _cleanup_old_records(self):
        """清理超过30天的旧记录"""
        cutoff_date = (date.today() - timedelta(days=30)).strftime("%Y-%m-%d")
        self.data["daily_records"] = [
            record for record in self.data["daily_records"]
            if record["date"] >= cutoff_date
        ]
    
    def get_today_count(self):
        """获取今日完成次数"""
        today_str = date.today().strftime("%Y-%m-%d")
        for record in self.data["daily_records"]:
            if record["date"] == today_str:
                return record["completed"]
        return 0
    
    def get_week_count(self):
        """获取本周完成次数"""
        today = date.today()
        # 获取本周的开始日期（周一）
        week_start = today - timedelta(days=today.weekday())
        week_start_str = week_start.strftime("%Y-%m-%d")
        
        week_count = 0
        for record in self.data["daily_records"]:
            if record["date"] >= week_start_str:
                week_count += record["completed"]
        return week_count
    
    def get_total_count(self):
        """获取总计完成次数"""
        return self.data["total_completed"]
    
    def get_daily_records(self, days=7):
        """获取最近N天的记录
        Args:
            days: 天数，默认7天
        Returns:
            list: [{"date": "2024-01-15", "completed": 5}, ...]
        """
        today = date.today()
        result = []
        
        for i in range(days):
            target_date = today - timedelta(days=days-1-i)
            target_date_str = target_date.strftime("%Y-%m-%d")
            
            # 查找该日期的记录
            completed = 0
            for record in self.data["daily_records"]:
                if record["date"] == target_date_str:
                    completed = record["completed"]
                    break
            
            result.append({
                "date": target_date_str,
                "completed": completed,
                "display_date": target_date.strftime("%m-%d")  # 显示用的简短日期
            })
        
        return result
    
    def get_average_daily_count(self):
        """获取平均每日完成次数"""
        if not self.data["daily_records"]:
            return 0.0
        
        total_days = len(self.data["daily_records"])
        total_completed = sum(record["completed"] for record in self.data["daily_records"])
        
        return round(total_completed / total_days, 1) if total_days > 0 else 0.0
    
    def reset_statistics(self):
        """重置所有统计数据"""
        self.data = {
            "total_completed": 0,
            "daily_records": []
        }
        self.save()
        self.logger.info("统计数据已重置") 