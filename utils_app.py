"""
应用工具函数模块
提供Flask应用所需的工具函数
"""
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, Union
from werkzeug.utils import secure_filename

from flask import current_app

from config import config


class FileManager:
    """文件管理类"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def validate_file_type(self, filename: str, allowed_extensions: Optional[set] = None) -> bool:
        """
        验证文件类型是否允许
        
        Args:
            filename: 文件名
            allowed_extensions: 允许的文件扩展名集合
            
        Returns:
            是否允许该文件类型
        """
        if allowed_extensions is None:
            allowed_extensions = config.app.allowed_extensions
        
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in allowed_extensions
    
    def generate_unique_filename(self, original_filename: str) -> str:
        """
        生成唯一的文件名
        
        Args:
            original_filename: 原始文件名
            
        Returns:
            唯一的文件名
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        extension = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
        
        if extension:
            return f"{timestamp}_{unique_id}.{extension}"
        else:
            return f"{timestamp}_{unique_id}"
    
    def save_uploaded_file(self, file, subdirectory: str = '') -> Optional[Path]:
        """
        保存上传的文件
        
        Args:
            file: 上传的文件对象
            subdirectory: 子目录名称
            
        Returns:
            保存的文件路径，失败时返回None
        """
        try:
            if not file or file.filename == '':
                self.logger.warning("没有选择文件")
                return None
            
            if not self.validate_file_type(file.filename):
                self.logger.warning(f"不支持的文件类型: {file.filename}")
                return None
            
            # 创建保存目录
            save_dir = config.uploads_path / subdirectory
            save_dir.mkdir(parents=True, exist_ok=True)
            
            # 生成安全的文件名
            filename = secure_filename(file.filename)
            unique_filename = self.generate_unique_filename(filename)
            file_path = save_dir / unique_filename
            
            # 保存文件
            file.save(str(file_path))
            self.logger.info(f"文件保存成功: {file_path}")
            
            return file_path
            
        except Exception as e:
            self.logger.error(f"文件保存失败: {e}")
            return None
    
    def cleanup_old_files(self, directory: Path, max_age_hours: int = 24) -> int:
        """
        清理旧文件
        
        Args:
            directory: 要清理的目录
            max_age_hours: 文件最大保留时间（小时）
            
        Returns:
            删除的文件数量
        """
        try:
            if not directory.exists():
                return 0
            
            deleted_count = 0
            current_time = datetime.now().timestamp()
            max_age_seconds = max_age_hours * 3600
            
            for file_path in directory.rglob('*'):
                if file_path.is_file():
                    file_age = current_time - file_path.stat().st_mtime
                    if file_age > max_age_seconds:
                        file_path.unlink()
                        deleted_count += 1
                        self.logger.info(f"清理旧文件: {file_path}")
            
            self.logger.info(f"清理完成，共删除 {deleted_count} 个文件")
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"文件清理失败: {e}")
            return 0
    
    def get_result_url(self, result_path: Path) -> Optional[str]:
        """
        获取结果文件的URL
        
        Args:
            result_path: 结果文件路径
            
        Returns:
            结果文件的URL，失败时返回None
        """
        try:
            if not result_path or not result_path.exists():
                return None
            
            # 获取相对于结果目录的相对路径
            relative_path = result_path.relative_to(config.results_path)
            # 确保使用正斜杠（适配Web URL，兼容Windows）
            url_path = str(relative_path).replace('\\', '/')
            return f"/{config.app.results_url_prefix}/{url_path}"
            
        except Exception as e:
            self.logger.error(f"获取结果URL失败: {e}")
            return None


def setup_logging():
    """设置日志配置（防止重复初始化）"""
    # 检查是否已经设置了日志处理器
    root_logger = logging.getLogger()
    if root_logger.handlers:
        # 已经初始化，跳过
        return
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(config.logs_path / 'app.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )


def validate_image_file(file, max_size_mb: int = None) -> Tuple[bool, str]:
    """
    验证图片文件（增强版）
    
    Args:
        file: 文件对象
        max_size_mb: 最大文件大小（MB），None则使用配置中的值
        
    Returns:
        (是否有效, 错误消息)
    """
    if not file or file.filename == '':
        return False, "请选择文件"
    
    # 使用全局 file_manager 实例（避免重复创建）
    if not file_manager.validate_file_type(file.filename):
        return False, f"不支持的文件类型。支持的类型: {', '.join(config.app.allowed_extensions)}"
    
    # 验证文件大小（在内存中检查，避免保存后才发现超限）
    max_size = (max_size_mb or config.app.max_upload_size_mb) * 1024 * 1024
    file.seek(0, 2)  # 移动到文件末尾
    file_size = file.tell()
    file.seek(0)  # 重置文件指针
    
    if file_size > max_size:
        size_mb = file_size / (1024 * 1024)
        return False, f"文件过大 ({size_mb:.2f}MB)，最大允许 {max_size_mb or config.app.max_upload_size_mb}MB"
    
    return True, ""


def create_directories():
    """创建必要的目录"""
    directories = [
        config.uploads_path,
        config.results_path,
        config.logs_path,
        config.uploads_path / 'images',
        config.uploads_path / 'videos',
        config.results_path / 'images',
        config.results_path / 'videos',
        # 添加原图展示目录
        config.static_path / 'images',
        config.static_path / 'images' / 'original'
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


def format_response(success: bool, message: str, data: Optional[dict] = None) -> dict:
    """
    格式化API响应
    
    Args:
        success: 是否成功
        message: 消息内容
        data: 响应数据
        
    Returns:
        格式化的响应字典
    """
    response = {
        'success': success,
        'message': message,
        'timestamp': datetime.now().isoformat()
    }
    
    if data is not None:
        response['data'] = data
    
    return response


def get_file_size_mb(file_path: Union[str, Path]) -> float:
    """
    获取文件大小（MB）
    
    Args:
        file_path: 文件路径
        
    Returns:
        文件大小（MB）
    """
    try:
        file_path = Path(file_path)
        if file_path.exists():
            return file_path.stat().st_size / (1024 * 1024)
        return 0.0
    except Exception:
        return 0.0


# 全局文件管理器实例
file_manager = FileManager()