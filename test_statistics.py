#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
统计功能测试脚本
"""

import sys
import os
from datetime import datetime, timedelta

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.lib.statistics_manager import StatisticsManager

def test_statistics():
    """测试统计功能"""
    print("=== 测试统计管理器 ===")
    
    # 创建统计管理器
    stats = StatisticsManager()
    
    # 1. 测试初始状态
    print(f"初始状态 - 今日: {stats.get_today_count()}, 本周: {stats.get_week_count()}, 总计: {stats.get_total_count()}")
    
    # 2. 添加一些测试数据
    print("\n添加测试数据...")
    
    # 添加今天的数据
    for i in range(3):
        stats.record_completed_rest()
        print(f"添加第{i+1}次完成记录")
    
    # 添加昨天的数据
    yesterday = datetime.now() - timedelta(days=1)
    for i in range(2):
        stats.record_completed_rest(yesterday)
        print(f"添加昨天第{i+1}次完成记录")
    
    # 添加前天的数据
    day_before_yesterday = datetime.now() - timedelta(days=2)
    stats.record_completed_rest(day_before_yesterday)
    print("添加前天1次完成记录")
    
    # 3. 检查统计结果
    print(f"\n更新后 - 今日: {stats.get_today_count()}, 本周: {stats.get_week_count()}, 总计: {stats.get_total_count()}")
    print(f"平均每日: {stats.get_average_daily_count()}")
    
    # 4. 测试每日记录
    print("\n最近7天记录:")
    daily_records = stats.get_daily_records(7)
    for record in daily_records:
        print(f"  {record['display_date']}: {record['completed']}次")
        
    # 5. 测试重置功能
    print("\n测试重置功能...")
    stats.reset_statistics()
    print(f"重置后 - 今日: {stats.get_today_count()}, 本周: {stats.get_week_count()}, 总计: {stats.get_total_count()}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_statistics() 