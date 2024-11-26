import wx
import json
from wx.adv import TaskBarIcon
import wx.lib.scrolledpanel as scrolled


class AgentConfigDialog(wx.Dialog):
    def __init__(self, parent, config):
        super().__init__(parent, title="Agent配置", size=(600, 500))
        self.config = config
        if 'agents' not in self.config:
            self.config['agents'] = {
                'default': {
                    'nickname': 'default',
                    'role_system': 'speak in chinese',
                    'model': 'openai/gpt-4o-mini'
                }
            }
        self.InitUI()
        
    def InitUI(self):
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        # Agents列表
        list_box = wx.StaticBox(panel, label="已配置的Agents")
        list_sizer = wx.StaticBoxSizer(list_box, wx.VERTICAL)
        
        self.agents_list = wx.ListCtrl(panel, style=wx.LC_REPORT)
        self.agents_list.InsertColumn(0, "昵称", width=100)
        self.agents_list.InsertColumn(1, "系统角色", width=200)
        self.agents_list.InsertColumn(2, "模型", width=150)
        
        list_sizer.Add(self.agents_list, 1, wx.EXPAND|wx.ALL, 5)
        
        # 编辑区域
        edit_box = wx.StaticBox(panel, label="编辑Agent")
        edit_sizer = wx.StaticBoxSizer(edit_box, wx.VERTICAL)
        
        # 昵称输入
        nickname_sizer = wx.BoxSizer(wx.HORIZONTAL)
        nickname_sizer.Add(wx.StaticText(panel, label="昵称:"), 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
        self.nickname_input = wx.TextCtrl(panel)
        nickname_sizer.Add(self.nickname_input, 1)
        
        # 系统角色输入
        role_sizer = wx.BoxSizer(wx.HORIZONTAL)
        role_sizer.Add(wx.StaticText(panel, label="系统角色:"), 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
        self.role_input = wx.TextCtrl(panel)
        role_sizer.Add(self.role_input, 1)
        
        # 模型输入
        model_sizer = wx.BoxSizer(wx.HORIZONTAL)
        model_sizer.Add(wx.StaticText(panel, label="模型:"), 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
        self.model_input = wx.TextCtrl(panel)
        model_sizer.Add(self.model_input, 1)
        
        # 按钮区域
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.add_button = wx.Button(panel, label="添加(&A)")
        self.update_button = wx.Button(panel, label="更新(&U)")
        self.delete_button = wx.Button(panel, label="删除(&D)")
        self.update_button.Disable()  # 初始禁用更新按钮
        self.delete_button.Disable()  # 初始禁用删除按钮
        
        button_sizer.Add(self.add_button, 0, wx.RIGHT, 5)
        button_sizer.Add(self.update_button, 0, wx.RIGHT, 5)
        button_sizer.Add(self.delete_button, 0)
        
        # 将所有元素添加到edit_sizer
        edit_sizer.Add(nickname_sizer, 0, wx.EXPAND|wx.ALL, 5)
        edit_sizer.Add(role_sizer, 0, wx.EXPAND|wx.ALL, 5)
        edit_sizer.Add(model_sizer, 0, wx.EXPAND|wx.ALL, 5)
        edit_sizer.Add(button_sizer, 0, wx.ALIGN_RIGHT|wx.ALL, 5)
        
        # 底部按钮
        bottom_sizer = wx.BoxSizer(wx.HORIZONTAL)
        save_btn = wx.Button(panel, wx.ID_OK, "保存(&S)")
        cancel_btn = wx.Button(panel, wx.ID_CANCEL, "取消")
        bottom_sizer.Add(save_btn)
        bottom_sizer.Add(cancel_btn, 0, wx.LEFT, 5)
        
        # 主布局
        vbox.Add(list_sizer, 1, wx.EXPAND|wx.ALL, 5)
        vbox.Add(edit_sizer, 0, wx.EXPAND|wx.ALL, 5)
        vbox.Add(bottom_sizer, 0, wx.ALIGN_RIGHT|wx.ALL, 5)
        
        panel.SetSizer(vbox)
        
        # 加载现有agents
        self.load_agents()
        
        # 绑定事件
        self.add_button.Bind(wx.EVT_BUTTON, self.OnAdd)
        self.update_button.Bind(wx.EVT_BUTTON, self.OnUpdate)
        self.delete_button.Bind(wx.EVT_BUTTON, self.OnDelete)
        save_btn.Bind(wx.EVT_BUTTON, self.OnSave)
        self.agents_list.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected)
        
    def load_agents(self):
        """加载现有agents到列表"""
        self.agents_list.DeleteAllItems()
        
        for nickname, agent in self.config['agents'].items():
            index = self.agents_list.GetItemCount()
            self.agents_list.InsertItem(index, agent['nickname'])
            self.agents_list.SetItem(index, 1, agent['role_system'])
            self.agents_list.SetItem(index, 2, agent['model'])
                
    def OnItemSelected(self, event):
        """处理列表项选择事件"""
        index = event.GetIndex()
        nickname = self.agents_list.GetItem(index, 0).GetText()
        agent = self.config['agents'][nickname]
        
        self.nickname_input.SetValue(agent['nickname'])
        self.role_input.SetValue(agent['role_system'])
        self.model_input.SetValue(agent['model'])
        
        # 如果是default agent，禁用昵称输入和删除按钮
        is_default = nickname == 'default'
        self.nickname_input.Enable(not is_default)
        self.delete_button.Enable(not is_default)
        
        # 启用更新按钮
        self.update_button.Enable()
                
    def OnAdd(self, event):
        """添加新agent"""
        nickname = self.nickname_input.GetValue().strip()
        role = self.role_input.GetValue().strip()
        model = self.model_input.GetValue().strip()
        
        if not nickname or not role or not model:
            wx.MessageBox("所有字段都必须填写", "错误", wx.OK | wx.ICON_ERROR)
            return
            
        if nickname in self.config['agents']:
            wx.MessageBox("该昵称已存在", "错误", wx.OK | wx.ICON_ERROR)
            return
            
        self.config['agents'][nickname] = {
            'nickname': nickname,
            'role_system': role,
            'model': model
        }
        
        # 清空输入框
        self.clear_inputs()
        
        # 重新加载列表
        self.load_agents()
        
    def OnUpdate(self, event):
        """更新现有agent"""
        nickname = self.nickname_input.GetValue().strip()
        role = self.role_input.GetValue().strip()
        model = self.model_input.GetValue().strip()
        
        if not nickname or not role or not model:
            wx.MessageBox("所有字段都必须填写", "错误", wx.OK | wx.ICON_ERROR)
            return
            
        # 更新agent
        self.config['agents'][nickname].update({
            'role_system': role,
            'model': model
        })
        
        # 清空输入框并重置按钮状态
        self.clear_inputs()
        
        # 重新加载列表
        self.load_agents()

    def OnDelete(self, event):
        """删除当前选中的agent"""
        nickname = self.nickname_input.GetValue().strip()
        
        if nickname == 'default':
            wx.MessageBox("不能删除default agent", "错误", wx.OK | wx.ICON_ERROR)
            return
            
        if nickname in self.config['agents']:
            if wx.MessageBox(f"确定要删除agent '{nickname}'吗？", 
                           "确认删除", 
                           wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION) == wx.YES:
                del self.config['agents'][nickname]
                self.clear_inputs()
                self.load_agents()
        
    def clear_inputs(self):
        """清空输入框并重置按钮状态"""
        self.nickname_input.SetValue("")
        self.role_input.SetValue("")
        self.model_input.SetValue("")
        self.nickname_input.Enable(True)
        self.add_button.Enable()
        self.update_button.Disable()
        self.delete_button.Disable()
        
    def OnSave(self, event):
        """保存所有更改"""
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4)
        self.EndModal(wx.ID_OK)


class ConfigDialog(wx.Dialog):
    def __init__(self, parent, config):
        super().__init__(parent, title="配置", size=(400, 500))
        self.config = config
        self.InitUI()
        
    def InitUI(self):
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        # OpenAI设置
        wx.StaticBox(panel, -1, 'OpenAI设置', pos=(5, 5), size=(380, 150))
        wx.StaticText(panel, -1, 'API Key:', pos=(15, 30))
        self.api_key = wx.TextCtrl(panel, -1, self.config['openai']['api_key'], pos=(15, 50), size=(360, -1))
        
        wx.StaticText(panel, -1, 'Base URL:', pos=(15, 80))
        self.base_url = wx.TextCtrl(panel, -1, self.config['openai']['base_url'], pos=(15, 100), size=(360, -1))
        
        # 热键设置
        wx.StaticBox(panel, -1, '热键设置', pos=(5, 170), size=(380, 80))
        wx.StaticText(panel, -1, '显示窗口:', pos=(15, 195))
        self.hotkey = wx.TextCtrl(panel, -1, self.config['hotkeys']['show_window'], pos=(15, 215), size=(360, -1))
        
        # 按钮
        save_btn = wx.Button(panel, -1, '保存(&S)', pos=(200, 260))
        cancel_btn = wx.Button(panel, -1, '取消', pos=(300, 260))
        
        save_btn.Bind(wx.EVT_BUTTON, self.OnSave)
        cancel_btn.Bind(wx.EVT_BUTTON, self.OnCancel)
        
        # 绑定ESC键事件
        self.Bind(wx.EVT_CHAR_HOOK, self.OnKeyDown)

    def OnKeyDown(self, event):
        """处理键盘事件"""
        if event.GetKeyCode() == wx.WXK_ESCAPE:
            self.EndModal(wx.ID_CANCEL)
        else:
            event.Skip()

    def OnSave(self, event):
        self.config['openai']['api_key'] = self.api_key.GetValue()
        self.config['openai']['base_url'] = self.base_url.GetValue()
        self.config['hotkeys']['show_window'] = self.hotkey.GetValue()
        
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4)
        
        self.EndModal(wx.ID_OK)
    
    def OnCancel(self, event):
        self.EndModal(wx.ID_CANCEL)

class ChatTrayIcon(TaskBarIcon):
    def __init__(self, frame):
        super().__init__()
        self.frame = frame
        self.SetIcon(wx.Icon('icon.png', wx.BITMAP_TYPE_PNG), 'LLM Chat')
        
    def CreatePopupMenu(self):
        menu = wx.Menu()
        show_item = menu.Append(-1, '显示')
        exit_item = menu.Append(-1, '退出')
        
        self.Bind(wx.EVT_MENU, self.OnShow, show_item)
        self.Bind(wx.EVT_MENU, self.OnExit, exit_item)
        return menu
    
    def OnShow(self, event):
        self.frame.show_window()
        
    def OnExit(self, event):
        self.frame.force_exit(event)
