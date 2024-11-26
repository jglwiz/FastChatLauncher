import keyboard
import time

class HotkeyManager:
    def __init__(self, config, callback):
        self.config = config
        self.callback = callback
        
    def setup_global_hotkey(self):
        """设置全局热键"""
        max_retries = 10  # 最大重试次数
        retry_delay = 2   # 每次重试间隔秒数
        
        for attempt in range(max_retries):
            try:
                # 先移除所有已存在的热键
                keyboard.unhook_all()
                # 添加新的热键
                keyboard.add_hotkey(self.config['hotkeys']['show_window'], self.callback, suppress=True)
                print(f"全局热键注册成功,尝试次数: {attempt + 1}")
                return
            except Exception as e:
                print(f"设置全局热键失败 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:  # 如果不是最后一次尝试
                    time.sleep(retry_delay)     # 等待一段时间后重试
                else:
                    print("全局热键注册失败,已达到最大重试次数")
                    
    def cleanup(self):
        """清理热键绑定"""
        try:
            keyboard.unhook_all()
        except:
            pass
