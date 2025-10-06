import requests, json
from PySide6.QtCore import QThread, Signal

class DataFetchThread(QThread):
    """数据抓取线程"""
    data_fetched = Signal(list)  # 数据抓取完成信号
    progress_updated = Signal(str)  # 进度更新信号
    error_occurred = Signal(str)  # 错误信号
    
    def __init__(self):
        super().__init__()
        # 可以配置多个数据源
        self.data_sources = [
            "https://api.github.com/repos/microsoft/vscode/contents/README.md",  # 示例API
            # 添加更多数据源...
        ]
    
    def run(self):
        """在后台线程中执行数据抓取"""
        try:
            self.progress_updated.emit("正在连接服务器...")
            
            # 示例：从在线源抓取数据
            # 这里我提供几个示例，你可以根据实际需要修改
            online_data = self.fetch_online_dictionary_data()
            
            if online_data:
                self.progress_updated.emit("数据加载完成")
                self.data_fetched.emit(online_data)
            else:
                self.progress_updated.emit("使用本地数据")
                # 如果在线数据获取失败，使用默认数据
                self.data_fetched.emit(self.get_default_data())
                
        except Exception as e:
            self.error_occurred.emit(f"数据加载失败: {str(e)}")
            self.data_fetched.emit(self.get_default_data())
    
    def fetch_online_dictionary_data(self):
        """从在线源获取字典数据"""
        try:
            # 示例1: 从一个模拟的在线词典API获取数据
            # 注意：这里使用的是示例URL，实际使用时需要替换为真实的API
            
            # 方法1: 从JSONPlaceholder获取模拟数据（仅作演示）
            self.progress_updated.emit("正在获取在线数据...")
            
            # 模拟延时
            self.msleep(2000)
            
            # 这里可以添加真实的API调用
            # response = requests.get("https://your-dictionary-api.com/words", timeout=10)
            # if response.status_code == 200:
            #     return self.parse_api_data(response.json())
            
            # 示例：生成一些在线数据（实际应用中替换为真实的API调用）
            online_words = [
                {"id": "online_001", "english": "awesome", "chinese": "令人敬畏的", "description": "非常棒的，了不起的"},
                {"id": "online_002", "english": "incredible", "chinese": "难以置信的", "description": "不可思议的，非常好的"},
                {"id": "online_003", "english": "fantastic", "chinese": "极好的", "description": "非常棒的，奇妙的"},
                {"id": "online_004", "english": "excellent", "chinese": "优秀的", "description": "卓越的，极好的"},
                {"id": "online_005", "english": "wonderful", "chinese": "精彩的", "description": "令人惊喜的，很棒的"},
                {"id": "online_006", "english": "amazing", "chinese": "惊人的", "description": "令人惊叹的"},
                {"id": "online_007", "english": "brilliant", "chinese": "杰出的", "description": "聪明的，出色的"},
                {"id": "online_008", "english": "outstanding", "chinese": "杰出的", "description": "突出的，优秀的"},
                {"id": "online_009", "english": "remarkable", "chinese": "非凡的", "description": "值得注意的，卓越的"},
                {"id": "online_010", "english": "spectacular", "chinese": "壮观的", "description": "引人注目的，非常棒的"},
            ]
            
            return online_words
            
        except requests.RequestException as e:
            self.progress_updated.emit(f"网络请求失败: {str(e)}")
            return None
        except Exception as e:
            self.progress_updated.emit(f"数据解析失败: {str(e)}")
            return None
    
    def parse_api_data(self, api_data):
        """解析API返回的数据"""
        # 根据实际API返回的数据格式进行解析
        parsed_data = []
        # 这里添加解析逻辑
        return parsed_data
    
    def get_default_data(self):
        """获取默认的本地数据"""
        return [
            {"id": "001", "english": "hello", "chinese": "你好", "description": "常用问候语"},
            {"id": "002", "english": "world", "chinese": "世界", "description": "地球，全世界"},
            {"id": "003", "english": "computer", "chinese": "电脑", "description": "计算机设备"},
            {"id": "004", "english": "programming", "chinese": "编程", "description": "程序设计"},
            {"id": "005", "english": "application", "chinese": "应用程序", "description": "软件应用"},
            {"id": "006", "english": "dictionary", "chinese": "字典", "description": "词汇集合"},
            {"id": "007", "english": "search", "chinese": "搜索", "description": "查找功能"},
            {"id": "008", "english": "language", "chinese": "语言", "description": "交流工具"},
            {"id": "009", "english": "translation", "chinese": "翻译", "description": "语言转换"},
            {"id": "010", "english": "learning", "chinese": "学习", "description": "获取知识"}
        ]