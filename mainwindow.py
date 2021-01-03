# -*- coding: utf-8 -*-

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtPrintSupport import *

import webbrowser
import os
import sys
from Graph import Graph
from Component import *
from Config import *


class MainWindow(QMainWindow):
    """Main Window

    Show the main window for app

    Signals:
        addNote: (int, int, str) -> (pos_x, pos_y, note_text)
        addLink: (int, int, str) -> (pos_x, pos_y, link_text)
        close_signal: MainWindow close signal
    """
    # 自定义信号槽
    addNote = pyqtSignal(int, int, str)
    addLink = pyqtSignal(int, int, str)
    close_signal = pyqtSignal()

    def __init__(self, settings):
        super().__init__()
        # self.path = None
        self.root = QFileInfo(__file__).absolutePath()
        self.m_contentChanged = False
        self.m_filename = None
        self.m_undoStack = None
        self.m_dockShow = True
        self.m_settings = settings
        self.timer = QTimer()
        self.timer.timeout.connect(self.file_autoSave)

        self.setWindowIcon(QIcon(self.root + '/images/PyMindIcon.png'))
        print(self.root)

        # ReWrite QGraphicsScene
        self.scene = Graph()
        self.scene.contentChanged.connect(self.contentChanged)
        self.scene.nodeNumChange.connect(self.nodeNumChange)
        self.scene.messageShow.connect(self.messageShow)

        self.view = QGraphicsView()
        self.view.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.view.setDragMode(QGraphicsView.RubberBandDrag)  # 设置拖拽模式
        self.view.setRenderHints(QPainter.Antialiasing |  # 抗锯齿
                                 QPainter.HighQualityAntialiasing |  # 高品质抗锯齿
                                 QPainter.TextAntialiasing |  # 文字抗锯齿
                                 QPainter.SmoothPixmapTransform |  # 使图元变换更加平滑
                                 QPainter.LosslessImageRendering)  # 不失真的图片渲染
        self.view.setScene(self.scene)

        self.setCentralWidget(self.view)
        self.view.show()

        self.setUpDockWidget()  # 热键帮助
        self.setUpMenuBar()  # MenuBar
        self.setUpToolBar()  # 工具ToolBar
        self.setUpStatusBar()  # StatusBar
        self.setUpIconToolBar()  # 图标toolBar
        self.update_title()
        self.setStyleSheet('''QMainWindow{background: LightGray;}''')
        self.resize(1600, 900)
        self.center()
        self.show()

    # 居中显示
    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def update_title(self):
        self.setWindowTitle('%s' % (os.path.basename(self.m_filename) if self.m_filename else '未命名'))
        print('(os.path.basename(self.m_filename) %s' % (os.path.basename(self.m_filename) if self.m_filename else '未命名'))

    # 热键帮助
    def setUpDockWidget(self):
        self.dock = QDockWidget('快捷键', self)
        self.dock.setAllowedAreas(Qt.RightDockWidgetArea)
        hotkeyList = QListWidget(self)
        hotkeyList.addItems(['Shift + Tab 增加同级', 'Tab 增加子级', '---' * 13,
                             'Ctrl + N 新文件', 'Ctrl + S 保存文件', 'Ctrl + Shift + S 另存为', '---' * 13,
                             'Ctrl + X 剪切', 'Ctrl + C 复制', 'Ctrl + V 粘贴', '---' * 13
                             ])
        self.dock.setWidget(hotkeyList)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock)
        self.dock.hide()

    # MenuBar
    def setUpMenuBar(self):
        self.m_undoStack = QUndoStack(self)

        # file menu
        file_menu = self.menuBar().addMenu('文件')

        # new file
        new_file_action = QAction('新文件', self)
        new_file_action.setShortcut('Ctrl+N')
        new_file_action.triggered.connect(self.file_new)
        file_menu.addAction(new_file_action)

        # open file
        open_file_action = QAction('打开', self)
        open_file_action.setShortcut('Ctrl+O')
        open_file_action.triggered.connect(self.file_open)
        file_menu.addAction(open_file_action)

        file_menu.addSeparator()

        # last open file
        self.last_open_file_menu = QMenu('最近打开', self)
        self.file_last_open()
        # TODO: function bind with action
        file_menu.addMenu(self.last_open_file_menu)

        file_menu.addSeparator()

        # save file
        self.save_file_action = QAction('保存', self)
        self.save_file_action.setShortcut('Ctrl+S')
        self.save_file_action.triggered.connect(self.file_save)
        file_menu.addAction(self.save_file_action)

        # save file as ...
        saveas_file_action = QAction('另存为', self)
        saveas_file_action.setShortcut('Ctrl+Shift+S')
        saveas_file_action.triggered.connect(self.file_saveas)
        file_menu.addAction(saveas_file_action)

        file_menu.addSeparator()

        # export as 
        exportas_menu = QMenu('导出', self)
        # TODO: function bind with action
        exportas_png_action = QAction('PNG', self)
        exportas_png_action.triggered.connect(self.exportas_png)
        exportas_menu.addAction(exportas_png_action)

        exportas_pdf_action = QAction('PDF', self)
        exportas_pdf_action.triggered.connect(self.exportas_pdf)
        exportas_menu.addAction(exportas_pdf_action)

        file_menu.addMenu(exportas_menu)

        file_menu.addSeparator()

        # print file
        print_action = QAction('打印', self)
        print_action.setShortcut('Ctrl+P')
        print_action.triggered.connect(self.file_print)
        file_menu.addAction(print_action)

        file_menu.addSeparator()

        # quit
        quit_action = QAction('退出', self)
        quit_action.setShortcut('Ctrl+Q')
        quit_action.triggered.connect(self.quit)
        file_menu.addAction(quit_action)

        # Edit menu
        edit_menu = self.menuBar().addMenu('编辑')

        # undo
        self.undo_action = self.m_undoStack.createUndoAction(self, '撤销')
        self.undo_action.setShortcut('Ctrl+Z')
        edit_menu.addAction(self.undo_action)

        # Redo
        self.redo_action = self.m_undoStack.createRedoAction(self, '恢复')
        self.redo_action.setShortcut('Ctrl+Y')
        edit_menu.addAction(self.redo_action)

        edit_menu.addSeparator()

        # Cut
        cut_action = QAction('剪切', self)
        cut_action.setShortcut('Ctrl+X')
        cut_action.triggered.connect(self.scene.cut)
        edit_menu.addAction(cut_action)

        # Copy
        copy_action = QAction('拷贝', self)
        copy_action.setShortcut('Ctrl+C')
        copy_action.triggered.connect(self.scene.copy)
        edit_menu.addAction(copy_action)

        # Paste
        paste_action = QAction('粘贴', self)
        paste_action.setShortcut('Ctrl+V')
        paste_action.triggered.connect(self.scene.paste)
        edit_menu.addAction(paste_action)

        # Delete
        delete_action = QAction('删除', self)
        delete_action.setShortcut('Delete')
        delete_action.triggered.connect(self.scene.removeNode)
        edit_menu.addAction(delete_action)

        edit_menu.addSeparator()

        # 皮肤
        skin_action = QAction('更改皮肤', self)
        skin_action.triggered.connect(self.setSkin)
        edit_menu.addAction(skin_action)

        # Insert menu

        insert_menu = self.menuBar().addMenu('插入')

        add_icon_action = QAction('图标', self)
        add_icon_action.setShortcut('Ctrl+I')
        add_icon_action.triggered.connect(self.add_icon)
        insert_menu.addAction(add_icon_action)

        add_link_action = QAction('链接', self)
        add_link_action.setShortcut('Ctrl+L')
        add_link_action.triggered.connect(self.add_link)
        insert_menu.addAction(add_link_action)

        add_notes_action = QAction('备注', self)
        add_notes_action.triggered.connect(self.add_notes)
        insert_menu.addAction(add_notes_action)

        # Help menu
        help_menu = self.menuBar().addMenu('帮助')

        hotKey_help_action = QAction('快捷键', self)
        hotKey_help_action.triggered.connect(self.hot_key)
        help_menu.addAction(hotKey_help_action)

        about_action = QAction('关于', self)
        about_action.triggered.connect(self.about)
        help_menu.addAction(about_action)

    #  ToolBar
    def setUpToolBar(self):
        self.toolbar = self.addToolBar('toolbar')
        self.toolbar.setMovable(False)
        self.toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.toolbar.setIconSize(QSize(28, 28))
        self.toolbar.setStyleSheet("QToolBar{spacing:16px;}")
        #  New Sibling Node
        new_siblingNode_action = QAction(QIcon(self.root + '/images/增加同级.png'), '增加同级', self)
        new_siblingNode_action.setShortcut('Shift+Tab')
        new_siblingNode_action.triggered.connect(self.scene.addSiblingNode)
        self.toolbar.addAction(new_siblingNode_action)

        #  New Son Node
        new_sonNode_action = QAction(QIcon(self.root + '/images/增加子级.png'), '增加子级', self)
        new_sonNode_action.setShortcut('Tab')
        new_sonNode_action.triggered.connect(self.scene.addSonNode)
        self.toolbar.addAction(new_sonNode_action)

        #  Add Link
        add_link_action = QAction(QIcon(self.root + '/images/addLink.png'), '添加链接', self)
        add_link_action.triggered.connect(self.add_link)
        self.toolbar.addAction(add_link_action)

        #  Link
        add_branch_action = QAction(QIcon(self.root + '/images/link.png'), '链接', self)
        # add_branch_action.triggered.connect(self.scene.buildRelation)
        add_branch_action.triggered.connect(self.link_relation)
        self.toolbar.addAction(add_branch_action)

        #  Add Notes
        add_notes_action = QAction(QIcon(self.root + '/images/note.png'), '备注', self)
        add_notes_action.triggered.connect(self.add_notes)
        self.toolbar.addAction(add_notes_action)

        #  Delete
        addBranch_action = QAction(QIcon(self.root + '/images/delete.png'), '删除', self)
        addBranch_action.triggered.connect(self.scene.removeNode)
        self.toolbar.addAction(addBranch_action)

        #  undo
        self.undo_action.setIcon(QIcon(self.root + '/images/undo.png'))
        self.toolbar.addAction(self.undo_action)

        #  redo
        self.redo_action.setIcon(QIcon(self.root + '/images/redo.png'))
        self.toolbar.addAction(self.redo_action)

        self.scene.setUndoStack(self.m_undoStack)

    #  IconToolBar
    def setUpIconToolBar(self):
        self.icontoolbar = QToolBar('icon toolbar', self)
        self.icontoolbar.setIconSize(QSize(28, 28))
        self.icontoolbar.setMovable(False)
        # self.icontoolbar.setAutoFillBackground(True)
        # self.icontoolbar.setPalette(QPalette(QColor(Qt.lightGray)))
        # # Method1：仅设置Toolbar的背景色为红色
        # toolbar.setPalette(QPalette(QColor(0xFF, 0x00, 0x00)))
        # # Method2：同时设置Toolbar的背景色和前景色
        # _palette = QPalette()
        # _palette.setColor(QPalette.Button, QColor(Qt.lightGray))
        # _palette.setColor(QPalette.ButtonText, QColor(Qt.lightGray))
        # self.icontoolbar.setPalette(_palette)

        m_signalMapper = QSignalMapper(self)

        # application-system
        application_system_action = QAction(QIcon(self.root + '/icons/1_round_solid.svg'), 'Applications-system', self)
        application_system_action.triggered.connect(m_signalMapper.map)
        m_signalMapper.setMapping(application_system_action, self.root + '/icons/1_round_solid.svg')

        # trash icon
        trash_action = QAction(QIcon(self.root + '/icons/2_round_solid.svg'), 'Trash', self)
        trash_action.triggered.connect(m_signalMapper.map)
        m_signalMapper.setMapping(trash_action, self.root + '/icons/2_round_solid.svg')

        # mail icon
        mail_action = QAction(QIcon(self.root + '/icons/3_round_solid.svg'), 'Mail', self)
        mail_action.triggered.connect(m_signalMapper.map)
        m_signalMapper.setMapping(mail_action, self.root + '/icons/3_round_solid.svg')

        # warn icon
        warn_action = QAction(QIcon(self.root + '/icons/4_round_solid.svg'), 'Warning', self)
        warn_action.triggered.connect(m_signalMapper.map)
        m_signalMapper.setMapping(warn_action, self.root + '/icons/4_round_solid.svg')

        # how icon
        help_action = QAction(QIcon(self.root + '/icons/5_round_solid.svg'), 'Help', self)
        help_action.triggered.connect(m_signalMapper.map)
        m_signalMapper.setMapping(help_action, self.root + '/icons/5_round_solid.svg')

        # calendar icon
        calendar_action = QAction(QIcon(self.root + '/icons/6_round_solid.svg'), 'Calendar', self)
        calendar_action.triggered.connect(m_signalMapper.map)
        m_signalMapper.setMapping(calendar_action, self.root + '/icons/6_round_solid.svg')

        # system_users icon
        system_users_action = QAction(QIcon(self.root + '/icons/7_round_solid.svg'), 'System-users', self)
        system_users_action.triggered.connect(m_signalMapper.map)
        m_signalMapper.setMapping(system_users_action, self.root + '/icons/7_round_solid.svg')

        # info icon
        info_action = QAction(QIcon(self.root + '/icons/8_round_solid.svg'), 'Infomation', self)
        info_action.triggered.connect(m_signalMapper.map)
        m_signalMapper.setMapping(info_action, self.root + '/icons/8_round_solid.svg')

        m_signalMapper.mapped[str].connect(self.scene.insertPicture)

        self.icontoolbar.addAction(application_system_action)
        self.icontoolbar.addAction(trash_action)
        self.icontoolbar.addAction(mail_action)
        self.icontoolbar.addAction(warn_action)
        self.icontoolbar.addAction(help_action)
        self.icontoolbar.addAction(calendar_action)
        self.icontoolbar.addAction(system_users_action)
        self.icontoolbar.addAction(info_action)

        self.addToolBar(Qt.TopToolBarArea, self.icontoolbar)
        self.icontoolbar.show()

    #  The bottom status bar
    def setUpStatusBar(self):
        zoomSlider = MySlider(self.view, Qt.Horizontal)
        zoomSlider.setMaximumWidth(400)
        zoomSlider.setRange(20, 200)
        zoomSlider.setSingleStep(5)  # 方向键步进值为5
        zoomSlider.setPageStep(5)  # 鼠标步进值为5
        zoomSlider.setValue(100)

        self.label1 = QLabel('100%')
        self.label2 = QLabel('主题: 1')
        self.label3 = QLabel('welcome to PyMind!')

        widget = QWidget(self)
        hbox = QHBoxLayout()

        hbox.addWidget(self.label3)
        # hbox.addWidget(self.label2)
        hbox.addWidget(zoomSlider)
        hbox.addWidget(self.label1)

        widget.setLayout(hbox)

        # 滑块跟踪
        zoomSlider.valueChanged.connect(self.labelShow)

        self.statusBar().addWidget(widget, 5)

    #  bottom label Change
    def nodeNumChange(self, v):
        self.label2.setText('主题: ' + str(v))

    def labelShow(self, v):
        self.label1.setText(str(v) + '%')

    def messageShow(self, text):
        self.label3.setText(text)

    def contentChanged(self, changed=True):
        print('m_contentChanged: ', self.m_contentChanged)
        if not self.m_contentChanged and changed:
            self.timer.start(AUTOSAVE_TIME)
            self.setWindowTitle('*' + self.windowTitle())
            self.m_contentChanged = True

            fileinfo = QFileInfo(self.m_filename)
            if '未命名' not in self.windowTitle() and fileinfo.isWritable():
                self.save_file_action.setEnabled(True)

        elif self.m_contentChanged and not changed:
            self.timer.stop()
            self.setWindowTitle(self.windowTitle()[1:])
            self.m_contentChanged = False
            self.save_file_action.setEnabled(False)

    # TODO: scene center move
    def file_new(self):
        if not self.close_file():
            return

        self.m_filename = None
        self.scene.addFirstNode()
        self.update_title()

    # TODO: make sure file is valid !
    def file_open(self, filename=''):

        cur_filename = self.m_filename
        print('file_open_cur_filename: ', cur_filename)
        if not filename:
            if self.sender().text() in self.m_settings.value('lastpath'):
                self.m_filename = self.root + '/files/' + self.sender().text()
                print('file_open_self.m_filename: ', self.m_filename)
            else:
                dialog = QFileDialog(self, '打开', self.root + '/files', 'MindMap(*.mm)')
                dialog.setAcceptMode(QFileDialog.AcceptOpen)
                dialog.setDefaultSuffix('mm')
                # 用户取消
                if not dialog.exec():
                    return
                self.m_filename = dialog.selectedFiles()[0]
                print('dialog.selectedFiles()[0]: ', self.m_filename)
        else:
            self.m_filename = filename
        fileInfo = QFileInfo(self.m_filename)
        if not fileInfo.isWritable():
            print('Read-Only File !')

        if not self.close_file():
            return

        if not self.scene.readContentFromXmlFile(self.m_filename):
            self.m_filename = cur_filename
            return

        lastpath = self.m_settings.value('lastpath')
        if len(lastpath) < 5:
            if os.path.basename(self.m_filename) not in lastpath:
                lastpath.append(os.path.basename(self.m_filename))
                self.m_settings.setValue('lastpath', lastpath)
                self.file_last_open()
        else:
            if os.path.basename(self.m_filename) not in lastpath:
                lastpath.append(os.path.basename(self.m_filename))
                self.m_settings.setValue('lastpath', lastpath[1:])
                self.file_last_open()
            else:
                lastpath.append(os.path.basename(self.m_filename))
                lastpathItem = lastpath[len(lastpath) - 1]
                list2 = []
                for i in lastpath:
                    if i not in list2:
                        list2.append(i)
                for i in list2:
                    if i == lastpathItem:
                        list2.remove(i)
                list2.append(lastpathItem)
                self.m_settings.setValue('lastpath', list2)
                self.file_last_open()

        self.update_title()

    def file_last_open(self):
        lastpath = self.m_settings.value('lastpath')

        if not lastpath:
            last_open_action = QAction('no last file', self)
            self.last_open_file_menu.addAction(last_open_action)
        else:
            self.last_open_file_menu.clear()
            for filename in reversed(lastpath):
                last_open_action = QAction(filename, self)
                last_open_action.triggered.connect(self.file_open)
                self.last_open_file_menu.addAction(last_open_action)

    def file_save(self, checkIfReadOnly=True):
        fileinfo = QFileInfo(self.m_filename)
        if checkIfReadOnly and not fileinfo.isWritable():
            self.messageShow('Error: the file is read only !')
            return
        if self.windowTitle() == '未命名' or self.windowTitle() == '*未命名':
            dialog = QFileDialog(self, '保存为', self.root + '/files', 'MindMap(*.mm)')
            dialog.setAcceptMode(QFileDialog.AcceptSave)
            dialog.setDefaultSuffix('mm')
            if not dialog.exec():
                return False

            self.m_filename = dialog.selectedFiles()[0]
            print('dialog.selectedFiles():', dialog.selectedFiles()[0])

        print('m_filename: ', self.m_filename)
        self.scene.writeContentToXmlFile(self.m_filename)
        self.contentChanged(False)
        self.m_undoStack.clear()

        self.update_title()

    def file_autoSave(self):
        fileInfo = QFileInfo(self.m_filename)
        if self.windowTitle() != '未命名' and fileInfo.isWritable():
            self.file_save()

    def file_saveas(self):
        dialog = QFileDialog(self, '另存为', self.root + '/files', 'MindMap(*.mm)')
        dialog.setAcceptMode(QFileDialog.AcceptSave)
        dialog.setDefaultSuffix('mm')

        if not dialog.exec():
            return False

        self.m_filename = dialog.selectedFiles()[0]
        print(dialog.selectedFiles())
        self.file_save(False)
        self.update_title()

    def file_print(self):
        printer = QPrinter(QPrinter.HighResolution)
        if QPrintDialog(printer).exec() == QDialog.Accepted:
            painter = QPainter(printer)
            painter.setRenderHint(QPainter.Antialiasing)
            self.scene.render(painter)
            painter.end()

    def close_file(self):
        if self.m_contentChanged:
            msgBox = QMessageBox(self)
            msgBox.setWindowTitle('Save MindMap')
            msgBox.setText('The MindMap has been modified !')
            msgBox.setInformativeText('Do you want to save this file ?')
            msgBox.setStandardButtons(QMessageBox.Save |
                                      QMessageBox.Ignore |
                                      QMessageBox.Cancel)

            msgBox.setDefaultButton(QMessageBox.Save)
            ret = msgBox.exec()

            if ret == QMessageBox.Save:
                if '未命名' in self.windowTitle():
                    if not self.file_saveas():
                        return False
                else:
                    self.file_save()
            elif ret == QMessageBox.Cancel:
                return False

        self.m_contentChanged = False
        self.scene.removeAllNodes()
        self.scene.removeAllBranches()
        self.m_undoStack.clear()
        return True

    def exportas_png(self):
        dialog = QFileDialog(self, 'Export mindmap as', self.root + '/files', 'MindMap(*.png)')
        dialog.setAcceptMode(QFileDialog.AcceptSave)
        dialog.setDefaultSuffix('png')

        if not dialog.exec():
            return False

        png_filename = dialog.selectedFiles()[0]
        print(dialog.selectedFiles())
        self.scene.writeContentToPngFile(png_filename)

    def exportas_pdf(self):
        dialog = QFileDialog(self, 'Export mindmap as', self.root + '/files', 'MindMap(*.pdf)')
        dialog.setAcceptMode(QFileDialog.AcceptSave)
        dialog.setDefaultSuffix('pdf')

        if not dialog.exec():
            return False

        pdf_filename = dialog.selectedFiles()[0]
        print(dialog.selectedFiles())
        self.scene.writeContentToPdfFile(pdf_filename)

    def quit(self):
        self.close_signal.emit()
        if self.m_contentChanged and not self.close_file():
            return
        qApp.quit()

    def closeEvent(self, e):
        self.close_signal.emit()
        if self.m_contentChanged and not self.close_file():
            e.ignore()
        else:
            e.accept()

    # 获取节点位置
    def getPos(self, size):
        p = QPointF(self.scene.m_activateNode.boundingRect().center().x(),
                    self.scene.m_activateNode.boundingRect().bottomRight().y())
        sceneP = self.scene.m_activateNode.mapToScene(p)
        viewP = self.view.mapFromScene(sceneP)
        pos = self.view.viewport().mapToGlobal(viewP)
        x = pos.x() - size[0] / 2
        y = pos.y()
        return x, y

    def add_notes(self):
        x, y = self.getPos(NOTE_SIZE)
        print('x,y: ', x, y)
        self.addNote.emit(x, y, self.scene.m_activateNode.m_note)

    # 链接外部网页
    def link_relation(self):
        webbrowser.open_new(self.scene.m_activateNode.m_link)

    def getNote(self, note):
        self.scene.m_activateNode.m_note = note

    def add_link(self):
        x, y = self.getPos(LINK_SIZE)
        print(x, y)
        self.addLink.emit(x, y, self.scene.m_activateNode.m_link)

    def getLink(self, link):
        self.scene.m_activateNode.m_link = link
        if not self.scene.m_activateNode.hasLink and link != 'https://':
            self.scene.m_activateNode.hasLink = True
            self.scene.m_activateNode.insertLink(link)
            self.scene.adjustSubTreeNode()
            self.scene.adjustBranch()
        elif self.scene.m_activateNode.hasLink:
            self.scene.m_activateNode.updateLink(link)

    def setSkin(self):
        dialog = QColorDialog()
        dialog.setWindowTitle('设置主界面颜色')
        if not dialog.exec():
            return
        skin_Color = dialog.selectedColor()
        print('skin_color', skin_Color)
        skin_Color_R = skin_Color.red()
        skin_Color_G = skin_Color.green()
        skin_Color_B = skin_Color.blue()
        print('RGB: ', skin_Color_B, skin_Color_G, skin_Color_R)
        # hex返回的字母A~F均为小写字母a~f，根据样例输出，用upper函数把字母全部转为大写
        hex1 = hex(int(skin_Color_R))[2:].upper()
        hex2 = hex(int(skin_Color_G))[2:].upper()
        hex3 = hex(int(skin_Color_B))[2:].upper()
        # 十进制转16进制时会出现缺省零的情况，用rjust函数可在字符串左侧填充0
        # 同理 ljust函数可在字符串的右侧填充0
        hex1 = hex1.rjust(2, '0')
        hex2 = hex2.rjust(2, '0')
        hex3 = hex3.rjust(2, '0')
        outputstr = "#"
        outputstr = outputstr + hex1 + hex2 + hex3
        skinFinalColor = 'QMainWindow{background: ' + outputstr + ';}'
        print('outputstr', outputstr, skinFinalColor)
        self.setStyleSheet('{}'.format(skinFinalColor))

    def about(self):
        msgBox = QMessageBox(self)
        msgBox.setWindowTitle('About PyMind')
        msgBox.setText('PyMind is written with PyQt5')
        msgBox.setTextFormat(Qt.RichText)
        pic = QPixmap(self.root + '/images/icon_m.png')
        msgBox.setIconPixmap(pic.scaled(60, 60))
        msgBox.exec()

    def hot_key(self):
        if not self.dock.isVisible():
            self.dock.show()

    def add_icon(self):
        if self.icontoolbar.isVisible():
            self.icontoolbar.hide()
        else:
            self.icontoolbar.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setApplicationName('MyXind')

    window = MainWindow()
    NoteWindow = Note()
    LinkWindow = Link()

    window.addNote.connect(NoteWindow.handle_addnote)
    window.close_signal.connect(NoteWindow.handle_close)
    window.scene.press_close.connect(NoteWindow.handle_close)

    NoteWindow.note.connect(window.getNote)
    NoteWindow.noteChange.connect(window.contentChanged)

    window.addLink.connect(LinkWindow.handle_addLink)
    window.close_signal.connect(LinkWindow.handle_close)
    window.scene.press_close.connect(LinkWindow.handle_close)

    LinkWindow.link.connect(window.getLink)
    LinkWindow.linkChange.connect(window.contentChanged)

    sys.exit(app.exec_())
