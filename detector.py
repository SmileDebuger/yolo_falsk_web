"""
YOLO检测服务模块
封装YOLO检测逻辑，提供统一的检测接口
"""
import logging
import platform
import sys
from pathlib import Path
from typing import Optional, Union
import torch
import cv2

# 添加YOLO路径
FILE = Path(__file__).resolve()
ROOT = FILE.parents[0]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from models.common import DetectMultiBackend
from utils.dataloaders import IMG_FORMATS, VID_FORMATS, LoadImages, LoadScreenshots, LoadStreams
from utils.general import (
    LOGGER, Profile, check_file, check_img_size, check_imshow, 
    colorstr, increment_path, non_max_suppression, scale_boxes, 
    strip_optimizer, xyxy2xywh
)
from utils.plots import Annotator, colors, save_one_box
from utils.torch_utils import select_device, smart_inference_mode

from config import config, YOLOConfig


class YOLODetector:
    """YOLO检测器类"""
    
    def __init__(self, yolo_config: Optional[YOLOConfig] = None):
        """
        初始化YOLO检测器
        
        Args:
            yolo_config: YOLO配置对象，如果为None则使用默认配置
        """
        self.config = yolo_config or config.yolo
        self.model = None
        self.device = None
        self.logger = logging.getLogger(__name__)
        
    def load_model(self):
        """加载YOLO模型"""
        try:
            self.device = select_device(self.config.device)
            self.model = DetectMultiBackend(
                self.config.weights, 
                device=self.device, 
                dnn=self.config.dnn, 
                data=self.config.data, 
                fp16=self.config.half
            )
            self.logger.info(f"模型加载成功: {self.config.weights}")
            return True
        except Exception as e:
            self.logger.error(f"模型加载失败: {e}")
            return False
    
    @smart_inference_mode()
    def detect(self, source: Union[str, Path], save_dir: Optional[Path] = None) -> Optional[Path]:
        """
        执行目标检测
        
        Args:
            source: 输入源路径
            save_dir: 保存目录，如果为None则使用默认目录
            
        Returns:
            检测结果保存路径，失败时返回None
        """
        try:
            if self.model is None:
                if not self.load_model():
                    return None
            
            source = str(source)
            save_dir = save_dir or config.results_path
            
            # 检查输入源类型
            source_info = self._analyze_source(source)
            if not source_info['valid']:
                self.logger.error(f"无效的输入源: {source}")
                return None
            
            # 设置保存目录
            save_dir = increment_path(Path(save_dir) / 'exp', exist_ok=False)
            save_dir.mkdir(parents=True, exist_ok=True)
            
            # 执行检测
            return self._run_detection(source, save_dir, source_info)
            
        except Exception as e:
            self.logger.error(f"检测过程中发生错误: {e}")
            return None
    
    def _analyze_source(self, source: str) -> dict:
        """分析输入源类型"""
        is_file = Path(source).suffix[1:] in (IMG_FORMATS + VID_FORMATS)
        is_url = source.lower().startswith(('rtsp://', 'rtmp://', 'http://', 'https://'))
        webcam = source.isnumeric() or source.endswith('.streams') or (is_url and not is_file)
        screenshot = source.lower().startswith('screen')
        
        return {
            'valid': is_file or is_url or webcam or screenshot,
            'is_file': is_file,
            'is_url': is_url,
            'webcam': webcam,
            'screenshot': screenshot
        }
    
    def _run_detection(self, source: str, save_dir: Path, source_info: dict) -> Path:
        """执行检测的核心逻辑"""
        # 检查并下载URL文件
        if source_info['is_url'] and source_info['is_file']:
            source = check_file(source)
        
        # 检查图像尺寸
        stride, names, pt = self.model.stride, self.model.names, self.model.pt
        imgsz = check_img_size(self.config.imgsz, s=stride)
        
        # 创建数据加载器
        dataset = self._create_dataloader(source, imgsz, stride, pt, source_info)
        
        # 预热模型
        bs = len(dataset) if source_info['webcam'] else 1
        self.model.warmup(imgsz=(1 if pt or self.model.triton else bs, 3, *imgsz))
        
        # 执行推理
        self._process_detections(dataset, save_dir, imgsz, names, stride)
        
        return save_dir
    
    def _create_dataloader(self, source: str, imgsz: tuple, stride: int, pt: bool, source_info: dict):
        """创建数据加载器"""
        if source_info['webcam']:
            check_imshow(warn=True)
            return LoadStreams(source, img_size=imgsz, stride=stride, auto=pt, vid_stride=self.config.vid_stride)
        elif source_info['screenshot']:
            return LoadScreenshots(source, img_size=imgsz, stride=stride, auto=pt)
        else:
            return LoadImages(source, img_size=imgsz, stride=stride, auto=pt, vid_stride=self.config.vid_stride)
    
    def _process_detections(self, dataset, save_dir: Path, imgsz: tuple, names: dict, stride: int):
        """处理检测结果"""
        seen, windows, dt = 0, [], (Profile(), Profile(), Profile())
        vid_path, vid_writer = [None] * len(dataset), [None] * len(dataset)
        
        for path, im, im0s, vid_cap, s in dataset:
            # 预处理
            with dt[0]:
                im = torch.from_numpy(im).to(self.model.device)
                im = im.half() if self.model.fp16 else im.float()
                im /= 255
                if len(im.shape) == 3:
                    im = im[None]
            
            # 推理
            with dt[1]:
                visualize = increment_path(save_dir / Path(path).stem, mkdir=True) if self.config.visualize else False
                pred = self.model(im, augment=self.config.augment, visualize=visualize)
            
            # NMS
            with dt[2]:
                pred = non_max_suppression(
                    pred, self.config.conf_thres, self.config.iou_thres, 
                    self.config.classes, self.config.agnostic_nms, max_det=self.config.max_det
                )
            
            # 处理每张图片的检测结果
            self._process_single_detection(
                pred, path, im, im0s, vid_cap, s, save_dir, names, 
                dataset, seen, vid_path, vid_writer, windows, dt
            )
            seen += 1
        
        # 打印统计信息
        self._print_results(dt, seen, imgsz, save_dir)
    
    def _process_single_detection(self, pred, path, im, im0s, vid_cap, s, save_dir, names, 
                                dataset, seen, vid_path, vid_writer, windows, dt):
        """处理单张图片的检测结果"""
        for i, det in enumerate(pred):
            if hasattr(dataset, 'mode') and dataset.mode == 'stream':
                p, im0, frame = path[i], im0s[i].copy(), dataset.count
                s += f'{i}: '
            else:
                p, im0, frame = path, im0s.copy(), getattr(dataset, 'frame', 0)
            
            p = Path(p)
            save_path = str(save_dir / p.name)
            s += '%gx%g ' % im.shape[2:]
            
            annotator = Annotator(im0, line_width=self.config.line_thickness, example=str(names))
            
            if len(det):
                # 缩放边界框
                det[:, :4] = scale_boxes(im.shape[2:], det[:, :4], im0.shape).round()
                
                # 统计检测结果
                for c in det[:, 5].unique():
                    n = (det[:, 5] == c).sum()
                    s += f"{n} {names[int(c)]}{'s' * (n > 1)}, "
                
                # 绘制边界框
                for *xyxy, conf, cls in reversed(det):
                    c = int(cls)
                    label = None if self.config.hide_labels else (
                        names[c] if self.config.hide_conf else f'{names[c]} {conf:.2f}'
                    )
                    annotator.box_label(xyxy, label, color=colors(c, True))
            
            # 保存结果
            im0 = annotator.result()
            self._save_results(im0, save_path, dataset, vid_path, vid_writer, vid_cap, i)
            
            LOGGER.info(f"{s}{'' if len(det) else '(no detections), '}{dt[1].dt * 1E3:.1f}ms")
    
    def _save_results(self, im0, save_path, dataset, vid_path, vid_writer, vid_cap, i):
        """保存检测结果"""
        if dataset.mode == 'image':
            cv2.imwrite(save_path, im0)
        else:  # video or stream
            if vid_path[i] != save_path:
                vid_path[i] = save_path
                if isinstance(vid_writer[i], cv2.VideoWriter):
                    vid_writer[i].release()
                
                if vid_cap:
                    fps = vid_cap.get(cv2.CAP_PROP_FPS)
                    w = int(vid_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    h = int(vid_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                else:
                    fps, w, h = 30, im0.shape[1], im0.shape[0]
                
                save_path = str(Path(save_path).with_suffix('.mp4'))
                vid_writer[i] = cv2.VideoWriter(save_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (w, h))
            
            vid_writer[i].write(im0)
    
    def _print_results(self, dt, seen, imgsz, save_dir):
        """打印检测结果统计"""
        t = tuple(x.t / seen * 1E3 for x in dt)
        LOGGER.info(f'Speed: %.1fms pre-process, %.1fms inference, %.1fms NMS per image at shape {(1, 3, *imgsz)}' % t)
        LOGGER.info(f"Results saved to {colorstr('bold', save_dir)}")


# 全局检测器实例
detector = YOLODetector()