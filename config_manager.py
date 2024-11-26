import json
import os
from openai import OpenAI

class ConfigManager:
    def __init__(self):
        self.config = self.load_config()
        self.client = self.init_openai_client()
        
    def load_config(self):
        """加载配置文件,如果不存在则创建默认配置"""
        if not os.path.exists('config.json'):
            default_config = {
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
            }
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=4)
            return default_config
            
        with open('config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
            
    def init_openai_client(self):
        """初始化OpenAI客户端"""
        return OpenAI(
            api_key=self.config['openai']['api_key'],
            base_url=self.config['openai']['base_url']
        )
        
    def save_config(self):
        """保存配置到文件"""
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4)
            
    def get_config(self):
        """获取当前配置"""
        return self.config
        
    def get_client(self):
        """获取OpenAI客户端"""
        return self.client
        
    def update_config(self, new_config):
        """更新配置"""
        self.config = new_config
        self.client = self.init_openai_client()
        self.save_config()
