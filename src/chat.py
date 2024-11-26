import wx
from chat_frame import ChatFrame

def main():
    app = wx.App()
    frame = ChatFrame()
    frame.Show()
    app.MainLoop()

if __name__ == '__main__':
    main()
