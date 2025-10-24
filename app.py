"""
Flask YOLO检测应用主文件
优化后的模块化结构
"""
from flask import Flask, render_template, request, jsonify
import os
import logging
from datetime import datetime
from pathlib import Path

# 导入自定义模块
from config import config
from detector import detector
from utils_app import file_manager, setup_logging, create_directories, validate_image_file, format_response

# 初始化应用
app = Flask(__name__, 
           static_folder=config.app.static_folder,
           template_folder=config.app.template_folder)
app.config['MAX_CONTENT_LENGTH'] = config.app.max_upload_size_mb * 1024 * 1024

# 设置日志
setup_logging()
logger = logging.getLogger(__name__)

# 创建必要目录
create_directories()

# 预加载模型
if not detector.load_model():
    logger.error("模型预加载失败，应用可能无法正常工作")
else:
    logger.info("YOLO模型预加载成功")


@app.route("/")
def index():
    """首页"""
    return render_template('index.html')


@app.route("/api/detect", methods=['POST'])
def api_detect():
    """
    API检测接口
    返回JSON格式的检测结果
    """
    try:
        if 'file' not in request.files:
            return jsonify(format_response(False, "请选择文件")), 400
        
        file = request.files['file']
        
        # 验证文件
        is_valid, error_msg = validate_image_file(file)
        if not is_valid:
            return jsonify(format_response(False, error_msg)), 400
        
        # 保存上传的文件
        file_path = file_manager.save_uploaded_file(file, 'images')
        if not file_path:
            return jsonify(format_response(False, "文件保存失败")), 500
        
        logger.info(f"开始处理文件: {file_path}")
        
        # 执行检测
        result_dir = detector.detect(file_path)
        
        if not result_dir:
            # 清理上传的文件
            file_path.unlink(missing_ok=True)
            return jsonify(format_response(False, "目标检测失败")), 500
        
        # 获取结果文件
        result_files = list(result_dir.glob('*'))
        if not result_files:
            # 清理上传的文件和结果目录
            file_path.unlink(missing_ok=True)
            import shutil
            shutil.rmtree(result_dir, ignore_errors=True)
            return jsonify(format_response(False, "未生成检测结果")), 500
        
        # 获取结果URL
        result_urls = []
        for result_file in result_files:
            if result_file.is_file():
                result_url = file_manager.get_result_url(result_file)
                if result_url:
                    result_urls.append(result_url)
        
        # 清理上传的文件
        file_path.unlink(missing_ok=True)
        
        if not result_urls:
            import shutil
            shutil.rmtree(result_dir, ignore_errors=True)
            return jsonify(format_response(False, "无法生成结果URL")), 500
        
        logger.info(f"检测完成，生成 {len(result_urls)} 个结果文件")
        
        return jsonify(format_response(
            True, 
            "检测成功", 
            {
                'result_urls': result_urls,
                'result_count': len(result_urls),
                'original_filename': file.filename
            }
        ))
        
    except Exception as e:
        logger.error(f"API检测异常: {e}")
        return jsonify(format_response(False, f"服务器内部错误: {str(e)}")), 500


@app.route("/detect", methods=['POST'])
def detect():
    """
    网页检测接口
    返回HTML页面显示检测结果
    """
    try:
        if 'file' not in request.files:
            return render_template('error.html', error_message="请选择文件"), 400
        
        file = request.files['file']
        
        # 验证文件
        is_valid, error_msg = validate_image_file(file)
        if not is_valid:
            return render_template('error.html', error_message=error_msg), 400
        
        # 保存上传的文件
        file_path = file_manager.save_uploaded_file(file, 'images')
        if not file_path:
            return render_template('error.html', error_message="文件保存失败"), 500
        
        # 同时保存原图到static目录以便展示
        import shutil
        original_filename = file_manager.generate_unique_filename(file.filename)
        static_original_path = config.static_path / 'images' / 'original' / original_filename
        static_original_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file_path, static_original_path)
        
        # 获取原图URL - 使用Flask的静态文件路由
        from flask import url_for
        original_relative_path = static_original_path.relative_to(config.static_path)
        original_url = url_for('static', filename=str(original_relative_path))
        
        logger.info(f"开始处理文件: {file_path}")
        
        # 执行检测
        result_dir = detector.detect(file_path)
        
        if not result_dir:
            # 清理上传的文件和原图
            file_path.unlink(missing_ok=True)
            static_original_path.unlink(missing_ok=True)
            return render_template('error.html', error_message="目标检测失败"), 500
        
        # 获取结果文件
        result_files = list(result_dir.glob('*'))
        if not result_files:
            # 清理上传的文件、原图和结果目录
            file_path.unlink(missing_ok=True)
            static_original_path.unlink(missing_ok=True)
            import shutil
            shutil.rmtree(result_dir, ignore_errors=True)
            return render_template('error.html', error_message="未生成检测结果"), 500
        
        # 获取第一个结果文件的URL
        result_url = None
        for result_file in result_files:
            if result_file.is_file():
                result_url = file_manager.get_result_url(result_file)
                if result_url:
                    break
        
        # 清理上传的文件（保留static中的原图）
        file_path.unlink(missing_ok=True)
        
        if not result_url:
            static_original_path.unlink(missing_ok=True)
            import shutil
            shutil.rmtree(result_dir, ignore_errors=True)
            return render_template('error.html', error_message="无法生成结果URL"), 500
        
        logger.info(f"检测完成，原图URL: {original_url}, 结果URL: {result_url}")
        
        return render_template('result.html', original_url=original_url, result_url=result_url)
        
    except Exception as e:
        logger.error(f"网页检测异常: {e}")
        return render_template('error.html', error_message=f"服务器内部错误: {str(e)}"), 500

@app.route("/health")
def health_check():
    """健康检查接口"""
    return jsonify({
        'status': 'healthy',
        'message': 'YOLO Flask应用运行正常',
        'timestamp': datetime.now().isoformat()
    })


@app.route("/cleanup", methods=['POST'])
def cleanup_files():
    """清理旧文件接口"""
    try:
        deleted_count = file_manager.cleanup_old_files(config.uploads_path)
        deleted_count += file_manager.cleanup_old_files(config.results_path)
        
        return jsonify({
            'success': True,
            'message': f'清理完成，共删除 {deleted_count} 个文件',
            'deleted_count': deleted_count
        })
    except Exception as e:
        logger.error(f"文件清理失败: {e}")
        return jsonify({
            'success': False,
            'message': f'文件清理失败: {str(e)}'
        }), 500


@app.errorhandler(404)
def not_found(error):
    """404错误处理"""
    return render_template('error.html', error_message="页面不存在"), 404


@app.errorhandler(500)
def internal_error(error):
    """500错误处理"""
    return render_template('error.html', error_message="服务器内部错误"), 500


@app.errorhandler(413)
def too_large(error):
    """文件过大错误处理"""
    return render_template('error.html', 
                         error_message=f"文件过大，最大允许 {config.app.max_upload_size_mb}MB"), 413


if __name__ == "__main__":
    # 启动应用
    logger.info(f"启动YOLO Flask应用，监听地址: {config.app.host}:{config.app.port}")
    logger.info(f"上传文件大小限制: {config.app.max_upload_size_mb}MB")
    logger.info(f"允许的文件类型: {', '.join(config.app.allowed_extensions)}")
    
    app.run(
        host=config.app.host, 
        port=config.app.port,
        debug=config.app.debug,
        threaded=config.app.threaded
    )
