import sys
import time
import traceback
import logging
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QComboBox, QCheckBox, QListWidget,
    QTextBrowser, QListWidgetItem, QDialog, QLabel, QSizePolicy,
    QMessageBox, 
)
from PySide6.QtCore import Qt, Signal, QSize
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
        self.search_mode       = "双边搜索"
        self.fuzzy_search      = False
        self.include_long_text = False
        self.show_text_id      = False
        self.use_comm_text     = False
        self.search_limit      = None
        
        self.advanced_mode     = True
        
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
        
        search_layout.addWidget(self.search_input, 4)
        search_layout.addWidget(self.mode_combo, 1)
        search_layout.addWidget(self.search_button, 1)
        
        # 第二行：设置选项
        options_layout = QHBoxLayout()
        
        self.fuzzy_search_checkbox = QCheckBox("模糊搜索")
        self.fuzzy_search_checkbox.toggled.connect(lambda checked: setattr(self, 'fuzzy_search', checked))
        
        self.long_text_checkbox = QCheckBox("包括长文本")
        self.long_text_checkbox.toggled.connect(lambda checked: setattr(self, 'include_long_text', checked))
        
        self.show_id_checkbox = QCheckBox("显示文本ID")
        self.show_id_checkbox.toggled.connect(lambda checked: setattr(self, 'show_text_id', checked))
        
        self.use_comm_text_checkbox = QCheckBox("包括社区汉化")
        self.use_comm_text_checkbox.toggled.connect(lambda checked: setattr(self, 'use_comm_text', checked))
        
        self.limit_input = QLineEdit()
        self.limit_input.setPlaceholderText("搜索数量限制, 默认100")
        self.limit_input.setValidator(QIntValidator(0, int(1e8), self))
        
        options_layout.addWidget(self.fuzzy_search_checkbox, 1 if self.advanced_mode else 2)
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
        self.buttons_layout = QHBoxLayout()
        self.help_button = QPushButton("帮助")
        self.help_button.clicked.connect(self.show_help)
        self.help_button.setMinimumHeight(30)
        
        self.refresh_local_button = QPushButton("从文件更新文本")
        self.refresh_local_button.clicked.connect(self.refresh_local)
        self.refresh_local_button.setMinimumHeight(30)
        
        # TODO 添加对应功能
        self.refresh_web_button = QPushButton("在线更新文本")
        self.refresh_web_button.clicked.connect(self.refresh_web)
        self.refresh_web_button.setMinimumHeight(30)
        
        self.buttons_layout.addWidget(self.help_button, 1)
        self.buttons_layout.addWidget(self.refresh_local_button, 2)
        # TODO 添加对应功能后取消注释
        # self.buttons_layout.addWidget(self.refresh_web_button, 2)
        
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
            
            self.enable_buttons(False)
            
            # 根据搜索类型显示不同的提示文字
            if self.fuzzy_search:
                self.detail_display.setHtml("正在进行模糊搜索...<br/>模糊搜索耗时较长，请耐心等待<br/>期间程序无响应为正常现象")
            else:
                self.detail_display.setHtml("正在搜索，请稍候...")
            
            # 强制刷新UI显示
            QApplication.processEvents()
            
            ranked_ids, results = self.perform_search(search_text)
            self.search_results = results
            self.display_search_results(ranked_ids, results)
            
            # 搜索完成后显示结果统计
            result_count = len(ranked_ids)
            if result_count > 0:
                self.detail_display.setHtml(f"搜索完成，找到 {result_count} 条结果<br/>点击列表中的项目查看详细信息")
            else:
                self.detail_display.setHtml("未找到匹配的结果<br/>请尝试使用不同的关键词或启用模糊搜索")
                
        except Exception as e:
            self.detail_display.setHtml("搜索过程中发生错误")
            self.show_error_dialog(e)
        finally:
            self.enable_buttons(True)
        
    def perform_search(self, text):
        """执行搜索逻辑（留空待实现）"""
        # TODO 添加设置影响的搜索和显示逻辑
        return self.dict_manager.search(
            keyword=text, 
            fuzzy_search=self.fuzzy_search
        )
    
    def display_search_results(self, ranked_ids, results):
        """显示搜索结果"""
        self.results_list.clear()
        
        for text_id in ranked_ids:
            # 创建列表项
            item = QListWidgetItem(self.results_list)
            
            # 创建容器widget
            container = QWidget()
            container_layout = QVBoxLayout(container)
            container_layout.setContentsMargins(10, 8, 10, 8)  # 左、上、右、下边距
            container_layout.setSpacing(4)
            
            text_data = results[text_id]
            
            # 创建中文标签
            cn_label = QLabel(text_data['cn'])
            cn_label.setWordWrap(True)
            cn_label.setStyleSheet("font-weight: normal; line-height: 1.2;")
            cn_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
            
            # 创建英文标签
            en_label = QLabel(text_data['en'])
            en_label.setWordWrap(True)
            en_label.setStyleSheet("font-weight: normal; line-height: 1.2;")
            en_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
            
            container_layout.addWidget(cn_label)
            container_layout.addWidget(en_label)
            
            # 设置容器的尺寸策略
            container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
            
            # 强制计算实际需要的高度
            # 获取列表的可用宽度
            available_width = self.results_list.viewport().width() - 20  # 减去边距
            
            # 设置固定宽度来计算高度
            container.setFixedWidth(available_width)
            container.updateGeometry()
            
            # 计算每个标签的实际高度
            cn_label.setFixedWidth(available_width - 20)  # 减去容器边距
            en_label.setFixedWidth(available_width - 20)
            
            # 让标签计算自己的高度
            cn_height = cn_label.heightForWidth(available_width - 20)
            en_height = en_label.heightForWidth(available_width - 20)
            
            # 如果heightForWidth返回-1，使用sizeHint
            if cn_height == -1:
                cn_height = cn_label.sizeHint().height()
            if en_height == -1:
                en_height = en_label.sizeHint().height()
            
            # 计算总高度：两个标签高度 + 布局间距 + 容器边距
            total_height = cn_height + en_height + container_layout.spacing() + 16  # 16是上下边距
            
            # 设置最小高度
            total_height = max(total_height, 50)
            
            # 重置宽度策略
            container.setMinimumWidth(0)
            container.setMaximumWidth(16777215)  # Qt的最大宽度
            
            # 设置项目大小
            item.setSizeHint(QSize(available_width, total_height))
            
            item.setData(Qt.ItemDataRole.UserRole, text_id)
            self.results_list.setItemWidget(item, container)


    
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
    
    def __init__(self, dict_manager: DictionaryManager):
        super().__init__()
        self.dict_manager = dict_manager
        
    def run(self):
        try:
            logging.info("本地数据完整刷新数据库")
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
