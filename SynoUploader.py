# coding=utf-8
# !python
import configparser
import os
import zipfile
from threading import Thread

import wx
from wx.lib.pubsub import pub

from synology import filestation, utils


class UploadThread(Thread):
    def __init__(self, data):
        # 线程实例化时立即启动
        Thread.__init__(self)
        self.data = data
        self.start()

    def compressLocalFolder(self):
        wx.CallAfter(pub.sendMessage, "update", msg = '正在压缩本地文件夹')

        zipf = zipfile.ZipFile(self.data['local_file_path'], 'w')
        pre_len = len(os.path.dirname(self.data['local']))
        for parent, dirnames, filenames in os.walk(self.data['local']):
            for filename in filenames:
                pathfile = os.path.join(parent, filename)
                arcname = pathfile[pre_len:].strip(os.path.sep)   # 相对路径
                zipf.write(pathfile, arcname)
        zipf.close()

    def deleteLocalFile(self):
        wx.CallAfter(pub.sendMessage, "update", msg = '正在清除本地临时文件')
        os.remove(self.data['local_file_path'])

    def uploadFile(self):
        wx.CallAfter(pub.sendMessage, "update", msg = '正在登录')
        fs = filestation.FileStation(self.data['host'],
                                     self.data['user'],
                                     self.data['passwd'],
                                     self.data['port'])
        if not fs.logged_in:
            wx.CallAfter(pub.sendMessage, "update", msg = '登录失败')
            wx.CallAfter(pub.sendMessage, "loginErr")
            return

        self.compressLocalFolder()

        wx.CallAfter(pub.sendMessage, "update", msg = '正在上传文件')
        fs.upload(self.data['remote_file_path'], self.data['local_file_path'])

        wx.CallAfter(pub.sendMessage, "update", msg = '正在解压文件')
        task = fs.extract(self.data['remote_file_path'], self.data['remote'])
        taskwait = fs.waitForTaskFinished(task["taskid"])

        if taskwait['success']:
            wx.CallAfter(pub.sendMessage, "update", msg = '正在清除远程临时文件')
            task = fs.delete(self.data['remote_file_path'])
            fs.waitForTaskFinished(task["taskid"], timeout = 30)
        else:
            wx.CallAfter(pub.sendMessage, "update", msg = '解压等待超时')

        self.deleteLocalFile()

    def run(self):
        self.uploadFile()
        wx.CallAfter(pub.sendMessage, "update", msg = '就绪')
        wx.CallAfter(pub.sendMessage, "finish")


class MainFrame(wx.Frame):
    cf = configparser.ConfigParser()
    fn = ''
    local_filename = ''

    def __init__(self):
        wx.Frame.__init__(self, None, -1, "群晖NAS文件夹上传助手", pos = wx.DefaultPosition, size = wx.Size(500, 260))
        self.SetSizeHints(wx.DefaultSize, wx.Size(500, 260))
        panel = wx.Panel(self)
        # 1 创建窗口部件
        self.topLbl = wx.StaticText(panel, -1, "群晖NAS", )
        self.topLbl.SetFont(wx.Font(18, wx.SWISS, wx.NORMAL, wx.BOLD))
        self.statusLbl = wx.StaticText(panel, -1, "就绪", size = (150, -1), style = wx.ALIGN_RIGHT)
        self.statusLbl.SetForegroundColour("Gray")

        hostLbl = wx.StaticText(panel, -1, "服务器:")
        hostLbl.SetForegroundColour("Gray")
        self.host = wx.TextCtrl(panel, -1, "", size = (150, -1));
        portLbl = wx.StaticText(panel, -1, "端口:", size = (50, -1), style = wx.ALIGN_RIGHT)
        portLbl.SetForegroundColour("Gray")
        self.port = wx.TextCtrl(panel, -1, "", size = (70, -1));

        userLbl = wx.StaticText(panel, -1, "用户名:")
        userLbl.SetForegroundColour("Gray")
        self.user = wx.TextCtrl(panel, -1, "");

        passwdLbl = wx.StaticText(panel, -1, "密码:")
        passwdLbl.SetForegroundColour("Gray")
        self.passwd = wx.TextCtrl(panel, -1, "", style = wx.TE_PASSWORD);

        localLbl = wx.StaticText(panel, -1, "本地文件夹:")
        localLbl.SetForegroundColour("Gray")
        self.local = wx.TextCtrl(panel, -1, "", size = (200, -1));
        # state = wx.TextCtrl(panel, -1, "", size=(50,-1));
        localSelect = wx.Button(panel, -1, "选择", size = (70, -1));

        remoteLbl = wx.StaticText(panel, -1, "远程文件夹:")
        remoteLbl.SetForegroundColour("Gray")
        self.remote = wx.TextCtrl(panel, -1, "", size = (200, -1));
        remoteSelect = wx.Button(panel, -1, "选择", size = (70, -1));

        self.submitBtn = wx.Button(panel, -1, "提交")
        cancelBtn = wx.Button(panel, -1, "取消")

        # 2 开始布局
        # 2.1 垂直的sizer-mainSizer位于顶层的管理所有内容
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        topSizer = wx.BoxSizer(wx.HORIZONTAL)
        topSizer.Add(self.topLbl, 1, wx.TOP | wx.LEFT, 10)
        topSizer.Add(self.statusLbl, 0, wx.TOP | wx.RIGHT, 13)
        mainSizer.Add(topSizer, 0, wx.EXPAND, 5)
        # mainSizer.Add(self.topLbl, 0, wx.ALL, 5)
        mainSizer.Add(wx.StaticLine(panel), 0, wx.EXPAND | wx.TOP | wx.BOTTOM, 5)

        # addrSizer is a grid that holds all of the address info
        # 2.2 表格Sizer-配置项Sizer管理所有的配置项
        configSizer = wx.FlexGridSizer(cols = 2, hgap = 5, vgap = 5)
        configSizer.AddGrowableCol(1)

        # 2.3 水平嵌套-服务器与端口
        configSizer.Add(hostLbl, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        hostSizer = wx.BoxSizer(wx.HORIZONTAL)
        hostSizer.Add(self.host, 1)
        hostSizer.Add(portLbl)
        hostSizer.Add(self.port)
        configSizer.Add(hostSizer, 0, wx.EXPAND)

        # 2.4 用户名
        configSizer.Add(userLbl, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        configSizer.Add(self.user, 0, wx.EXPAND)

        # 2.5 密码
        configSizer.Add(passwdLbl, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        configSizer.Add(self.passwd, 0, wx.EXPAND)

        # 2.6 水平嵌套-本地文件夹
        configSizer.Add(localLbl, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        localSizer = wx.BoxSizer(wx.HORIZONTAL)
        localSizer.Add(self.local, 1)
        localSizer.Add(localSelect)
        configSizer.Add(localSizer, 0, wx.EXPAND)

        # 2.7 水平嵌套-远程文件夹
        configSizer.Add(remoteLbl, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        remoteSizer = wx.BoxSizer(wx.HORIZONTAL)
        remoteSizer.Add(self.remote, 1)
        remoteSizer.Add(remoteSelect)
        configSizer.Add(remoteSizer, 0, wx.EXPAND)

        # 2.8 添加configSizer
        mainSizer.Add(configSizer, 0, wx.EXPAND | wx.ALL, 10)
        mainSizer.Add(wx.StaticLine(panel), 0, wx.EXPAND | wx.TOP | wx.BOTTOM, 5)

        # 2.9 按钮sizer在一个可变宽度的行中显示，按钮每一边都有可变空间
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        btnSizer.Add((20, 20), 1)
        btnSizer.Add(self.submitBtn)
        btnSizer.Add((20, 20), 1)
        btnSizer.Add(cancelBtn)
        btnSizer.Add((20, 20), 1)
        mainSizer.Add(btnSizer, 0, wx.EXPAND | wx.BOTTOM, 10)

        panel.SetSizer(mainSizer)

        # 3 绑定事件
        self.Bind(wx.EVT_SHOW, self.OnShow)
        self.host.Bind(wx.EVT_TEXT, self.OnServerOrPortText)
        self.port.Bind(wx.EVT_TEXT, self.OnServerOrPortText)
        self.submitBtn.Bind(wx.EVT_BUTTON, self.OnSubmit)
        self.Bind(wx.EVT_BUTTON, self.OnClose, cancelBtn)
        self.Bind(wx.EVT_BUTTON, self.OnLocalSelect, localSelect)
        self.Bind(wx.EVT_BUTTON, self.OnRemoteSelect, remoteSelect)

        pub.subscribe(self.updateStatus, "update")
        pub.subscribe(self.activeSubmit, "finish")
        pub.subscribe(self.LoginAlert, "loginErr")

    def writeConf(self):
        try:
            self.cf.set("server", "host", self.host.GetValue())
            self.cf.set("server", "port", self.port.GetValue())
            self.cf.set("server", "user", self.user.GetValue())
            self.cf.set("server", "passwd", self.passwd.GetValue())
            self.cf.set("path", "local", self.local.GetValue())
            self.cf.set("path", "remote", self.remote.GetValue())
            self.cf.set("path", "filename", self.fn)
            self.cf.write(open("setting.cfg", "w"))
        except:
            pass

    def readConf(self):
        try:
            self.cf.read("setting.cfg")
            self.host.SetValue(self.cf.get("server", "host"))
            self.port.SetValue(self.cf.get("server", "port"))
            self.user.SetValue(self.cf.get("server", "user"))
            self.passwd.SetValue(self.cf.get("server", "passwd"))
            self.local.SetValue(self.cf.get("path", "local"))
            self.remote.SetValue(self.cf.get("path", "remote"))
        except:
            pass

    def OnShow(self, e):
        self.readConf()

    def OnSubmit(self, e):
        self.fn = 'syno_uploader_' + utils.generate_key(8, True, False, False)
        self.writeConf()
        data = {
            'host': self.host.GetValue(),
            'port': self.port.GetValue(),
            'user': self.user.GetValue(),
            'passwd': self.passwd.GetValue(),
            'local': self.local.GetValue(),
            'remote': self.remote.GetValue(),
            'filename': self.fn,
            'local_file_path': '%s/%s.zip' % (os.path.dirname(self.local.GetValue()), self.fn),
            'remote_file_path': '%s/%s.zip' % (self.remote.GetValue(), self.fn)
        }
        UploadThread(data)
        self.statusLbl.SetLabel('开始执行')
        e.GetEventObject().Disable()

    def OnClose(self, e):
        self.Close(True)
        self.Destroy()

    def OnServerOrPortText(self, e):
        self.topLbl.SetLabelText('群晖NAS:%s%s%s' % (self.host.GetValue(),
                                                   ':' if self.port.GetValue() != '' else '',
                                                   self.port.GetValue()))

    def OnLocalSelect(self, e):
        dlg = wx.DirDialog(self, u"选择文件夹", style = wx.DD_DEFAULT_STYLE)
        if dlg.ShowModal() == wx.ID_OK:
            self.local.SetValue(dlg.GetPath())
            self.local.SetFocus()
        dlg.Destroy()

    def OnRemoteSelect(self, e):
        fs = filestation.FileStation(self.host.GetValue(),
                                     self.user.GetValue(),
                                     self.passwd.GetValue(),
                                     self.port.GetValue())
        if fs.logged_in:
            dlg = NASDialog(fs)
            if dlg.ShowModal() == wx.ID_OK:
                self.remote.SetValue(dlg.GetPath())
                self.remote.SetFocus()
            else:
                if not dlg.HasLogged():
                    self.LoginAlert()
            dlg.Destroy()
        else:
            self.LoginAlert()

    def updateStatus(self, msg):
        self.statusLbl.SetLabel(msg)

    def activeSubmit(self):
        self.submitBtn.Enable(True)

    def LoginAlert(self):
        msg = wx.MessageDialog(None, "未能成功登录群晖NAS,请检查配置项是否输入错误！",
                               '登录失败',
                               wx.OK | wx.ICON_WARNING)
        msg.ShowModal()
        self.submitBtn.Enable(True)


class NASDialog(wx.Dialog):
    def __init__(self, filestation):
        wx.Dialog.__init__(self, None, title = "远程文件夹选择", size = (400, 500))
        self.fs = filestation
        panel = wx.Panel(self)

        mainSizer = wx.BoxSizer(wx.VERTICAL)

        self.tree = wx.TreeCtrl(panel, size = (-1, 460), style = wx.TR_DEFAULT_STYLE | wx.SIMPLE_BORDER)
        treeSizer = wx.BoxSizer(wx.VERTICAL)
        treeSizer.Add(self.tree, 0, wx.EXPAND, 5)

        il = wx.ImageList(16, 16)

        root_icon = wx.Icon('icons/nas.png', wx.BITMAP_TYPE_PNG, 16, 16)
        forder_icon = wx.Icon('icons/folder.png', wx.BITMAP_TYPE_PNG, 16, 16)
        shareforder_icon = wx.Icon('icons/sharefolder.png', wx.BITMAP_TYPE_PNG, 16, 16)

        self.rootidx = il.Add(root_icon)
        self.fldridx = il.Add(forder_icon)
        self.sharefldridx = il.Add(shareforder_icon)

        self.tree.AssignImageList(il)

        panel.SetSizer(treeSizer)

        btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        okBtn = wx.Button(self, label = '确定')
        cancelBtn = wx.Button(self, label = '取消')
        okBtn.SetId(wx.ID_OK)
        cancelBtn.SetId(wx.ID_CANCEL)
        btnSizer.Add(okBtn)
        btnSizer.Add(cancelBtn, flag = wx.LEFT, border = 5)

        mainSizer.Add(panel, proportion = 1,
                      flag = wx.ALL | wx.EXPAND, border = 5)
        mainSizer.Add(btnSizer,
                      flag = wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, border = 10)

        self.SetSizer(mainSizer)

        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnSelChanged, self.tree)

        self.GetShareFolder()

    def AddTreeNodes(self, parentItem, items):
        """
 Recursively traverses the data structure, adding tree nodes to
 match it.
 """
        children = self.GetTreeChildren(parentItem)
        for item in items:
            if type(item) == str:
                if item not in children:
                    newItem = self.tree.AppendItem(parentItem, item)
                    if self.tree.GetRootItem() == parentItem:
                        self.tree.SetItemImage(newItem, self.sharefldridx,
                                               wx.TreeItemIcon_Normal)
                    else:
                        self.tree.SetItemImage(newItem, self.fldridx,
                                               wx.TreeItemIcon_Normal)

        if self.tree.GetChildrenCount(parentItem) > 0:
            self.tree.Expand(parentItem)

    def GetTreeChildren(self, item):
        pieces = []
        (child, cookie) = self.tree.GetFirstChild(item)
        while child.IsOk():
            piece = self.tree.GetItemText(child)
            pieces.insert(0, piece)
            (child, cookie) = self.tree.GetNextChild(item, cookie)
        return pieces

    def GetItemText(self, item):
        if item:
            return self.tree.GetItemText(item)
        else:
            return ""

    def GetItemPath(self, item):
        if item:
            pieces = []

            while self.tree.GetItemParent(item):
                piece = self.tree.GetItemText(item)
                pieces.insert(0, piece)
                item = self.tree.GetItemParent(item)
            return '/' + '/'.join(pieces)
        else:
            return ""

    def GetPath(self):
        return self.GetItemPath(self.tree.GetSelection())

    def GetShareFolder(self):
        shareFolders = self.fs.list_share()

        root = self.tree.AddRoot('群晖NAS[%s%s%s]' % (self.fs.host,
                                                    ':' if self.fs.port != '' else '',
                                                    self.fs.port))
        self.tree.SetItemImage(root, self.rootidx,
                               wx.TreeItemIcon_Normal)

        self.AddTreeNodes(root, [f['name'] for f in shareFolders['shares']])
        self.tree.Expand(root)
        self.tree.SetFocus()

    def HasLogged(self):
        return self.fs.logged_in

    def OnSelChanged(self, e):
        folders = self.fs.list(self.GetItemPath(e.GetItem()), filetype = 'dir')
        self.AddTreeNodes(e.GetItem(), [f['name'] for f in folders['files']])


    def OnClose(self, e):
        self.Close(True)


app = wx.App()
MainFrame().Show()
app.MainLoop()