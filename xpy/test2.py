
import wx
def GetImage(path, larg=None, haut=None,qual = wx.IMAGE_QUALITY_HIGH):
    # reçoit le pointeur d'une image bitmap et la renvoie scalée
    imageBmp = wx.Bitmap(path)
    imageWx = imageBmp.ConvertToImage()
    if larg and haut:
        imageWx = imageWx.Scale(larg, haut, qual)
    return wx.Bitmap(imageWx)

class Panel(wx.Panel):
    def __init__(self, parent, path):
        super(Panel, self).__init__(parent, -1)
        imageBmp = GetImage(path, 80, 40)
        control = wx.StaticBitmap(self, -1, imageBmp)
        control.SetPosition((10, 10))

if __name__ == '__main__':
    import os
    os.chdir("..")
    app =wx.App()
    frame = wx.Frame(None, -1, 'Scaled Image')
    panel = Panel(frame, "xpy/Images/80x80/Entree.png")
    frame.Show()
    app.MainLoop()