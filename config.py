"""
配置管理模块
集中管理应用配置和YOLO检测参数
"""
import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Tuple, Union


@dataclass
class YOLOConfig:
    """YOLO检测配置类"""
    weights: str = 'yolov5s.pt'
    data: Optional[str] = None
    imgsz: Tuple[int, int] = (640, 640)
    conf_thres: float = 0.25
    iou_thres: float = 0.45
    max_det: int = 1000
    device: str = ''
    save_txt: bool = False
    save_conf: bool = False
    save_crop: bool = False
    nosave: bool = False
    classes: Optional[list] = None
    agnostic_nms: bool = False
    augment: bool = False
    visualize: bool = False
    update: bool = False
    line_thickness: int = 3
    hide_labels: bool = False
    hide_conf: bool = False
    half: bool = False
    dnn: bool = False
    vid_stride: int = 1


@dataclass
class AppConfig:
    """Flask应用配置类"""
    host: str = "0.0.0.0"
    port: int = 5000
    debug: bool = False
    # Flask的最大请求体长度（字节）
    max_content_length: int = 16 * 1024 * 1024  # 16MB
    # 以MB为单位的上传大小配置，供应用显示与计算使用
    max_upload_size_mb: int = 16
    # 是否启用多线程运行
    threaded: bool = True
    upload_folder: str = 'uploads'
    static_folder: str = 'static'
    template_folder: str = 'templates'
    # 结果文件URL前缀，用于生成可访问的结果文件URL
    results_url_prefix: str = 'static/images'
    allowed_extensions: set = None
    
    def __post_init__(self):
        if self.allowed_extensions is None:
            self.allowed_extensions = {
                'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff',
                'mp4', 'avi', 'mov', 'mkv', 'flv', 'wmv'
            }
        # 同步max_content_length与max_upload_size_mb两个字段的值
        if self.max_content_length:
            # 根据字节长度计算MB
            self.max_upload_size_mb = max(self.max_content_length // (1024 * 1024), 1)
        else:
            # 根据MB长度计算字节长度
            self.max_content_length = self.max_upload_size_mb * 1024 * 1024


class Config:
    """主配置类"""
    
    def __init__(self):
        # 项目根目录
        self.ROOT = Path(__file__).resolve().parent
        
        # YOLO配置
        self.yolo = YOLOConfig()
        self.yolo.data = str(self.ROOT / 'data/coco128.yaml')
        
        # Flask应用配置
        self.app = AppConfig()
        
        # 目录配置
        self.setup_directories()
    
    def setup_directories(self):
        """设置必要的目录"""
        self.uploads_dir = self.ROOT / self.app.upload_folder
        self.static_dir = self.ROOT / self.app.static_folder
        self.results_dir = self.static_dir / 'images'
        self.logs_dir = self.ROOT / 'logs'
        
        # 创建目录
        for directory in [self.uploads_dir, self.static_dir, self.results_dir, self.logs_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    @property
    def upload_path(self) -> Path:
        """上传文件路径（旧命名，兼容）"""
        return self.uploads_dir
    
    @property
    def uploads_path(self) -> Path:
        """上传文件路径（新命名，供其他模块使用）"""
        return self.uploads_dir
    
    @property
    def results_path(self) -> Path:
        """结果保存路径"""
        return self.results_dir
    
    @property
    def logs_path(self) -> Path:
        """日志保存路径"""
        return self.logs_dir
    
    @property
    def static_path(self) -> Path:
        """静态文件路径"""
        return self.static_dir


# 全局配置实例
config = Config()