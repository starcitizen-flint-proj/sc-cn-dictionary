import os, json, re, time
import sqlite3
import jieba
import logging
from html import escape
from fuzzywuzzy import fuzz, process

from resource_manager import ResourceManager, get_resource_manager

# DEBUG
from pprint import pprint

class DictionaryManager:
    
    DB_PATH_REL     = './data/dict.db'
    TEXT_FOLDER_REL = './data/text_files/'
    TEXT_FILE_DICT  = {
        'en':   'en.ini',
        'cn':   'cn.ini',
        'rsui': 'rsui.ini'
    }
    
    def __init__(self, use_rsui = False) -> None:
        self.resource_manager = get_resource_manager()
        self.db_path = self.resource_manager.get_external_path(self.DB_PATH_REL)
        logging.info(f"数据库路径：{self.db_path}")
        self.text_dict = dict()
        self.refreshed = False
        self.used_text = ['en', 'cn', 'rsui'] if use_rsui else ['en', 'cn']
        
        self.display_length = 100
        logging.info('词典数据管理器初始化完毕')
        
    def __conv_path(self, path: str, sep = '/'):
        path_list = path.split(sep)
        ret = ''
        for p in path_list:
            ret = os.path.join(ret, p)
        return ret
        
    def create_db(self):
        # if os.path.exists(self.db_path): return
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            for key in self.used_text:
                logging.info(f"创建表: text_{key}")
                logging.debug(f'''
                    CREATE VIRTUAL TABLE IF NOT EXISTS text_{key} USING fts5(
                        content,
                        text_id UNINDEXED,
                        raw_text UNINDEXED
                    );
                ''')
                cursor.execute(f'''
                    CREATE VIRTUAL TABLE IF NOT EXISTS text_{key} USING fts5(
                        content,
                        text_id UNINDEXED,
                        raw_text UNINDEXED
                    );
                ''')
    
    def refresh_db(self):
        for key in self.used_text:
            text_file_rel  = self.TEXT_FOLDER_REL + self.TEXT_FILE_DICT[key]
            text_file_rel  = self.__conv_path(text_file_rel)
            text_file_path = self.resource_manager.get_external_path(text_file_rel)
            if not os.path.exists(text_file_path):
                raise RuntimeError(f"文本文件{key}不存在，无法读取")
            with open(text_file_path, 'r', encoding='utf-8') as file:
                logging.info(f"处理文件：{text_file_path}")
                text_list = []
                for line in file.readlines():
                    id, _, text = line.partition('=')
                    segmented = ' '.join(jieba.cut(text))
                    text_list.append((id, text, segmented))
            with sqlite3.connect(self.db_path) as conn:
                logging.info(f"插入数据到表：text_{key}")
                cursor = conn.cursor()
                cursor.execute(f"DELETE FROM text_{key}")
                cursor.executemany(f'''
                    INSERT OR REPLACE INTO text_{key} (text_id, raw_text, content)
                    VALUES (?, ?, ?)
                ''', text_list)
    
    def full_refresh(self):
        logging.info('完整刷新开始')
        logging.info('开始建表')
        self.create_db()
        logging.info('开始处理数据')
        self.refresh_db()
        
    def _fuzzy_search(
        self, 
        db, 
        keyword, 
        threshold: float = 0.6
    ) -> list[tuple[str, float]]:
        logging.info(f"模糊搜索{keyword} - 使用数据库{db}")
        ret = []
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(f"SELECT text_id, raw_text from text_{db}")
            all_texts = cursor.fetchall()
            for text_id, raw_text in all_texts:
                similarity = fuzz.partial_ratio(keyword.lower(), raw_text.lower()) / 100
                # similarity = self.fuzzy.get_score(keyword, raw_text)
                logging.debug(f"模糊匹配：{keyword} {raw_text} {similarity}")
                if similarity >= threshold:
                    ret.append((text_id, -similarity))
                    logging.info(f"模糊匹配：{similarity} {raw_text}")
        return ret

    def search(
        self, 
        keyword: str, 
        limit: int = 100, 
        use_db: list | str = ['cn', 'en'], 
        display_rsui: bool = False, 
        max_length: int | None = None,
        fuzzy_search: bool = False,
    ):
        
        def escape_fts5(text):
            # FTS5 特殊字符需要用双引号包裹或转义
            special_chars = ['"', '-', '(', ')', '*', ':']
            for char in special_chars:
                text = text.replace(char, ' ')  # 替换为空格
            return text.strip()
        
        start = time.time()
        seg_keyword = ' '.join(jieba.cut(escape_fts5(keyword)))
        logging.info(f"开始搜索: {seg_keyword}")
        if isinstance(use_db, str):
            use_db = [use_db]
        
        result = []  # 改为list存储(text_id, rank)
        for db in use_db:
            logging.info(f"在数据库{db}里搜索")
            with sqlite3.connect(self.db_path) as conn:
                if max_length is not None:
                    cursor = conn.execute(
                        f"SELECT text_id, rank-1 FROM text_{db} "  # 添加rank
                        f"WHERE content MATCH ? AND LENGTH(raw_text) < ? "
                        f"ORDER BY rank "  # 按相关性排序
                        f"LIMIT ?",
                        (seg_keyword, max_length, limit)
                    )
                else:
                    cursor = conn.execute(
                        f"SELECT text_id, rank-1 FROM text_{db} "
                        f"WHERE content MATCH ? "
                        f"ORDER BY rank "  # rank值越小越相关
                        f"LIMIT ?",
                        (seg_keyword, limit)
                    )
                cache = cursor.fetchall()
                result.extend(cache)
                
        logging.debug(result)
                
        if fuzzy_search:
            for db in use_db:
                cache = self._fuzzy_search(db, keyword)
                result += cache
        
        result_dict = {}
        for text_id, rank in result:
            if text_id not in result_dict or rank < result_dict[text_id]:
                result_dict[text_id] = rank
        
        weighted_ids = [(tid, trank) for tid, trank in result_dict.items()]
        weighted_ids.sort(key=lambda x: x[1])
        ids = [tid[0] for tid in weighted_ids][:limit]
        
        logging.info(f"搜索完成,返回{len(ids)}项,耗时{time.time() - start:.3f}s")
        return ids, self.__generate_result_sqlite(ids, keyword, display_rsui)
 
    def __generate_result_sqlite(self, text_ids: list, keyword: str, display_rsui: bool, ):
        # NOTE 这块display的实现有点尴尬，但是不影响使用
        if display_rsui and 'rsui' in self.used_text:
            use_db = self.used_text
        else:
            use_db = ['en', 'cn']
        if not text_ids:
            return {}
        
        ret_data = {}
        with sqlite3.connect(self.db_path) as conn:
            placeholders = ','.join('?' * len(text_ids))
            for db in use_db:
                cursor = conn.execute(
                    f"SELECT text_id, raw_text FROM text_{db} WHERE text_id IN ({placeholders})",
                    text_ids
                )
                results = cursor.fetchall()
                for text_id, raw_text in results:
                    if ret_data.get(text_id) is None:
                        ret_data[text_id] = dict()
                    ret_data[text_id][db] = self.highlight(raw_text.replace('\n', ' '), keyword)
        
        return ret_data
    
    def contains_chinese(self, text):
        """
        检查字符串是否包含中文字符
        """
        for char in text:
            if '\u4e00' <= char <= '\u9fff':
                return True
        return False

    def highlight(self, text, keyword):
        display_length = self.display_length // 2 if self.contains_chinese(text) else self.display_length
        text = escape(text)
        pattern = re.compile(re.escape(keyword), re.IGNORECASE)
        hl_text = pattern.sub(lambda m: f'<b>{m.group()}</b>', text)
        if display_length is None or len(text) < display_length:
            return hl_text
        
        result = re.match(r"(.*?)(<b>.*</b>)(.*?)", hl_text)
        if result is None: 
            return hl_text[:display_length] + '...'
        start, content, _ = result.groups()
        raw_content = content.replace('<b>', '').replace('</b>', '')
        
        if len(start + raw_content) > display_length:
            if len(start) > display_length:
                return start[:display_length] + '...'
            return f"{start}<b>{raw_content[:(display_length-len(start))]}</b>..."

        return hl_text[:display_length] + '...'
    
    def get_full_text(self, text_id: str, use_rsui: bool = False):
        ret_data = dict()
        with sqlite3.connect(self.db_path) as conn:
            for db in self.used_text:
                cursor = conn.execute(
                    f"SELECT raw_text FROM text_{db} WHERE text_id = ?",
                    (text_id,)
                )
                ret_data[db] = escape(cursor.fetchone()[0])
        
        return ret_data
