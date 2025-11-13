import sys
import traceback
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QComboBox, QCheckBox, QListWidget,
    QTextBrowser, QListWidgetItem, QDialog, QLabel, QSizePolicy,
    QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent


class DictionaryApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("中英互查词典")
        self.setMinimumSize(600, 500)
        
        # 初始化设置变量
        self.search_mode = "双边搜索"
        self.fuzzy_search = False
        self.include_long_text = False
        self.show_text_id = False
        
        self.init_ui()
    
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
        
        self.fuzzy_checkbox = QCheckBox("模糊搜索")
        self.fuzzy_checkbox.toggled.connect(lambda checked: setattr(self, 'fuzzy_search', checked))
        
        self.long_text_checkbox = QCheckBox("包括长文本")
        self.long_text_checkbox.toggled.connect(lambda checked: setattr(self, 'include_long_text', checked))
        
        self.show_id_checkbox = QCheckBox("结果显示文本ID")
        self.show_id_checkbox.toggled.connect(self.on_show_id_changed)
        
        options_layout.addWidget(self.fuzzy_checkbox)
        options_layout.addWidget(self.long_text_checkbox)
        options_layout.addWidget(self.show_id_checkbox)
        options_layout.addStretch()
        
        # 第三行：搜索结果列表
        self.results_list = QListWidget()
        self.results_list.itemClicked.connect(self.on_result_clicked)
        self.results_list.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # 第四行：搜索细节显示
        self.detail_display = QTextBrowser()
        self.detail_display.setReadOnly(True)
        self.detail_display.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # 第五行：帮助按钮
        self.help_button = QPushButton("帮助")
        self.help_button.clicked.connect(self.show_help)
        self.help_button.setMinimumHeight(30)
        
        # 添加所有组件到主布局
        main_layout.addLayout(search_layout)
        main_layout.addLayout(options_layout)
        main_layout.addWidget(self.results_list, 2)  # 占比2
        main_layout.addWidget(self.detail_display, 1)  # 占比1
        main_layout.addWidget(self.help_button)
        
        # 存储搜索结果数据
        self.search_results = {}
        
    def on_mode_changed(self, mode):
        """搜索模式改变时的处理"""
        self.search_mode = mode
        
    def on_show_id_changed(self, checked):
        """是否显示文本ID改变时的处理"""
        self.show_text_id = checked
        # 如果有搜索结果，重新显示
        # if self.search_results:
        #     self.display_search_results(self.search_results)
    
    def on_search(self):
        """执行搜索"""
        try:
            search_text = self.search_input.text().strip()
            if not search_text:
                return
                
            # TODO 调用搜索函数（这里留空，实际实现时替换）
            results = self.perform_search(search_text)
            self.search_results = results
            self.display_search_results(results)
        except Exception as e:
            self.show_error_dialog(e)
        
    def perform_search(self, text):
        """执行搜索逻辑（留空待实现）"""
        # TODO 执行搜索逻辑（留空待实现）
        # 这是一个示例返回值，实际使用时替换为真实的搜索逻辑
        # 返回格式: {text_id: (chinese_preview, english_preview)}
        return {
            "id001": ("你好", "Hello"),
            "id002": ("世界", "World"),
            "id003": ("词典", "Dictionary"),
        }
    
    def display_search_results(self, results):
        """显示搜索结果"""
        # TODO 检查效果进行优化
        self.results_list.clear()
        
        for text_id, (chinese, english) in results.items():
            # 创建列表项
            item = QListWidgetItem()
            
            # 根据搜索模式确定显示顺序
            if self.search_mode == "英->中":
                line1 = english
                line2 = chinese
            else:
                line1 = chinese
                line2 = english
            
            # 构建显示文本
            if self.show_text_id:
                display_text = f"[{text_id}]\n{line1}\n{line2}"
            else:
                display_text = f"{line1}\n{line2}"
                
            item.setText(display_text)
            item.setData(Qt.ItemDataRole.UserRole, text_id)  # 存储ID供点击时使用
            
            self.results_list.addItem(item)
    
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
        # TODO 获取详细文本 暂时直接返回文本ID
        return f"<p>文本ID: {text_id}</p>"
    
    def show_help(self):
        """显示帮助对话框"""
        help_dialog = HelpDialog(self)
        help_dialog.exec()


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
        
        <p>更多信息请访问：<a href="https://example.com">官方网站</a></p>
        """


def main():
    app = QApplication(sys.argv)
    
    # 创建并显示主窗口
    dictionary = DictionaryApp()
    dictionary.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
