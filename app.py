import sys
import time
import traceback
import logging
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QComboBox, QCheckBox, QListWidget,
    QTextBrowser, QListWidgetItem, QDialog, QLabel, QSizePolicy,
    QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent, QIntValidator
from PySide6.QtCore import QThread, Signal
from html import escape

from dict_manager import DictionaryManager

class DictionaryApp(QMainWindow):
    
    DEFAULT_LIMIT = 100
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("星际公民 - 中英文本互查词典")
        self.setMinimumSize(600, 500)
        
        # 初始化设置变量
        self.search_mode = "双边搜索"
        self.include_long_text = False
        self.show_text_id = False
        self.use_comm_text = False
        self.search_limit = None
        
        self.advanced_mode = True
        
        self.init_ui()
        
        # 数据操作类
        self.dict_manager = DictionaryManager()
    
    # NOTE 报错回调
    def show_error_dialog(self, exception):
        """显示错误对话框"""
        error_msg = QMessageBox(self)
        error_msg.setIcon(QMessageBox.Icon.Critical)
        error_msg.setWindowTitle("错误")
        error_msg.setText("程序执行过程中发生错误")
        error_msg.setInformativeText(str(exception))
        error_msg.setDetailedText(traceback.format_exc())
        error_msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        error_msg.exec()

    def init_ui(self):
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        
        # 第一行：搜索栏
        search_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("请输入搜索内容...")
        self.search_input.returnPressed.connect(self.on_search)
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["双边搜索", "中->英", "英->中"])
        self.mode_combo.currentTextChanged.connect(self.on_mode_changed)
        self.mode_combo.setMinimumWidth(100)
        
        self.search_button = QPushButton("搜索")
        self.search_button.clicked.connect(self.on_search)
        self.search_button.setMinimumWidth(80)
        
        search_layout.addWidget(self.search_input, 1)
        search_layout.addWidget(self.mode_combo)
        search_layout.addWidget(self.search_button)
        
        # 第二行：设置选项
        options_layout = QHBoxLayout()
        
        self.long_text_checkbox = QCheckBox("包括长文本")
        self.long_text_checkbox.toggled.connect(lambda checked: setattr(self, 'include_long_text', checked))
        
        self.show_id_checkbox = QCheckBox("结果显示文本ID")
        self.show_id_checkbox.toggled.connect(lambda checked: setattr(self, 'show_text_id', checked))
        
        self.use_comm_text_checkbox = QCheckBox("搜索和结果包括社区汉化版本")
        self.use_comm_text_checkbox.toggled.connect(lambda checked: setattr(self, 'use_comm_text', checked))
        
        self.limit_input = QLineEdit()
        self.limit_input.setPlaceholderText("搜索数量限制, 默认100")
        self.limit_input.setValidator(QIntValidator(0, int(1e6), self))
        
        options_layout.addWidget(self.long_text_checkbox, 1 if self.advanced_mode else 2)
        options_layout.addWidget(self.show_id_checkbox, 1 if self.advanced_mode else 2)
        if self.advanced_mode:
            options_layout.addWidget(self.use_comm_text_checkbox, 2)
        
        options_layout.addWidget(self.limit_input, 4)
        
        # 第三行：搜索结果列表
        self.results_list = QListWidget()
        self.results_list.itemClicked.connect(self.on_result_clicked)
        self.results_list.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # 第四行：搜索细节显示
        self.detail_display = QTextBrowser()
        self.detail_display.setReadOnly(True)
        self.detail_display.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # 第五行：帮助按钮
        # TODO 添加对应功能
        self.buttons_layout = QHBoxLayout()
        self.help_button = QPushButton("帮助")
        self.help_button.clicked.connect(self.show_help)
        self.help_button.setMinimumHeight(30)
        
        self.refresh_local_button = QPushButton("从文件更新文本")
        self.refresh_local_button.clicked.connect(self.refresh_local)
        self.refresh_local_button.setMinimumHeight(30)
        
        self.refresh_web_button = QPushButton("在线更新文本")
        self.refresh_web_button.clicked.connect(self.refresh_web)
        self.refresh_web_button.setMinimumHeight(30)
        
        self.buttons_layout.addWidget(self.help_button, 1)
        self.buttons_layout.addWidget(self.refresh_local_button, 2)
        self.buttons_layout.addWidget(self.refresh_web_button, 2)
        
        # 添加所有组件到主布局
        main_layout.addLayout(search_layout)
        main_layout.addLayout(options_layout)
        main_layout.addWidget(self.results_list, 2)  # 占比2
        main_layout.addWidget(self.detail_display, 1)  # 占比1
        main_layout.addLayout(self.buttons_layout)
        
        # 存储搜索结果数据
        self.search_results = {}
        
        self.buttons = [
            self.search_button,
            self.help_button,
            self.refresh_local_button,
            self.refresh_web_button,
        ]
    
    def enable_buttons(self, status = True):
        if status:
            self.search_input.returnPressed.connect(self.on_search)
        else:
            self.search_input.returnPressed.connect(None)
        
        for b in self.buttons:
            b.setEnabled(status)
    
    def get_search_limit(self):
        """获取搜索数量限制，如果为空或无效则返回None"""
        text = self.limit_input.text().strip()
        if not text:
            return self.DEFAULT_LIMIT
        try:
            limit = int(text)
            return limit if limit >= 0 else self.DEFAULT_LIMIT
        except ValueError:
            return self.DEFAULT_LIMIT
    
    def on_mode_changed(self, mode):
        """搜索模式改变时的处理"""
        self.search_mode = mode
    
    def on_search(self):
        """执行搜索"""
        try:
            search_text = self.search_input.text().strip()
            if not search_text:
                return
                
            # TODO 检查实现
            ranked_ids, results = self.perform_search(search_text)
            self.search_results = results
            self.display_search_results(ranked_ids, results)
        except Exception as e:
            self.show_error_dialog(e)
        
    def perform_search(self, text):
        """执行搜索逻辑（留空待实现）"""
        # TODO 添加设置影响的搜索和显示逻辑
        return self.dict_manager.search(text)
    
    def display_search_results(self, ranked_ids, results):
        """显示搜索结果"""
        # TODO 检查效果进行优化
        # TODO 添加社区汉化显示的相关逻辑
        self.results_list.clear()
        
        for text_id in ranked_ids:
            # 创建列表项
            item = QListWidgetItem(self.results_list)
            label = QLabel()
            label.setTextFormat(Qt.TextFormat.RichText)  # 启用富文本
            label.setWordWrap(True)  # 自动换行
            
            # TODO 根据搜索模式确定显示顺序
            
            text_data = results[text_id]
            display_text = f"{text_data['cn']}<br/>{text_data['en']}"
            label.setText(display_text)
                
            item.setSizeHint(label.sizeHint())
            item.setData(Qt.ItemDataRole.UserRole, text_id)
            self.results_list.setItemWidget(item, label)
    
    def on_result_clicked(self, item):
        """点击搜索结果时的处理"""
        try:
            text_id = item.data(Qt.ItemDataRole.UserRole)
            detail_text = self.get_detail_text(text_id)
            self.detail_display.setHtml(detail_text)
        except Exception as e:
            self.show_error_dialog(e)
 
    def get_detail_text(self, text_id):
        """获取详细文本（留空待实现）"""
        # TODO 获取详细文本 暂时写死等待设置逻辑更新
        text_data = self.dict_manager.get_full_text(text_id)
        text_id_display = f"<b>文本ID:<br/>{text_id}</b><br/>"
        text_content_display = f"<b>中文文本:</b><br/>{text_data['cn']}<br/><b>英文文本:</b><br/>{text_data['en']}"
        return f"<p>{text_id_display}{text_content_display}</p>"
        
    def show_help(self):
        """显示帮助对话框"""
        help_dialog = HelpDialog(self)
        help_dialog.exec()
        
    def refresh_local(self):
        self.enable_buttons(False)
        logging.info('开始使用本地文件更新数据库')
        self.detail_display.setHtml("正在使用本地文件更新数据库<br/>期间无法进行搜索<br/>请耐心等待")
        self.refresh_thread = RefreshLocalThread(self.dict_manager)
        self.refresh_thread.finished.connect(self.on_refresh_finished)
        self.refresh_thread.error.connect(self.on_refresh_error)
        self.refresh_thread.start()
    
    def refresh_web(self):
        pass
    
    def on_refresh_finished(self):
        logging.info('数据库更新操作结束')
        self.detail_display.setHtml("数据库更新完成！")
        self.enable_buttons(True)

    def on_refresh_error(self, exception):
        logging.error('数据库更新时发生错误')
        self.show_error_dialog(exception)
        self.enable_buttons(True)


class HelpDialog(QDialog):
    """帮助对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("帮助")
        self.setMinimumSize(400, 300)
        
        layout = QVBoxLayout(self)
        
        help_browser = QTextBrowser()
        help_browser.setHtml(self.get_help_text())
        help_browser.setOpenExternalLinks(True)
        
        close_button = QPushButton("关闭")
        close_button.clicked.connect(self.close)
        
        layout.addWidget(help_browser)
        layout.addWidget(close_button)
        
    def get_help_text(self):
        """获取帮助文本"""
        # TODO 修改帮助文本
        return """
        <h2>中英互查词典使用说明</h2>
        <h3>基本功能</h3>
        <ul>
            <li>输入中文或英文进行搜索</li>
            <li>支持三种搜索模式：双边搜索、中译英、英译中</li>
            <li>点击搜索结果查看详细信息</li>
        </ul>
        
        <h3>搜索选项</h3>
        <ul>
            <li><b>模糊搜索</b>：启用模糊匹配功能</li>
            <li><b>包括长文本</b>：在搜索结果中包含长文本内容</li>
            <li><b>结果显示文本ID</b>：在搜索结果中显示文本的唯一标识符</li>
        </ul>
        
        <h3>快捷键</h3>
        <ul>
            <li>Enter：执行搜索</li>
        </ul>
        
        <p>更多信息请访问：<a href="https://robertsspaceindustries.com/">TODO</a></p>
        """

class RefreshLocalThread(QThread):
    
    finished = Signal()
    error = Signal(Exception)
    
    def __init__(self, dict_manager):
        super().__init__()
        self.dict_manager = dict_manager
        
    def run(self):
        try:
            self.dict_manager.full_refresh()
            self.finished.emit()
        except Exception as e:
            self.error.emit(e)

class RefreshWebThread(QThread):
    
    finished = Signal()
    error = Signal(Exception)
    
    def __init__(self, dict_manager):
        super().__init__()
        self.dict_manager = dict_manager
        
    def run(self):
        try:
            # TODO 下载逻辑
            self.dict_manager.full_refresh()
            self.finished.emit()
        except Exception as e:
            self.error.emit(e)

def main():
    app = QApplication(sys.argv)
    
    # 创建并显示主窗口
    dictionary = DictionaryApp()
    dictionary.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
