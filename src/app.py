import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QLineEdit, QPushButton, QCheckBox, 
                               QListWidget, QLabel, QListWidgetItem, QProgressBar,
                               QMessageBox)
from PySide6.QtCore import Qt

from DataFetch import DataFetchThread

class DictionaryApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("字典应用 - 加载中...")
        self.setGeometry(300, 300, 800, 600)
        
        # 初始化为空数据，等待网络数据加载
        self.dictionary_data = []
        
        self.setup_ui()
        self.connect_signals()
        
        # 启动数据抓取
        self.start_data_fetch()
        
    def setup_ui(self):
        """设置用户界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # 添加进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(0)  # 无限进度条
        self.progress_label = QLabel("正在加载数据，请稍候...")
        
        # 第一行：搜索框和按钮
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("请输入要搜索的单词...")
        self.search_input.setEnabled(False)  # 初始禁用
        self.search_button = QPushButton("搜索")
        self.search_button.setEnabled(False)  # 初始禁用
        
        search_layout.addWidget(self.search_input, 1)
        search_layout.addWidget(self.search_button)
        
        # 第二行：复选框
        checkbox_layout = QHBoxLayout()
        self.include_desc_checkbox = QCheckBox("包括描述")
        self.fuzzy_search_checkbox = QCheckBox("模糊搜索")
        self.include_desc_checkbox.setEnabled(False)  # 初始禁用
        self.fuzzy_search_checkbox.setEnabled(False)  # 初始禁用
        
        checkbox_layout.addWidget(self.include_desc_checkbox)
        checkbox_layout.addWidget(self.fuzzy_search_checkbox)
        checkbox_layout.addStretch()
        
        # 第三行：搜索结果列表
        self.result_list = QListWidget()
        self.result_list.setMinimumHeight(300)
        
        # 第四行和第五行：程序控制的文本
        self.info_label1 = QLabel("正在加载数据...")
        self.info_label2 = QLabel("请等待数据加载完成")
        
        # 添加所有组件到主布局
        main_layout.addWidget(self.progress_label)
        main_layout.addWidget(self.progress_bar)
        main_layout.addLayout(search_layout)
        main_layout.addLayout(checkbox_layout)
        main_layout.addWidget(self.result_list, 1)
        main_layout.addWidget(self.info_label1)
        main_layout.addWidget(self.info_label2)
        
    def connect_signals(self):
        """连接信号和槽"""
        self.search_button.clicked.connect(self.perform_search)
        self.search_input.returnPressed.connect(self.perform_search)
        self.result_list.itemSelectionChanged.connect(self.on_item_selected)
    
    def start_data_fetch(self):
        """启动数据抓取"""
        self.fetch_thread = DataFetchThread()
        self.fetch_thread.data_fetched.connect(self.on_data_loaded)
        self.fetch_thread.progress_updated.connect(self.on_progress_updated)
        self.fetch_thread.error_occurred.connect(self.on_error_occurred)
        self.fetch_thread.start()
    
    def on_data_loaded(self, data):
        """数据加载完成的回调"""
        self.dictionary_data = data
        
        # 启用所有控件
        self.search_input.setEnabled(True)
        self.search_button.setEnabled(True)
        self.include_desc_checkbox.setEnabled(True)
        self.fuzzy_search_checkbox.setEnabled(True)
        
        # 隐藏进度条
        self.progress_bar.hide()
        self.progress_label.hide()
        
        # 更新窗口标题
        self.setWindowTitle("字典应用")
        
        # 显示所有数据
        self.display_results(self.dictionary_data)
        self.info_label1.setText("数据加载完成")
        self.info_label2.setText(f"共加载 {len(self.dictionary_data)} 条记录")
    
    def on_progress_updated(self, message):
        """进度更新的回调"""
        self.progress_label.setText(message)
        self.info_label1.setText(message)
    
    def on_error_occurred(self, error_message):
        """错误处理的回调"""
        self.progress_label.setText("加载失败，使用本地数据")
        QMessageBox.warning(self, "加载警告", error_message)
        
    def perform_search(self):
        """执行搜索"""
        search_term = self.search_input.text().strip().lower()
        
        if not search_term:
            results = self.dictionary_data
            self.info_label1.setText("显示所有结果")
            self.info_label2.setText(f"共找到 {len(results)} 条记录")
        else:
            results = []
            include_desc = self.include_desc_checkbox.isChecked()
            fuzzy_search = self.fuzzy_search_checkbox.isChecked()
            
            for item in self.dictionary_data:
                match_found = False
                search_fields = [item['english'].lower(), item['chinese'].lower()]
                
                if include_desc:
                    search_fields.append(item['description'].lower())
                
                for field in search_fields:
                    if fuzzy_search:
                        if search_term in field:
                            match_found = True
                            break
                    else:
                        if field == search_term:
                            match_found = True
                            break
                
                if match_found:
                    results.append(item)
            
            self.info_label1.setText(f"搜索关键词: '{search_term}'")
            search_type = "模糊搜索" if fuzzy_search else "精确搜索"
            desc_info = "（包括描述）" if include_desc else ""
            self.info_label2.setText(f"{search_type}{desc_info} - 找到 {len(results)} 条结果")
        
        self.display_results(results)
    
    def display_results(self, results):
        """显示搜索结果"""
        self.result_list.clear()
        
        for item in results:
            display_text = f"[{item['id']}] {item['english']} - {item['chinese']}"
            if self.include_desc_checkbox.isChecked():
                display_text += f" ({item['description']})"
            
            list_item = QListWidgetItem(display_text)
            list_item.setData(Qt.ItemDataRole.UserRole, item)
            self.result_list.addItem(list_item)
    
    def on_item_selected(self):
        """处理列表项选择事件"""
        current_item = self.result_list.currentItem()
        if current_item:
            data = current_item.data(Qt.ItemDataRole.UserRole)
            if data:
                self.info_label1.setText(f"选中: {data['english']} - {data['chinese']}")
                self.info_label2.setText(f"ID: {data['id']}, 描述: {data['description']}")

def main():
    app = QApplication(sys.argv)
    
    app.setStyleSheet("""
        QLineEdit {
            padding: 8px;
            border: 1px solid;
            border-radius: 4px;
            font-size: 14px;
        }
        QPushButton {
            padding: 8px 16px;
            border: 1px solid;
            border-radius: 4px;
            font-size: 14px;
            font-weight: bold;
            min-width: 60px;
        }
        QPushButton:disabled {
            opacity: 0.6;
        }
        QCheckBox {
            font-size: 12px;
            spacing: 5px;
        }
        QCheckBox:disabled {
            opacity: 0.6;
        }
        QListWidget {
            border: 1px solid;
            border-radius: 4px;
            font-size: 13px;
        }
        QListWidget::item {
            padding: 8px;
            border-bottom: 1px solid;
        }
        QLabel {
            font-size: 12px;
            padding: 4px;
        }
        QProgressBar {
            border: 1px solid;
            border-radius: 4px;
            text-align: center;
            font-size: 12px;
        }
    """)
    
    window = DictionaryApp()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
