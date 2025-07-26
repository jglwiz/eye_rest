import wx

class StatisticsChart(wx.Panel):
    """统计图表面板 - 显示每日休息完成次数的条形图"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.data = []  # 数据格式: [{"display_date": "01-15", "completed": 5}, ...]
        self.max_value = 10  # 最大值，用于计算比例
        
        # 颜色设置
        self.bg_color = wx.Colour(245, 245, 245)
        self.bar_color = wx.Colour(52, 152, 219)  # 蓝色
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
            data: [{"display_date": "01-15", "completed": 5}, ...]
        """
        self.data = data if data else []
        if self.data:
            self.max_value = max(10, max(item["completed"] for item in self.data))
        else:
            self.max_value = 10
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
        margin_left = 40
        margin_right = 20
        margin_top = 20
        margin_bottom = 40
        
        # 计算绘图区域
        chart_width = width - margin_left - margin_right
        chart_height = height - margin_top - margin_bottom
        
        if chart_width <= 0 or chart_height <= 0:
            return
            
        # 绘制Y轴刻度和网格线
        self._draw_y_axis(dc, margin_left, margin_top, chart_height)
        
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
        steps = 5
        step_value = max(1, self.max_value // steps)
        
        for i in range(steps + 1):
            value = i * step_value
            if value > self.max_value:
                break
                
            # 计算Y坐标
            y_pos = y + height - int(height * value / self.max_value)
            
            # 绘制刻度标签
            text = str(value)
            text_size = dc.GetTextExtent(text)
            dc.DrawText(text, x - text_size.width - 5, y_pos - text_size.height // 2)
            
            # 绘制网格线
            if i > 0:  # 不绘制底部网格线
                dc.DrawLine(x, y_pos, x + self.GetSize().width - 60, y_pos)
                
    def _draw_bars(self, dc, x, y, width, height):
        """绘制条形图"""
        if not self.data:
            return
            
        bar_count = len(self.data)
        bar_width = width // bar_count * 0.6  # 条形宽度，留出间距
        bar_spacing = width / bar_count
        
        dc.SetPen(wx.Pen(self.bar_color, 1))
        dc.SetBrush(wx.Brush(self.bar_color))
        dc.SetTextForeground(self.text_color)
        
        font = wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        dc.SetFont(font)
        
        for i, item in enumerate(self.data):
            completed = item["completed"]
            
            # 计算条形位置和大小
            bar_x = x + i * bar_spacing + (bar_spacing - bar_width) / 2
            bar_height = height * completed / self.max_value if self.max_value > 0 else 0
            bar_y = y + height - bar_height
            
            # 绘制条形
            if bar_height > 0:
                dc.DrawRectangle(int(bar_x), int(bar_y), int(bar_width), int(bar_height))
                
                # 在条形上方显示数值
                if completed > 0:
                    text = str(completed)
                    text_size = dc.GetTextExtent(text)
                    text_x = bar_x + (bar_width - text_size.width) / 2
                    text_y = bar_y - text_size.height - 2
                    dc.DrawText(text, int(text_x), int(text_y))
                    
    def _draw_x_labels(self, dc, x, y, width):
        """绘制X轴标签（日期）"""
        if not self.data:
            return
            
        dc.SetTextForeground(self.text_color)
        font = wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        dc.SetFont(font)
        
        bar_count = len(self.data)
        bar_spacing = width / bar_count
        
        for i, item in enumerate(self.data):
            date_text = item["display_date"]
            text_size = dc.GetTextExtent(date_text)
            
            # 计算文本位置（居中对齐）
            text_x = x + i * bar_spacing + (bar_spacing - text_size.width) / 2
            text_y = y + 5
            
            dc.DrawText(date_text, int(text_x), int(text_y)) 