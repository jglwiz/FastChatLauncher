# 无障碍大模型聊天工具

这是一个专门为无障碍需求设计的大模型聊天工具，让所有用户都能便捷地使用AI聊天功能。

## ✨ 特点

### 1. 无障碍设计
- 完全支持屏幕阅读器
- 清晰的界面布局
- 高对比度显示
- 适配各种辅助技术

### 2. 全键盘操作支持
- 所有功能都可通过键盘完成
- 快捷键操作便捷高效
- 无需依赖鼠标操作
- 清晰的键盘焦点提示

### 3. 简单易用
- 界面简洁直观
- 操作流程清晰
- 即开即用，无需复杂设置
- 支持多种对话模式

### 4. 灵活配置
- 支持通过菜单栏图形界面配置
  - OpenAI API设置
  - 全局热键设置
  - Agent角色配置
- 支持JSON配置文件
  - 配置文件位置：`config.json`
  - 可直接编辑修改配置

## 🚀 安装说明

1. 确保您的系统已安装Python 3.11或更高版本
2. 下载本项目的最新发布版本
3. 安装依赖包：
```bash
pip install -r requirements.txt
```

## 📖 使用方法

1. 运行主程序：
```bash
python src/chat.py
```

2. 常用快捷键：
- `Ctrl + N`: 新建对话
- `Enter`: 发送消息
- `Tab`: 在各个元素间切换焦点

3. 配置说明：
- 通过菜单栏配置
  1. 点击"文件" -> "配置"可设置OpenAI API和全局热键
  2. 点击"文件" -> "添加agent"可配置不同的对话角色
- 通过JSON配置
  1. 直接编辑`config.json`文件
  2. 配置文件结构：
```json
{
    "openai": {
        "api_key": "你的OpenAI API密钥",
        "base_url": "https://api.openai.com/v1"
    },
    "hotkeys": {
        "show_window": "alt+z"
    },
    "agents": {
        "default": {
            "nickname": "default",
            "role_system": "speak in chinese",
            "model": "openai/gpt-4-mini"
        }
    }
}
```

## 🛠️ 系统要求

- 操作系统：Windows 10及以上
- Python版本：3.11+
- 内存：4GB及以上
- 硬盘空间：100MB以上

## 其他

这是一次尝试, 如何利用大模型低成本的开发日常应用. 大部分程序的代码都是由cline+claude sonnet 3.5完成. 
用户完全可以配置相似的开发环境, 快速增减功能, 实现定制. 
在开发的过程中, 简易step by step, 然后测试. 大模型基本上能完成绝大部分工作了. 
偶尔回遇到大模型反复修改代码都有bug的情况, 这时候才需要人工接入.

# English Version

# Accessible Large Language Model Chat Tool

This is a large language model chat tool specifically designed for accessibility, allowing all users to conveniently use the AI chat functionality.

## ✨ Features

### 1. Accessible Design
- Full support for screen readers
- Clear interface layout
- High contrast display
- Compatibility with various assistive technologies

### 2. Full Keyboard Support
- All functionalities can be accessed via keyboard
- Convenient and efficient keyboard shortcuts
- No reliance on mouse operation
- Clear keyboard focus indicators

### 3. Simple and Easy to Use
- Intuitive and straightforward interface
- Clear usage flow
- Plug-and-play, no complex setup required
- Support for multiple conversation modes

### 4. Flexible Configuration
- Supports configuration through the graphical menu bar
  - OpenAI API settings
  - Global hotkey settings
  - Agent role configuration
- Supports JSON configuration file
  - Configuration file location: `config.json`
  - Can be directly edited to modify the configuration

## 🚀 Installation Instructions

1. Ensure your system has Python 3.11 or a higher version installed
2. Download the latest release of this project
3. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## 📖 Usage Instructions

1. Run the main program:
```bash
python src/chat.py
```

2. Common Shortcuts:
- `Ctrl + N`: Create a new conversation
- `Enter`: Send a message
- `Tab`: Switch focus between different elements

3. Configuration Guide:
- Through the menu bar
  1. Click "File" -> "Configuration" to set the OpenAI API and global hotkeys
  2. Click "File" -> "Add Agent" to configure different conversation roles
- Through the JSON configuration
  1. Directly edit the `config.json` file
  2. Configuration file structure:
```json
{
    "openai": {
        "api_key": "Your OpenAI API key",
        "base_url": "https://api.openai.com/v1"
    },
    "hotkeys": {
        "show_window": "alt+z"
    },
    "agents": {
        "default": {
            "nickname": "default",
            "role_system": "speak in chinese",
            "model": "openai/gpt-4-mini"
        }
    }
}
```

## 🛠️ System Requirements

- Operating System: Windows 10 or later
- Python Version: 3.11+
- Memory: 4GB or more
- Disk Space: 100MB or more
