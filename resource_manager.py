import os
import sys
import shutil
from pathlib import Path
from typing import Union, Optional
import logging

APP_NAME_STRING = 'sc-cn-dict'

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ResourceManager:
    """
    资源管理类，处理PyInstaller打包程序的资源访问
    """
    
    def __init__(self, app_name: str = APP_NAME_STRING):
        """
        初始化资源管理器
        
        Args:
            app_name: 应用程序名称，用于创建外部数据目录
        """
        self.app_name = app_name
        self._base_path = self._get_base_path()
        self._is_frozen = getattr(sys, 'frozen', False)
        
        logger.info(f"资源管理器初始化:")
        logger.info(f"  - 应用名称: {app_name}")
        logger.info(f"  - 运行模式: {'打包模式(exe)' if self._is_frozen else '开发模式(.py)'}")
        logger.info(f"  - 基础路径: {self._base_path}")
    
    @staticmethod
    def _get_base_path() -> Path:
        """
        获取程序基础路径
        
        Returns:
            Path: 基础路径对象
        """
        if getattr(sys, 'frozen', False):
            # PyInstaller打包后的路径
            # sys._MEIPASS 是PyInstaller创建的临时文件夹
            if hasattr(sys, '_MEIPASS'):
                base_path = Path(sys._MEIPASS)
            else:
                base_path = Path(sys.executable).parent
        else:
            # 开发环境路径
            base_path = Path(__file__).parent
        
        return base_path
    
    def get_internal_path(self, relative_path: str) -> Path:
        """
        获取打包在exe内的资源路径
        
        Args:
            relative_path: 相对于程序根目录的路径
        
        Returns:
            Path: 资源的绝对路径
        
        Example:
            >>> rm = ResourceManager()
            >>> config_path = rm.get_internal_path('config/settings.json')
        """
        resource_path = self._base_path / relative_path
        
        if not resource_path.exists():
            logger.warning(f"内部资源不存在: {resource_path}")
        
        return resource_path
    
    def get_external_path(self, relative_path: str, location: str = "exe_dir") -> Path:
        """
        获取exe外部的数据路径（用户数据目录）
        
        Args:
            relative_path: 相对路径
            location: 外部位置类型
                - "user_data": 用户数据目录（AppData/Roaming或~/.local/share）
                - "exe_dir": exe所在目录
                - "current": 当前工作目录
                - "temp": 临时目录
        
        Returns:
            Path: 外部数据的绝对路径
        
        Example:
            >>> rm = ResourceManager()
            >>> log_path = rm.get_external_path('logs/app.log')
        """
        if location == "user_data":
            base_dir = self._get_user_data_dir()
        elif location == "exe_dir":
            if self._is_frozen:
                base_dir = Path(sys.executable).parent
            else:
                base_dir = Path(__file__).parent
        elif location == "current":
            base_dir = Path.cwd()
        elif location == "temp":
            import tempfile
            base_dir = Path(tempfile.gettempdir()) / self.app_name
        else:
            raise ValueError(f"未知的位置类型: {location}")
        
        external_path = base_dir / relative_path
        
        # 确保父目录存在
        external_path.parent.mkdir(parents=True, exist_ok=True)
        
        return external_path
    
    def _get_user_data_dir(self) -> Path:
        """
        获取用户数据目录（跨平台）
        
        Returns:
            Path: 用户数据目录路径
        """
        if sys.platform == "win32":
            # Windows: C:/Users/Username/AppData/Roaming/AppName
            base = Path(os.getenv('APPDATA', '~'))
        elif sys.platform == "darwin":
            # macOS: ~/Library/Application Support/AppName
            base = Path.home() / "Library" / "Application Support"
        else:
            # Linux: ~/.local/share/AppName
            base = Path.home() / ".local" / "share"
        
        app_dir = base / self.app_name
        app_dir.mkdir(parents=True, exist_ok=True)
        
        return app_dir
    
    def copy_internal_to_external(
        self,
        internal_relative_path: str,
        external_relative_path: Optional[str] = None,
        location: str = "user_data",
        overwrite: bool = False
    ) -> bool:
        """
        将内部资源复制到外部
        
        Args:
            internal_relative_path: 内部资源的相对路径
            external_relative_path: 外部路径（None则使用相同路径）
            location: 外部位置类型
            overwrite: 是否覆盖已存在的文件
        
        Returns:
            bool: 复制成功返回True
        
        Example:
            >>> rm = ResourceManager()
            >>> rm.copy_internal_to_external('config/default.json', 'config/settings.json')
        """
        if external_relative_path is None:
            external_relative_path = internal_relative_path
        
        internal_path = self.get_internal_path(internal_relative_path)
        external_path = self.get_external_path(external_relative_path, location)
        
        try:
            # 检查源文件是否存在
            if not internal_path.exists():
                logger.error(f"源文件不存在: {internal_path}")
                return False
            
            # 检查目标文件是否已存在
            if external_path.exists() and not overwrite:
                logger.info(f"目标文件已存在，跳过复制: {external_path}")
                return True
            
            # 确保目标目录存在
            external_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 复制文件或目录
            if internal_path.is_file():
                shutil.copy2(internal_path, external_path)
                logger.info(f"文件复制成功: {internal_path} -> {external_path}")
            elif internal_path.is_dir():
                if external_path.exists():
                    shutil.rmtree(external_path)
                shutil.copytree(internal_path, external_path)
                logger.info(f"目录复制成功: {internal_path} -> {external_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"复制资源时出错: {e}")
            return False
    
    def ensure_external_resource(
        self,
        internal_relative_path: str,
        external_relative_path: Optional[str] = None,
        location: str = "user_data"
    ) -> Path:
        """
        确保外部资源存在，不存在则从内部复制
        
        Args:
            internal_relative_path: 内部资源的相对路径
            external_relative_path: 外部路径（None则使用相同路径）
            location: 外部位置类型
        
        Returns:
            Path: 外部资源路径
        
        Example:
            >>> rm = ResourceManager()
            >>> config = rm.ensure_external_resource('config/settings.json')
        """
        if external_relative_path is None:
            external_relative_path = internal_relative_path
        
        external_path = self.get_external_path(external_relative_path, location)
        
        if not external_path.exists():
            logger.info(f"外部资源不存在，从内部复制: {external_path}")
            self.copy_internal_to_external(
                internal_relative_path,
                external_relative_path,
                location,
                overwrite=False
            )
        
        return external_path
    
    def batch_copy_resources(
        self,
        resource_mapping: dict,
        location: str = "user_data",
        overwrite: bool = False
    ) -> dict:
        """
        批量复制资源
        
        Args:
            resource_mapping: 资源映射字典 {内部路径: 外部路径}
            location: 外部位置类型
            overwrite: 是否覆盖
        
        Returns:
            dict: 复制结果 {路径: 是否成功}
        
        Example:
            >>> rm = ResourceManager()
            >>> results = rm.batch_copy_resources({
            ...     'config/default.json': 'config/settings.json',
            ...     'data/template.xlsx': 'data/template.xlsx'
            ... })
        """
        results = {}
        
        for internal_path, external_path in resource_mapping.items():
            success = self.copy_internal_to_external(
                internal_path,
                external_path,
                location,
                overwrite
            )
            results[internal_path] = success
        
        return results
    
    def get_exe_dir(self) -> Path:
        """
        获取exe所在目录（或开发时的脚本目录）
        
        Returns:
            Path: exe目录路径
        """
        if self._is_frozen:
            return Path(sys.executable).parent
        else:
            return Path(__file__).parent
    
    def is_frozen(self) -> bool:
        """
        检查是否在打包环境中运行
        
        Returns:
            bool: 打包环境返回True
        """
        return self._is_frozen
    
    def list_internal_resources(self, directory: str = "") -> list:
        """
        列出内部资源目录中的所有文件
        
        Args:
            directory: 要列出的目录（相对路径）
        
        Returns:
            list: 文件路径列表
        """
        internal_dir = self.get_internal_path(directory)
        
        if not internal_dir.exists() or not internal_dir.is_dir():
            logger.warning(f"目录不存在或不是目录: {internal_dir}")
            return []
        
        files = []
        for item in internal_dir.rglob('*'):
            if item.is_file():
                relative_path = item.relative_to(internal_dir)
                files.append(str(relative_path))
        
        return files
    
    def cleanup_external_data(self, location: str = "exe_dir") -> bool:
        """
        清理外部数据目录
        
        Args:
            location: 外部位置类型
        
        Returns:
            bool: 清理成功返回True
        """
        try:
            if location == "user_data":
                data_dir = self._get_user_data_dir()
            elif location == "exe_dir":
                data_dir = self.get_exe_dir()
            else:
                logger.error(f"不支持清理位置: {location}")
                return False
            
            if data_dir.exists():
                shutil.rmtree(data_dir)
                logger.info(f"清理成功: {data_dir}")
                return True
            
            return True
            
        except Exception as e:
            logger.error(f"清理失败: {e}")
            return False


# 便捷函数
_default_manager = None

def get_resource_manager(app_name: str = APP_NAME_STRING) -> ResourceManager:
    """
    获取默认的资源管理器实例（单例模式）
    
    Args:
        app_name: 应用程序名称
    
    Returns:
        ResourceManager: 资源管理器实例
    """
    global _default_manager
    if _default_manager is None:
        _default_manager = ResourceManager(app_name)
    return _default_manager


# 使用示例和测试代码
if __name__ == "__main__":
    # 创建资源管理器
    rm = ResourceManager(app_name="TestApp")
    
    print("\n=== 资源管理器测试 ===\n")
    
    # 1. 测试获取内部路径
    print("1. 获取内部路径:")
    internal_config = rm.get_internal_path("config/settings.json")
    print(f"   内部配置文件: {internal_config}")
    
    # 2. 测试获取外部路径
    print("\n2. 获取外部路径:")
    external_log = rm.get_external_path("app.log", location="user_data")
    print(f"   外部日志文件: {external_log}")
    
    # exe_dir_data = rm.get_external_path("data/user.db", location="exe_dir")
    # print(f"   exe目录数据: {exe_dir_data}")
    
    # 3. 测试创建示例文件并复制
    print("\n3. 测试复制资源:")
    
    # 创建示例内部文件
    test_internal = rm.get_internal_path("test_data.txt")
    test_internal.parent.mkdir(parents=True, exist_ok=True)
    test_internal.write_text("这是测试数据", encoding='utf-8')
    print(f"   创建测试文件: {test_internal}")
    
    # 复制到外部
    success = rm.copy_internal_to_external("test_data.txt", "backup/test_data.txt")
    print(f"   复制结果: {'成功' if success else '失败'}")
    
    # 4. 测试确保资源存在
    print("\n4. 确保资源存在:")
    ensured_path = rm.ensure_external_resource("test_data.txt", "config/test.txt")
    print(f"   确保的资源路径: {ensured_path}")
    
    # 5. 测试批量复制
    print("\n5. 批量复制资源:")
    results = rm.batch_copy_resources({
        "test_data.txt": "batch/file1.txt",
        "test_data.txt": "batch/file2.txt"
    })
    for path, success in results.items():
        print(f"   {path}: {'成功' if success else '失败'}")
    
    # 6. 显示环境信息
    print("\n6. 环境信息:")
    print(f"   运行模式: {'打包模式' if rm.is_frozen() else '开发模式'}")
    print(f"   exe目录: {rm.get_exe_dir()}")
    print(f"   用户数据目录: {rm._get_user_data_dir()}")
    
    print("\n=== 测试完成 ===")
