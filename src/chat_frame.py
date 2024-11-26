import wx
import json
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from config_manager import ConfigManager
from hotkey_manager import HotkeyManager
from chat_client import ChatClient
from message_panel import MessagePanel
from ui import ChatTrayIcon, ConfigDialog, AgentConfigDialog

class ChatFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="Quick Chat Launcher", size=(400, 600),
                        style=wx.DEFAULT_FRAME_STYLE)
        
        # 初始化配置管理器
        self.config_manager = ConfigManager()
        self.config = self.config_manager.get_config()
        
        # 初始化UI
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
        
        # 初始化热键管理器
        self.hotkey_manager = HotkeyManager(self.config, self.safe_toggle_window)
        self.hotkey_manager.setup_global_hotkey()
        
        # 初始化聊天客户端
        self.chat_client = ChatClient(self.config_manager.get_client())
        
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
        self.hotkey_manager.cleanup()
        self.tray_icon.Destroy()
        self.Destroy()
        wx.GetApp().ExitMainLoop()
        
    def OnConfig(self, event):
        dlg = ConfigDialog(self, self.config)
        if dlg.ShowModal() == wx.ID_OK:
            self.config = self.config_manager.get_config()
            # 重新设置全局热键
            self.hotkey_manager.setup_global_hotkey()
        dlg.Destroy()

    def OnAgentConfig(self, event):
        dlg = AgentConfigDialog(self, self.config)
        if dlg.ShowModal() == wx.ID_OK:
            self.config = self.config_manager.get_config()
            # 重置聊天历史为当前agent的system role
            self.chat_history = [
                ("system", self.config['agents'][self.current_agent]['role_system'])
            ]
        dlg.Destroy()
        
    def OnClose(self, event):
        self.minimize_to_tray()

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
                message_text = self.history_panel.create_message_panel("AI")
            wx.CallAfter(create_panel)
            
            # 等待面板创建完成
            import time
            time.sleep(0.1)
            
            # 使用当前agent的model
            current_model = self.config['agents'][self.current_agent]['model']
            
            # 获取聊天完成结果
            response = self.chat_client.get_chat_completion(messages, current_model)
            
            # 处理响应
            def update_message(text):
                if message_text:
                    wx.CallAfter(message_text.SetValue, text)
                    wx.CallAfter(self.history_panel.update_message_text_size, message_text, text)
                    
            full_response = self.chat_client.process_stream_response(response, update_message)
            return full_response
            
        except Exception as e:
            return f"错误: {str(e)}"

    def OnSend(self, event):
        message = self.input_text.GetValue().strip()
        if not message:
            return
            
        # 显示用户消息
        self.history_panel.add_message("User", message)
        self.chat_history.append(("user", message))
        self.input_text.SetValue("")
        
        def on_complete(future):
            """处理异步调用完成"""
            try:
                ai_message = future.result()
                self.chat_history.append(("assistant", ai_message))
                # 将焦点移动到最新的消息文本框
                if self.history_panel.latest_message_text:
                    wx.CallAfter(self.history_panel.latest_message_text.SetFocus)
            except Exception as e:
                wx.CallAfter(self.history_panel.add_message, "System", f"错误: {str(e)}")
        
        # 在线程池中执行API调用
        future = self.thread_pool.submit(self.async_send_message, message)
        future.add_done_callback(on_complete)
            
    def OnNew(self, event):
        """清空历史聊天记录"""
        self.history_panel.clear_history()
        # 清空输入框
        self.input_text.SetValue("")
        # 重置聊天历史为当前agent的system role
        self.chat_history = [
            ("system", self.config['agents'][self.current_agent]['role_system'])
        ]
        # 更新布局
        self.UpdateLayout()
            
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
        
        # 消息历史面板
        self.history_panel = MessagePanel(panel)
        
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
