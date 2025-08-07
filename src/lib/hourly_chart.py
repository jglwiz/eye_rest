import wx

class HourlyChart(wx.Panel):
    """小时统计图表面板 - 显示今日24小时休息完成次数的条形图"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.data = []  # 数据格式: [{"hour": 0, "completed": 1}, {"hour": 1, "completed": 0}, ...]
        self.max_value = 5  # 最大值，用于计算比例
        
        # 颜色设置
        self.bg_color = wx.Colour(245, 245, 245)
        self.bar_color = wx.Colour(46, 204, 113)  # 绿色
        self.text_color = wx.Colour(44, 62, 80)   # 深灰色
        self.grid_color = wx.Colour(189, 195, 199) # 浅灰色
        
        # 绑定绘图事件
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_SIZE, self.on_size)
        
        # 设置背景色
        self.SetBackgroundColour(self.bg_color)
        
    def set_data(self, data):
        """设置图表数据
        Args:
            data: [{"hour": 0, "completed": 1}, {"hour": 1, "completed": 0}, ...]
        """
        self.data = data if data else []
        if self.data:
            self.max_value = max(5, max(item["completed"] for item in self.data))
        else:
            self.max_value = 5
        self.Refresh()  # 触发重绘
        
    def on_size(self, event):
        """窗口大小变化时重绘"""
        self.Refresh()
        event.Skip()
        
    def on_paint(self, event):
        """绘制图表"""
        dc = wx.PaintDC(self)
        self.draw_chart(dc)
        
    def draw_chart(self, dc):
        """绘制图表内容"""
        size = self.GetSize()
        width, height = size.width, size.height
        
        if width <= 0 or height <= 0:
            return
            
        # 清空背景
        dc.SetBackground(wx.Brush(self.bg_color))
        dc.Clear()
        
        if not self.data:
            # 没有数据时显示提示
            dc.SetTextForeground(self.text_color)
            font = wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
            dc.SetFont(font)
            text = "暂无数据"
            text_size = dc.GetTextExtent(text)
            dc.DrawText(text, (width - text_size.width) // 2, (height - text_size.height) // 2)
            return
            
        # 设置边距
        margin_left = 10
        margin_right = 20
        margin_top = 20
        margin_bottom = 30
        
        # 计算绘图区域
        chart_width = width - margin_left - margin_right
        chart_height = height - margin_top - margin_bottom
        
        if chart_width <= 0 or chart_height <= 0:
            return
            
        # 绘制条形图
        self._draw_bars(dc, margin_left, margin_top, chart_width, chart_height)
        
        # 绘制X轴标签
        self._draw_x_labels(dc, margin_left, margin_top + chart_height, chart_width)
        
    def _draw_y_axis(self, dc, x, y, height):
        """绘制Y轴刻度和网格线"""
        dc.SetPen(wx.Pen(self.grid_color, 1))
        dc.SetTextForeground(self.text_color)
        font = wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        dc.SetFont(font)
        
        # 计算刻度
        steps = min(5, self.max_value)
        if steps == 0:
            steps = 1
        step_value = max(1, self.max_value // steps)
        
        for i in range(steps + 1):
            value = i * step_value
            if value > self.max_value:
                break
                
            # 计算Y坐标
            y_pos = y + height - int(height * value / self.max_value) if self.max_value > 0 else y + height
            
            # 绘制刻度标签
            text = str(value)
            text_size = dc.GetTextExtent(text)
            dc.DrawText(text, x - text_size.width - 5, y_pos - text_size.height // 2)
            
            # 绘制网格线
            if i > 0:  # 不绘制底部网格线
                dc.DrawLine(x, y_pos, x + self.GetSize().width - 50, y_pos)
                
    def _draw_bars(self, dc, x, y, width, height):
        """绘制条形图"""
        if not self.data:
            return
            
        bar_count = 24  # 固定24小时
        bar_width = width // bar_count * 0.85  # 条形宽度，留出间距
        bar_spacing = width / bar_count
        
        dc.SetPen(wx.Pen(self.bar_color, 1))
        dc.SetBrush(wx.Brush(self.bar_color))
        dc.SetTextForeground(self.text_color)
        
        font = wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)  # 增加字体大小到16
        dc.SetFont(font)
        
        # 创建小时到完成次数的映射
        hour_data = {item["hour"]: item["completed"] for item in self.data}
        
        for hour in range(24):
            completed = hour_data.get(hour, 0)
            
            # 计算条形位置和大小
            bar_x = x + hour * bar_spacing + (bar_spacing - bar_width) / 2
            bar_height = height * completed / self.max_value if self.max_value > 0 else 0
            bar_y = y + height - bar_height
            
            # 绘制条形
            if bar_height > 0:
                dc.DrawRectangle(int(bar_x), int(bar_y), int(bar_width), int(bar_height))
                
                # 在条形上方显示数值（只有大于0时才显示）
                if completed > 0:
                    text = str(completed)
                    text_size = dc.GetTextExtent(text)
                    text_x = bar_x + (bar_width - text_size.width) / 2
                    text_y = bar_y - text_size.height - 2
                    dc.DrawText(text, int(text_x), int(text_y))
                    
    def _draw_x_labels(self, dc, x, y, width):
        """绘制X轴标签（小时）"""
        dc.SetTextForeground(self.text_color)  # 使用白色文字
        font = wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)  # 增加字体大小到14并加粗
        dc.SetFont(font)
        
        bar_count = 24
        bar_spacing = width / bar_count
        
        # 只显示关键小时标签：0, 6, 12, 18
        key_hours = [0, 6, 12, 18]
        
        for hour in key_hours:
            hour_text = f"{hour:02d}"
            text_size = dc.GetTextExtent(hour_text)
            
            # 计算文本位置（居中对齐）
            text_x = x + hour * bar_spacing + (bar_spacing - text_size.width) / 2
            text_y = y + 5
            
            dc.DrawText(hour_text, int(text_x), int(text_y))


class DarkHourlyChart(wx.Panel):
    """黑底小时统计图表面板 - 适用于休息界面的黑色背景"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.data = []  # 数据格式: [{"hour": 0, "completed": 1}, {"hour": 1, "completed": 0}, ...]
        self.max_value = 5  # 最大值，用于计算比例
        
        # 黑底颜色设置
        self.bg_color = wx.BLACK
        self.bar_color = wx.WHITE  # 白色条形图
        self.text_color = wx.WHITE   # 白色文字
        self.axis_color = wx.WHITE # 白色坐标轴
        self.grid_color = wx.Colour(80, 80, 80) # 深灰色网格
        
        # 绑定绘图事件
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_SIZE, self.on_size)
        
        # 设置黑色背景
        self.SetBackgroundColour(self.bg_color)
        
    def set_data(self, data):
        """设置图表数据
        Args:
            data: [{"hour": 0, "completed": 1}, {"hour": 1, "completed": 0}, ...]
        """
        self.data = data if data else []
        if self.data:
            self.max_value = max(5, max(item["completed"] for item in self.data))
        else:
            self.max_value = 5
        self.Refresh()  # 触发重绘
        
    def on_size(self, event):
        """窗口大小变化时重绘"""
        self.Refresh()
        event.Skip()
        
    def on_paint(self, event):
        """绘制图表"""
        dc = wx.PaintDC(self)
        self.draw_chart(dc)
        
    def draw_chart(self, dc):
        """绘制图表内容"""
        size = self.GetSize()
        width, height = size.width, size.height
        
        if width <= 0 or height <= 0:
            return
            
        # 清空背景
        dc.SetBackground(wx.Brush(self.bg_color))
        dc.Clear()
        
        if not self.data:
            # 没有数据时显示提示
            dc.SetTextForeground(self.text_color)
            font = wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
            dc.SetFont(font)
            text = "暂无数据"
            text_size = dc.GetTextExtent(text)
            dc.DrawText(text, (width - text_size.width) // 2, (height - text_size.height) // 2)
            return
            
        # 设置边距
        margin_left = 10
        margin_right = 20
        margin_top = 20
        margin_bottom = 30
        
        # 计算绘图区域
        chart_width = width - margin_left - margin_right
        chart_height = height - margin_top - margin_bottom
        
        if chart_width <= 0 or chart_height <= 0:
            return
            
        # 绘制坐标轴
        self._draw_axes(dc, margin_left, margin_top, chart_width, chart_height)
        
        # 绘制条形图
        self._draw_bars(dc, margin_left, margin_top, chart_width, chart_height)
        
        # 绘制X轴标签
        self._draw_x_labels(dc, margin_left, margin_top + chart_height, chart_width)
        
    def _draw_axes(self, dc, x, y, width, height):
        """绘制坐标轴"""
        dc.SetPen(wx.Pen(self.axis_color, 2))  # 增加线宽到2
        dc.SetBrush(wx.Brush(self.axis_color))
        
        # 绘制X轴（底部水平线）
        dc.DrawLine(x, y + height, x + width, y + height)
        
        # 绘制Y轴（左侧垂直线）
        dc.DrawLine(x, y, x, y + height)
        
        # 绘制X轴箭头
        arrow_size = 8
        arrow_x = x + width
        arrow_y = y + height
        
        # 创建X轴箭头的三个点（向右的三角形）
        arrow_points = [
            wx.Point(arrow_x, arrow_y),  # 箭头尖端
            wx.Point(arrow_x - arrow_size, arrow_y - arrow_size//2),  # 上方点
            wx.Point(arrow_x - arrow_size, arrow_y + arrow_size//2)   # 下方点
        ]
        
        # 绘制填充的X轴箭头三角形
        dc.DrawPolygon(arrow_points)
        
        # 绘制Y轴箭头
        y_arrow_x = x
        y_arrow_y = y
        
        # 创建Y轴箭头的三个点（向上的三角形）
        y_arrow_points = [
            wx.Point(y_arrow_x, y_arrow_y),  # 箭头尖端
            wx.Point(y_arrow_x - arrow_size//2, y_arrow_y + arrow_size),  # 左方点
            wx.Point(y_arrow_x + arrow_size//2, y_arrow_y + arrow_size)   # 右方点
        ]
        
        # 绘制填充的Y轴箭头三角形
        dc.DrawPolygon(y_arrow_points)
        
    def _draw_bars(self, dc, x, y, width, height):
        """绘制条形图"""
        if not self.data:
            return
            
        bar_count = 24  # 固定24小时
        bar_width = width // bar_count * 0.85  # 条形宽度，留出间距
        bar_spacing = width / bar_count
        
        dc.SetPen(wx.Pen(self.bar_color, 1))
        dc.SetBrush(wx.Brush(self.bar_color))
        dc.SetTextForeground(self.text_color)
        
        font = wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        dc.SetFont(font)
        
        # 创建小时到完成次数的映射
        hour_data = {item["hour"]: item["completed"] for item in self.data}
        
        for hour in range(24):
            completed = hour_data.get(hour, 0)
            
            # 计算条形位置和大小
            bar_x = x + hour * bar_spacing + (bar_spacing - bar_width) / 2
            bar_height = height * completed / self.max_value if self.max_value > 0 else 0
            bar_y = y + height - bar_height
            
            # 绘制条形
            if bar_height > 0:
                dc.DrawRectangle(int(bar_x), int(bar_y), int(bar_width), int(bar_height))
                
                # 在条形上方显示数值（只有大于0时才显示）
                if completed > 0:
                    text = str(completed)
                    text_size = dc.GetTextExtent(text)
                    text_x = bar_x + (bar_width - text_size.width) / 2
                    text_y = bar_y - text_size.height - 2
                    dc.DrawText(text, int(text_x), int(text_y))
                    
    def _draw_x_labels(self, dc, x, y, width):
        """绘制X轴标签（小时）"""
        dc.SetTextForeground(self.text_color)  # 使用白色文字
        font = wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)  # 增加字体大小到14并加粗
        dc.SetFont(font)
        
        bar_count = 24
        bar_spacing = width / bar_count
        
        # 增加更多小时标签：6,8,10,12,14,16,18,20,22
        key_hours = [6,7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 20, 22]
        
        for hour in key_hours:
            hour_text = f"{hour:02d}"
            text_size = dc.GetTextExtent(hour_text)
            
            # 计算文本位置（居中对齐）
            text_x = x + hour * bar_spacing + (bar_spacing - text_size.width) / 2
            text_y = y + 5
            
            dc.DrawText(hour_text, int(text_x), int(text_y)) 