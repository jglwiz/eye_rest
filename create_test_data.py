#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
创建测试数据脚本 - 为统计功能生成一些示例数据
"""

import sys
import os
from datetime import datetime, timedelta

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.lib.statistics_manager import StatisticsManager

def create_test_data():
    """创建测试数据"""
    print("=== 创建测试数据 ===")
    
    # 创建统计管理器
    stats = StatisticsManager()
    
    # 先重置数据，确保从干净状态开始
    stats.reset_statistics()
    print("已重置现有数据")
    
    # 创建最近7天的测试数据，模拟实际使用情况
    test_data = [
        (6, 2),  # 6天前，2次
        (5, 4),  # 5天前，4次
        (4, 1),  # 4天前，1次
        (3, 3),  # 3天前，3次
        (2, 5),  # 2天前，5次
        (1, 2),  # 昨天，2次
        (0, 4),  # 今天，4次
    ]
    
    total_added = 0
    for days_ago, count in test_data:
        target_date = datetime.now() - timedelta(days=days_ago)
        for i in range(count):
            stats.record_completed_rest(target_date)
            total_added += 1
        
        day_name = "今天" if days_ago == 0 else f"{days_ago}天前"
        print(f"{day_name}: 添加了{count}次完成记录")
    
    print(f"\n总共添加了{total_added}次完成记录")
    
    # 显示最终统计
    print(f"统计结果 - 今日: {stats.get_today_count()}, 本周: {stats.get_week_count()}, 总计: {stats.get_total_count()}")
    print(f"平均每日: {stats.get_average_daily_count()}")
    
    print("\n=== 测试数据创建完成 ===")
    print("现在可以打开程序查看统计标签页的效果")

if __name__ == "__main__":
    create_test_data() 