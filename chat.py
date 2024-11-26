import wx
import json
import os
import keyboard
from openai import OpenAI
from wx.adv import TaskBarIcon
import wx.lib.scrolledpanel as scrolled
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
import time
from ui import ChatTrayIcon, ConfigDialog, AgentConfigDialog


class ChatFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="Quick Chat Launcher", size=(400, 600),
                        style=wx.DEFAULT_FRAME_STYLE)
        
        self.load_config()
        self.InitUI()
        
        # 创建线程池
        self.thread_pool = ThreadPoolExecutor(max_workers=1)
        
        # 创建系统托盘图标
        self.tray_icon = ChatTrayIcon(self)
        
        # 绑定关闭事件
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        
        # 设置最小窗口大小
        self.SetMinSize((400, 600))
        
        # 强制更新布局
        self.Layout()
        wx.CallAfter(self.UpdateLayout)
        
        # 设置全局热键
        self.setup_global_hotkey()
        
        # 初始化聊天历史
        self.current_agent = "default"
        self.chat_history = [
            ("system", self.config['agents']['default']['role_system'])
        ]

        # 设置初始窗口位置为屏幕中央
        self.Center()
        
        # 设置窗口置顶
        self.SetWindowStyle(wx.DEFAULT_FRAME_STYLE | wx.STAY_ON_TOP)
        self.SetWindowStyle(wx.DEFAULT_FRAME_STYLE)
        
        # 记录最新的消息文本框
        self.latest_message_text = None
        
    def setup_global_hotkey(self):
        """设置全局热键"""
        max_retries = 10  # 最大重试次数
        retry_delay = 2   # 每次重试间隔秒数
        
        for attempt in range(max_retries):
            try:
                # 先移除所有已存在的热键
                keyboard.unhook_all()
                # 添加新的热键
                keyboard.add_hotkey(self.config['hotkeys']['show_window'], self.safe_toggle_window, suppress=True)
                print(f"全局热键注册成功,尝试次数: {attempt + 1}")
                return
            except Exception as e:
                print(f"设置全局热键失败 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:  # 如果不是最后一次尝试
                    time.sleep(retry_delay)     # 等待一段时间后重试
                else:
                    print("全局热键注册失败,已达到最大重试次数")
        
    def safe_toggle_window(self):
        """线程安全的窗口切换"""
        wx.CallAfter(self.toggle_window)
            
    def toggle_window(self):
        """切换窗口显示状态"""
        if self.IsShown():
            self.minimize_to_tray()
        else:
            self.show_window()
            
    def show_window(self):
        """显示窗口"""
        # 确保在主线程中执行
        self.Show(True)
        self.Raise()
        
        # 获取屏幕尺寸
        display = wx.Display().GetGeometry()
        # 获取窗口尺寸
        size = self.GetSize()
        # 计算居中位置
        x = (display.width - size.width) // 2
        y = (display.height - size.height) // 2
        # 设置窗口位置
        self.SetPosition((x, y))
        
        self.SetFocus()
        
        # 尝试置顶窗口
        self.SetWindowStyle(wx.DEFAULT_FRAME_STYLE | wx.STAY_ON_TOP)
        self.SetWindowStyle(wx.DEFAULT_FRAME_STYLE)
        
    def minimize_to_tray(self):
        """最小化到系统托盘"""
        self.Hide()
        
    def force_exit(self, event):
        """强制退出程序"""
        try:
            keyboard.unhook_all()  # 清除所有热键
        except:
            pass
        self.tray_icon.Destroy()
        self.Destroy()
        wx.GetApp().ExitMainLoop()
        
    def OnConfig(self, event):
        dlg = ConfigDialog(self, self.config)
        if dlg.ShowModal() == wx.ID_OK:
            self.load_config()
            # 重新设置全局热键
            self.setup_global_hotkey()
        dlg.Destroy()

    def OnAgentConfig(self, event):
        dlg = AgentConfigDialog(self, self.config)
        if dlg.ShowModal() == wx.ID_OK:
            self.load_config()
            # 重置聊天历史为当前agent的system role
            self.chat_history = [
                ("system", self.config['agents'][self.current_agent]['role_system'])
            ]
        dlg.Destroy()
        
    def OnClose(self, event):
        self.minimize_to_tray()

    def create_message_panel(self, sender):
        """创建消息面板"""
        msg_panel = wx.Panel(self.history_panel)
        msg_sizer = wx.BoxSizer(wx.VERTICAL)
        
        sender_text = wx.StaticText(msg_panel, -1, f"{sender}:")
        sender_text.SetForegroundColour(wx.BLUE if sender == "AI" else wx.BLACK)
        
        # 创建消息文本框
        message_text = wx.TextCtrl(msg_panel, -1, "", 
                                 style=wx.TE_READONLY | wx.TE_AUTO_URL | wx.NO_BORDER | 
                                       wx.TE_BESTWRAP | wx.TE_MULTILINE | wx.TE_NO_VSCROLL)
        
        # 设置初始大小为5行
        dc = wx.ClientDC(message_text)
        dc.SetFont(message_text.GetFont())
        line_height = dc.GetCharHeight()
        initial_height = line_height * 5
        message_text.SetMinSize((-1, initial_height))
        
        msg_sizer.Add(sender_text, 0, wx.ALL, 5)
        msg_sizer.Add(message_text, 0, wx.EXPAND | wx.ALL, 5)
        msg_panel.SetSizer(msg_sizer)
        
        self.history_sizer.Add(msg_panel, 0, wx.EXPAND | wx.ALL, 5)
        self.history_panel.Layout()
        self.history_panel.FitInside()
        self.scroll_to_bottom()
        
        # 更新最新的消息文本框引用
        self.latest_message_text = message_text
        
        return message_text

    def update_message_text_size(self, message_text, text):
        """更新消息文本框大小"""
        if not message_text:
            return
            
        # 计算文本需要的高度
        dc = wx.ClientDC(message_text)
        dc.SetFont(message_text.GetFont())
        
        # 获取文本框的宽度（减去边距）
        text_width = message_text.GetSize().width - 20
        
        # 计算所需的总高度
        text_height = 0
        line_height = dc.GetCharHeight()
        
        # 为每行计算高度
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
        
        # 确保至少有5行的高度
        min_height = line_height * 5
        text_height = max(text_height, min_height)
        
        # 设置新的大小
        message_text.SetMinSize((-1, text_height + 10))  # 添加一些边距
        
        # 更新布局
        message_text.GetParent().Layout()
        self.history_panel.Layout()
        self.history_panel.FitInside()
        self.scroll_to_bottom()

    def check_for_agent(self, message):
        """检查消息是否包含@nickname指令"""
        if message.startswith('@'):
            parts = message.split(' ', 1)
            nickname = parts[0][1:]  # 去掉@
            if nickname in self.config['agents']:
                self.current_agent = nickname
                # 重置聊天历史
                self.chat_history = [
                    ("system", self.config['agents'][nickname]['role_system'])
                ]
                return parts[1] if len(parts) > 1 else ""
            else:
                # 如果找不到指定的agent，使用default
                self.current_agent = "default"
                self.chat_history = [
                    ("system", self.config['agents']['default']['role_system'])
                ]
        return message

    def async_send_message(self, message):
        """在后台线程中发送消息"""
        try:
            # 检查是否有@nickname指令
            message = self.check_for_agent(message)
            if not message:
                return "请输入消息内容"

            # 构建包含历史记录的消息列表
            messages = []
            for msg in self.chat_history:
                messages.append({"role": msg[0], "content": msg[1]})
            messages.append({"role": "user", "content": message})
            
            # 在主线程中创建消息面板
            message_text = None
            def create_panel():
                nonlocal message_text
                message_text = self.create_message_panel("AI")
            wx.CallAfter(create_panel)
            
            # 等待面板创建完成
            time.sleep(0.1)
            
            # 使用流式API
            full_response = ""
            buffer = ""
            last_update = time.time()
            update_interval = 0.1  # 100ms更新一次UI

            # 使用当前agent的model
            current_model = self.config['agents'][self.current_agent]['model']
            
            for chunk in self.client.chat.completions.create(
                model=current_model,
                messages=messages,
                stream=True
            ):
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    buffer += content
                    
                    # 检查是否需要更新UI
                    current_time = time.time()
                    if current_time - last_update >= update_interval:
                        if buffer:
                            def update_text():
                                if message_text:
                                    message_text.SetValue(full_response)
                                    self.update_message_text_size(message_text, full_response)
                            wx.CallAfter(update_text)
                            buffer = ""
                            last_update = current_time
            
            # 确保最后的内容被显示
            if buffer:
                def update_final_text():
                    if message_text:
                        message_text.SetValue(full_response)
                        self.update_message_text_size(message_text, full_response)
                wx.CallAfter(update_final_text)

            return full_response
        except Exception as e:
            return f"错误: {str(e)}"

    def OnSend(self, event):
        message = self.input_text.GetValue().strip()
        if not message:
            return
            
        # 显示用户消息
        self.add_message("User", message)
        self.chat_history.append(("user", message))
        self.input_text.SetValue("")
        
        def on_complete(future):
            """处理异步调用完成"""
            try:
                ai_message = future.result()
                self.chat_history.append(("assistant", ai_message))
                # 将焦点移动到最新的消息文本框
                if self.latest_message_text:
                    wx.CallAfter(self.latest_message_text.SetFocus)
            except Exception as e:
                wx.CallAfter(self.add_message, "System", f"错误: {str(e)}")
        
        # 在线程池中执行API调用
        future = self.thread_pool.submit(self.async_send_message, message)
        future.add_done_callback(on_complete)
            
    def OnNew(self, event):
        """清空历史聊天记录"""
        # 清空历史记录面板中的所有内容
        for child in self.history_panel.GetChildren():
            child.Destroy()
        self.history_sizer.Clear()
        # 清空输入框
        self.input_text.SetValue("")
        # 重置聊天历史为当前agent的system role
        self.chat_history = [
            ("system", self.config['agents'][self.current_agent]['role_system'])
        ]
        # 重置最新消息文本框引用
        self.latest_message_text = None
        # 更新布局
        self.history_panel.Layout()
        self.UpdateLayout()
            
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
        self.history_panel.Layout()
        self.history_panel.FitInside()
        
        # 获取虚拟大小和实际大小
        virtual_size = self.history_panel.GetVirtualSize()
        client_size = self.history_panel.GetClientSize()
        
        # 计算最大滚动位置
        max_scroll = max(0, virtual_size[1] - client_size[1])
        
        # 滚动到底部
        self.history_panel.Scroll(0, max_scroll)
        
        # 强制刷新显示
        self.history_panel.Refresh()

    def OnKeyDown(self, event):
        """处理按键事件"""
        key_code = event.GetKeyCode()
        
        # 处理Enter键
        if key_code == wx.WXK_RETURN:
            if event.ShiftDown():
                # Shift+Enter: 插入换行
                current_pos = self.input_text.GetInsertionPoint()
                current_text = self.input_text.GetValue()
                new_text = current_text[:current_pos] + '\n' + current_text[current_pos:]
                self.input_text.SetValue(new_text)
                self.input_text.SetInsertionPoint(current_pos + 1)
            else:
                # Enter: 发送消息
                self.OnSend(event)
        else:
            event.Skip()
            
    def OnHistoryKeyDown(self, event):
        key = event.GetKeyCode()
        if key == wx.WXK_UP:
            # 向上移动焦点
            pass
        elif key == wx.WXK_DOWN:
            # 向下移动焦点
            pass
        else:
            event.Skip()

    def OnShow(self, event):
        """处理窗口显示事件"""
        if event.IsShown():
            # 设置焦点到输入框
            wx.CallAfter(self.input_text.SetFocus)
        event.Skip()
        
    def OnKeyPress(self, event):
        """处理按键事件"""
        key_code = event.GetKeyCode()
        
        # 处理 ESC 键
        if key_code == wx.WXK_ESCAPE:
            self.minimize_to_tray()
            return
            
        # 处理 Ctrl+N 快捷键
        if event.ControlDown() and key_code == ord('N'):
            self.OnNew(event)
            return
            
        # 处理其他按键
        if event.AltDown():
            if key_code == wx.WXK_F4:  # Alt+F4
                self.minimize_to_tray()
                return
                
        # 处理 X 键关闭按钮
        if key_code == ord('X') and event.AltDown():
            self.minimize_to_tray()
            return
            
        event.Skip()
        
    def InitUI(self):
        # 创建主面板
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 创建菜单栏
        menubar = wx.MenuBar()
        fileMenu = wx.Menu()
        configItem = fileMenu.Append(-1, '配置(&S)')
        agentItem = fileMenu.Append(-1, '添加agent(&A)')
        exitItem = fileMenu.Append(-1, '退出(&X)')
        menubar.Append(fileMenu, '文件(&F)')
        self.SetMenuBar(menubar)
        
        # 消息历史面板 - 使用ScrolledPanel
        self.history_panel = scrolled.ScrolledPanel(panel, style=wx.SUNKEN_BORDER | wx.VSCROLL)
        self.history_sizer = wx.BoxSizer(wx.VERTICAL)
        self.history_panel.SetSizer(self.history_sizer)
        
        # 设置滚动
        self.history_panel.SetupScrolling(scroll_x=False, scroll_y=True, rate_y=20)
        
        # 输入面板 - 固定高度
        self.input_panel = wx.Panel(panel)
        self.input_panel.SetMinSize((-1, 100))  # 固定输入面板高度为100像素
        input_sizer = wx.BoxSizer(wx.VERTICAL)  # 改为垂直布局以容纳标签
        
        # 创建标签和输入框的容器
        input_container = wx.BoxSizer(wx.HORIZONTAL)
        
        # 创建标签
        input_label = wx.StaticText(self.input_panel, -1, "问题输入框 (Enter发送, Shift+Enter换行):")
        
        # 创建输入框
        self.input_text = wx.TextCtrl(self.input_panel, style=wx.TE_MULTILINE)
        
        # 添加标签和输入框到容器
        input_sizer.Add(input_label, 0, wx.EXPAND | wx.BOTTOM, 5)
        
        # 创建按钮面板
        button_panel = wx.Panel(self.input_panel)
        button_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 创建按钮并设置固定大小
        self.send_btn = wx.Button(button_panel, -1, '发送(Enter)')
        new_btn = wx.Button(button_panel, -1, '新建(Ctrl+N)')
        
        # 设置按钮大小一致
        btn_size = wx.Size(100, 35)
        self.send_btn.SetMinSize(btn_size)
        new_btn.SetMinSize(btn_size)
        
        # 添加按钮到按钮布局
        button_sizer.Add(self.send_btn, 0, wx.EXPAND | wx.BOTTOM, 5)
        button_sizer.Add(new_btn, 0, wx.EXPAND)
        button_panel.SetSizer(button_sizer)
        
        # 添加输入框和按钮到水平容器
        input_container.Add(self.input_text, 1, wx.EXPAND | wx.RIGHT, 5)
        input_container.Add(button_panel, 0, wx.ALIGN_CENTER_VERTICAL)
        
        # 添加容器到主输入布局
        input_sizer.Add(input_container, 1, wx.EXPAND)
        
        self.input_panel.SetSizer(input_sizer)
        
        # 设置主布局
        main_sizer.Add(self.history_panel, 1, wx.EXPAND | wx.ALL, 5)  # 历史面板占用所有剩余空间
        main_sizer.Add(self.input_panel, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)  # 输入面板固定在底部
        
        panel.SetSizer(main_sizer)
        
        # 绑定事件
        self.Bind(wx.EVT_MENU, self.OnConfig, configItem)
        self.Bind(wx.EVT_MENU, self.OnAgentConfig, agentItem)
        self.Bind(wx.EVT_MENU, self.force_exit, exitItem)
        self.send_btn.Bind(wx.EVT_BUTTON, self.OnSend)
        new_btn.Bind(wx.EVT_BUTTON, self.OnNew)
        self.input_text.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        self.history_panel.Bind(wx.EVT_KEY_DOWN, self.OnHistoryKeyDown)
        
        # 绑定按键事件
        self.Bind(wx.EVT_CHAR_HOOK, self.OnKeyPress)
        
        # 绑定窗口显示事件
        self.Bind(wx.EVT_SHOW, self.OnShow)
        
        # 强制更新布局
        self.input_panel.Layout()
        self.history_panel.Layout()
        panel.Layout()
        
    def UpdateLayout(self):
        """强制更新所有面板的布局"""
        self.history_panel.Layout()
        self.history_panel.SetupScrolling(scroll_x=False, scroll_y=True, rate_y=20)
        self.history_panel.FitInside()  # 确保内容适应面板大小
        self.Layout()
        
    def OnSize(self, event):
        """处理窗口大小改变事件"""
        event.Skip()
        wx.CallAfter(self.UpdateLayout)
        
    def load_config(self):
        if not os.path.exists('config.json'):
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump({
                    'openai': {
                        'api_key': '',
                        'base_url': 'https://api.openai.com/v1',
                    },
                    'hotkeys': {
                        'show_window': 'alt+z'
                    },
                    'agents': {
                        'default': {
                            'nickname': 'default',
                            'role_system': 'speak in chinese',
                            'model': 'openai/gpt-4-mini'
                        }
                    }
                }, f, indent=4)
        
        with open('config.json', 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        # 初始化OpenAI客户端
        self.client = OpenAI(
            api_key=self.config['openai']['api_key'],
            base_url=self.config['openai']['base_url']
        )

def main():
    app = wx.App()
    frame = ChatFrame()
    frame.Show()
    app.MainLoop()

if __name__ == '__main__':
    main()
