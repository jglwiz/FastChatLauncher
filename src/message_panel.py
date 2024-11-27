import wx
import wx.lib.scrolledpanel as scrolled

class MessagePanel(scrolled.ScrolledPanel):
    def __init__(self, parent):
        super().__init__(parent, style=wx.SUNKEN_BORDER | wx.VSCROLL | wx.WANTS_CHARS)
        self.history_sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.history_sizer)
        
        # 设置滚动
        self.SetupScrolling(scroll_x=True, scroll_y=True, rate_y=20)
        
        # 记录最新的消息文本框
        self.latest_message_text = None
        
        # 绑定鼠标滚轮事件处理函数
        self.Bind(wx.EVT_MOUSEWHEEL, self.OnMouseWheel)
        
    def OnMouseWheel(self, event):
        """处理鼠标滚轮事件"""
        # 获取滚轮旋转方向和位置
        rotation = event.GetWheelRotation()
        position = event.GetPosition()
        
        # 检查鼠标是否在窗口内或当前焦点在消息文本框上
        window_rect = self.GetRect()
        focused_window = wx.Window.FindFocus()
        if window_rect.Contains(position) or (focused_window and isinstance(focused_window, wx.TextCtrl)):
            # 计算新的滚动位置
            current_position = self.GetViewStart()[1]
            new_position = current_position - rotation / event.GetWheelDelta()
            
            # 设置新的滚动位置
            self.Scroll(-1, int(new_position))
        else:
            # 如果鼠标不在窗口内,则跳过处理
            event.Skip()
        
    def create_message_panel(self, sender):
        """创建消息面板"""
        msg_panel = wx.Panel(self)
        msg_sizer = wx.BoxSizer(wx.VERTICAL)
        
        sender_text = wx.StaticText(msg_panel, -1, f"{sender}:")
        sender_text.SetForegroundColour(wx.BLUE if sender == "AI" else wx.BLACK)
        
        # 创建消息文本框
        message_text = wx.TextCtrl(msg_panel, -1, "", 
                                 style=wx.TE_READONLY | wx.TE_AUTO_URL | wx.NO_BORDER | 
                                       wx.TE_BESTWRAP | wx.TE_MULTILINE | wx.TE_NO_VSCROLL)
        
        # 设置文本框的宽度为父窗口的宽度减去边距
        message_text.SetMinSize((self.GetSize()[0] - 40, -1))
        
        # 绑定消息文本框的滚轮事件处理函数
        message_text.Bind(wx.EVT_MOUSEWHEEL, self.OnMouseWheel)
        
        msg_sizer.Add(sender_text, 0, wx.ALL, 5)
        msg_sizer.Add(message_text, 0, wx.EXPAND | wx.ALL, 5)
        msg_panel.SetSizer(msg_sizer)
        
        self.history_sizer.Add(msg_panel, 0, wx.EXPAND | wx.ALL, 5)
        self.Layout()
        self.FitInside()
        self.scroll_to_bottom()
        
        # 更新最新的消息文本框引用
        self.latest_message_text = message_text
        
        return message_text
        
    def update_message_text_size(self, message_text, text):
        """更新消息文本框大小"""
        if not message_text:
            return
            
        # 计算文本需要的高度和宽度
        dc = wx.ClientDC(message_text)
        dc.SetFont(message_text.GetFont())
        
        # 获取文本框的宽度（减去边距）
        text_width = message_text.GetSize().width - 20
        
        # 计算所需的总高度
        text_height = 0
        line_height = dc.GetCharHeight()
        
        # 为每行计算高度和宽度
        for line in text.split('\n'):
            if not line:
                text_height += line_height
                continue
                
            # 计算这行文字需要多少个行高
            extent = dc.GetPartialTextExtents(line)
            if not extent:
                text_height += line_height
                continue
                
            # 计算换行
            current_width = 0
            for width in extent:
                if width - current_width > text_width:
                    text_height += line_height
                    current_width = width
            text_height += line_height
        
        # 设置新的大小
        message_text.SetMinSize((text_width, text_height + 10))  # 添加一些边距
        
        # 更新布局
        message_text.GetParent().Layout()
        self.Layout()
        self.FitInside()
        self.scroll_to_bottom()
        
    def add_message(self, sender, message):
        """添加消息到历史记录"""
        if sender == "AI":
            return  # AI消息由async_send_message处理
            
        message_text = self.create_message_panel(sender)
        message_text.SetValue(message)
        self.update_message_text_size(message_text, message)
        
    def scroll_to_bottom(self):
        """确保滚动到底部"""
        # 强制更新布局
        self.Layout()
        self.FitInside()
        
        # 获取虚拟大小和实际大小
        virtual_size = self.GetVirtualSize()
        client_size = self.GetClientSize()
        
        # 计算最大滚动位置
        max_scroll = max(0, virtual_size[1] - client_size[1])
        
        # 滚动到底部
        self.Scroll(0, max_scroll)
        
        # 强制刷新显示
        self.Refresh()
        
    def clear_history(self):
        """清空历史记录"""
        for child in self.GetChildren():
            child.Destroy()
        self.history_sizer.Clear()
        self.latest_message_text = None
        self.Layout()
