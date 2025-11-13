import os, json, re
import sqlite3
from resource_manager import ResourceManager, get_resource_manager

class DictionaryManager:
    
    DB_PATH_REL     = './data/dict.db'
    TEXT_FOLDER_REL = './data/text_files/'
    TEXT_FILE_DICT  = {
        'en':   'en.ini',
        'cn':   'cn.ini',
        'rsui': 'rsui.ini'
    }
    TEXT_FILE_LIST = ['en', 'cn']
    
    def __init__(self) -> None:
        self.resource_manager = get_resource_manager()
        self.db_path = self.resource_manager.get_external_path(self.DB_PATH_REL)
        self.reader = TextReader()
        
    def __conv_path(self, path: str, sep = '/'):
        path_list = path.split(sep)
        ret = ''
        for p in path_list:
            ret = os.path.join(ret, p)
        return ret
        
    def create_db(self):
        if os.path.exists(self.db_path): return True
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            for key in self.TEXT_FILE_LIST:
                cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS text_{key} (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        text_id TEXT NOT NULL UNIQUE,
                        text TEXT NOT NULL
                    )
                ''')
    
    def refresh_db(self):
        for key in self.TEXT_FILE_LIST:
            text_file_rel  = self.TEXT_FOLDER_REL + self.TEXT_FILE_DICT[key]
            text_file_rel  = self.__conv_path(text_file_rel)
            text_file_path = self.resource_manager.get_external_path(text_file_rel)
            if not os.path.exists(text_file_path):
                raise RuntimeError(f"文本文件{key}不存在，无法读取")
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                text_list = self.reader.read_as_list(text_file_path)
                cursor.execute(f"DELETE FROM text_{key}")
                cursor.executemany(f'''
                    INSERT OR REPLACE INTO text_{key} (text_id, text)
                    VALUES (?, ?)
                ''', text_list)
                    
class TextReader:
    
    def __init__(self) -> None:
        pass
    
    def read_as_list(self, file_path) -> list:
        return []