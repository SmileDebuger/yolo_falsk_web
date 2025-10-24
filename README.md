# Flask集成YOLO系列算法

## 项目简介

这是一个基于Flask框架集成YOLO目标检测算法的Web应用示例，经过全面重构优化，采用模块化设计，提供了更好的代码结构、错误处理和扩展性。

## 🚀 新版本特性

- **模块化架构** - 将原单文件重构为多模块设计
- **配置管理** - 集中化配置管理，易于维护
- **RESTful API** - 提供JSON API接口，支持程序化调用
- **错误处理** - 完善的异常处理和日志记录
- **文件管理** - 自动文件清理和安全处理
- **健康监控** - 应用状态检查接口

## 📁 项目结构

```
yolo_flask/
├── app.py              # Flask主应用文件
├── config.py           # 配置管理模块
├── detector.py         # YOLO检测服务类
├── utils_app.py        # 工具函数模块
├── logs/              # 日志文件目录
├── static/            # 静态文件
│   └── images/        # 检测结果图片
├── templates/         # HTML模板
│   ├── index.html     # 主页模板
│   ├── result.html    # 结果页面模板
│   └── error.html     # 错误页面模板
└── uploads/           # 上传文件临时目录
    ├── images/        # 图片上传目录
    └── videos/        # 视频上传目录
```

## 🛠️ 安装步骤

### 1. 准备YOLO环境

- 下载YOLOV5仓库代码：https://github.com/ultralytics/yolov5
- 将本项目代码复制到YOLOV5项目目录下

### 2. 创建虚拟环境

```shell
# 创建Python 3.9虚拟环境
conda create -n yolo_flask python=3.9
conda activate yolo_flask
```

### 3. 安装依赖

```shell
# 安装YOLO依赖
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 安装Flask相关依赖
pip install flask werkzeug -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 4. 运行应用

```shell
python app.py
```

访问地址：http://127.0.0.1:5000

## 📡 API接口

### 1. Web界面检测

- **URL**: `/`
- **方法**: GET
- **描述**: 访问Web界面进行图片上传检测

### 2. API检测接口

- **URL**: `/api/detect`
- **方法**: POST
- **参数**: 
  - `file`: 图片文件 (multipart/form-data)
- **响应**: JSON格式检测结果

```json
{
    "success": true,
    "message": "检测完成",
    "results": [
        {
            "filename": "result_image.jpg",
            "url": "/static/images/exp/result_image.jpg"
        }
    ],
    "detection_count": 5,
    "timestamp": "2024-01-01 12:00:00"
}
```

### 3. 健康检查

- **URL**: `/health`
- **方法**: GET
- **描述**: 检查应用运行状态

### 4. 文件清理

- **URL**: `/cleanup`
- **方法**: POST
- **描述**: 清理临时上传文件

## 🔍 使用示例

### Web界面使用

1. 访问 http://127.0.0.1:5000
2. 选择图片文件上传
3. 点击检测按钮
4. 查看检测结果

### API调用示例

```python
import requests

# 上传图片进行检测
url = 'http://127.0.0.1:5000/api/detect'
files = {'file': open('test_image.jpg', 'rb')}
response = requests.post(url, files=files)
result = response.json()

print(f"检测结果: {result}")
```

### cURL调用示例

```bash
curl -X POST -F "file=@test_image.jpg" http://127.0.0.1:5000/api/detect
```

## 📊 日志系统

应用提供完整的日志记录功能：

- **日志位置**: `logs/app.log`
- **日志级别**: INFO, WARNING, ERROR
- **日志内容**: 请求处理、错误信息、性能统计

## 🛡️ 安全特性

- **文件类型验证** - 只允许图片和视频文件
- **文件大小限制** - 最大16MB文件上传
- **安全文件名** - 自动处理文件名安全性
- **自动清理** - 定期清理临时文件
- **错误处理** - 完善的异常捕获机制

## 🚀 性能优化

- **模型预加载** - 应用启动时预加载YOLO模型
- **批量处理** - 支持批量检测结果返回
- **资源管理** - 自动清理临时文件释放存储空间
- **异步处理** - 支持非阻塞文件处理

## 🔧 扩展开发

### 添加新的检测模型

1. 在 `config.py` 中添加新模型配置
2. 在 `detector.py` 中扩展检测逻辑
3. 更新API接口支持模型选择

## 🐛 故障排除

### 常见问题

1. **模型加载失败**
   - 检查模型文件路径是否正确
   - 确认模型文件完整性

2. **文件上传失败**
   - 检查文件大小是否超过限制
   - 确认文件格式是否支持

3. **检测结果不显示**
   - 检查静态文件目录权限
   - 查看日志文件错误信息

### 日志查看

```bash
# 查看应用日志
tail -f logs/app.log

# 查看错误日志
grep "ERROR" logs/app.log
```

## 📚 参考资料

- [YOLOv5官方仓库](https://github.com/ultralytics/yolov5)
- [Flask官方文档](https://flask.palletsprojects.com/)
- [PyTorch官方文档](https://pytorch.org/docs/)

## 🤝 贡献指南

欢迎提交Issue和Pull Request来改进这个项目！

## 📄 许可证

本项目采用MIT许可证，详见LICENSE文件。

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给个 Star 支持一下！**

Made with ❤️ by SmileDebuger

</div>