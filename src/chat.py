import wx
from chat_frame import ChatFrame
from logger_manager import LoggerManager

def main():
    # 初始化日志系统
    logger = LoggerManager.get_logger()
    logger.info("=== 程序启动 ===")
    
    try:
        app = wx.App()
        logger.info("wxPython应用程序初始化成功")
        
        frame = ChatFrame()
        frame.Show()
        logger.info("主窗口创建并显示成功")
        
        app.MainLoop()
    except Exception as e:
        logger.error(f"程序运行时发生错误: {str(e)}")
    finally:
        logger.info("=== 程序退出 ===")

if __name__ == '__main__':
    main()
