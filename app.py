#!/usr/bin/env python3
"""
PaddlePaddle OCR v0.2.0 - 基于PaddleOCR 3.x优化版
优化特性：
- 快速启动，延迟初始化OCR服务
- 强制CPU模式，确保稳定性
- 基于最新PaddleOCR 3.x API和最佳实践
- 分离的模板和静态文件
- 使用推荐的predict方法替代弃用的ocr方法
"""

import os
import logging
import json
import threading
import time
import tempfile
import uuid
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)

# 全局状态
ocr_service = None
ocr_initializing = False
ocr_init_error = None

def create_app():
    """创建Flask应用"""
    app = Flask(__name__)
    
    # 基础配置
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
    
    # 启用CORS
    CORS(app)
    
    return app

def check_paddle_available():
    """检查PaddleOCR是否可用"""
    try:
        import paddle
        from paddleocr import PaddleOCR
        return True
    except ImportError as e:
        logging.warning(f"PaddleOCR不可用: {e}")
        return False

def get_file_size_mb(file_path):
    """获取文件大小（MB）"""
    try:
        if os.path.exists(file_path):
            size_bytes = os.path.getsize(file_path)
            return round(size_bytes / (1024 * 1024), 2)
        return 0
    except Exception:
        return 0

def get_directory_size_mb(dir_path):
    """获取目录总大小（MB）"""
    try:
        if not os.path.exists(dir_path):
            return 0
        
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(dir_path):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                try:
                    total_size += os.path.getsize(file_path)
                except (OSError, IOError):
                    continue
        return round(total_size / (1024 * 1024), 2)
    except Exception:
        return 0

def get_model_info():
    """获取模型版本和大小信息"""
    models_info = []
    
    try:
        home_dir = os.path.expanduser("~")
        
        # 确定当前使用的模型类型
        # PaddleOCR 3.x优先使用PaddleX模型，如果没有则使用传统v4模型
        paddlex_dir = os.path.join(home_dir, ".paddlex", "official_models")
        use_paddlex = os.path.exists(paddlex_dir)
        
        # 检查PaddleOCR 3.x的新模型存储位置
        if use_paddlex:
            model_dirs = [d for d in os.listdir(paddlex_dir) if os.path.isdir(os.path.join(paddlex_dir, d))]
            
            # 确定当前使用的PaddleX模型（通常是mobile版本优先）
            current_models = []
            for model_dir in model_dirs:
                if 'mobile' in model_dir.lower():
                    current_models.append(model_dir)
            
            # 如果没有mobile版本，选择其他可用模型
            if not current_models and model_dirs:
                current_models = model_dirs[:3]  # 取前3个作为当前使用的模型
            
            for model_dir in model_dirs:
                model_path = os.path.join(paddlex_dir, model_dir)
                size_mb = get_directory_size_mb(model_path)
                if size_mb > 0:
                    models_info.append({
                        'name': model_dir,
                        'version': '3.x',
                        'size_mb': size_mb,
                        'type': 'PaddleX Official',
                        'is_current': model_dir in current_models
                    })
        
        # 向后兼容：检查旧版本模型结构
        paddle_dir = os.path.join(home_dir, ".paddleocr")
        if os.path.exists(paddle_dir):
            whl_dir = os.path.join(paddle_dir, "whl")
            if os.path.exists(whl_dir):
                # 检查v4模型文件
                model_configs = [
                    {
                        'path': os.path.join(whl_dir, "det", "ch", "ch_PP-OCRv4_det_infer"),
                        'name': 'PP-OCRv4 检测模型',
                        'version': 'v4.0',
                        'type': 'Detection'
                    },
                    {
                        'path': os.path.join(whl_dir, "rec", "ch", "ch_PP-OCRv4_rec_infer"),
                        'name': 'PP-OCRv4 识别模型',
                        'version': 'v4.0',
                        'type': 'Recognition'
                    },
                    {
                        'path': os.path.join(whl_dir, "cls", "ch_ppocr_mobile_v2.0_cls_infer"),
                        'name': '文字方向分类模型',
                        'version': 'v2.0',
                        'type': 'Classification'
                    }
                ]
                
                for model_config in model_configs:
                    model_path = model_config['path']
                    if os.path.exists(model_path):
                        pdmodel_file = os.path.join(model_path, "inference.pdmodel")
                        pdiparams_file = os.path.join(model_path, "inference.pdiparams")
                        if os.path.exists(pdmodel_file) and os.path.exists(pdiparams_file):
                            size_mb = get_directory_size_mb(model_path)
                            models_info.append({
                                'name': model_config['name'],
                                'version': model_config['version'],
                                'size_mb': size_mb,
                                'type': model_config['type'],
                                'is_current': not use_paddlex  # 只有在没有PaddleX模型时才标记为当前
                            })
        
        return models_info
        
    except Exception as e:
        logging.error(f"获取模型信息时出错: {e}")
        return []

def check_models_downloaded():
    """检查模型文件是否已下载 - 兼容PaddleOCR 3.x版本"""
    try:
        home_dir = os.path.expanduser("~")
        
        # 检查PaddleOCR 3.x的新模型存储位置
        paddlex_dir = os.path.join(home_dir, ".paddlex", "official_models")
        if os.path.exists(paddlex_dir):
            # 检查是否有任何模型文件
            model_dirs = [d for d in os.listdir(paddlex_dir) if os.path.isdir(os.path.join(paddlex_dir, d))]
            if len(model_dirs) >= 3:  # 至少需要检测、识别、方向分类模型
                logging.info(f"检测到PaddleOCR 3.x模型文件: {len(model_dirs)}个模型")
                return True
        
        # 向后兼容：检查旧版本模型结构
        paddle_dir = os.path.join(home_dir, ".paddleocr")
        if os.path.exists(paddle_dir):
            whl_dir = os.path.join(paddle_dir, "whl")
            if os.path.exists(whl_dir):
                # 检查v4模型文件
                model_paths = [
                    os.path.join(whl_dir, "det", "ch", "ch_PP-OCRv4_det_infer"),
                    os.path.join(whl_dir, "rec", "ch", "ch_PP-OCRv4_rec_infer"), 
                    os.path.join(whl_dir, "cls", "ch_ppocr_mobile_v2.0_cls_infer")
                ]
                
                valid_models = 0
                for model_path in model_paths:
                    if os.path.exists(model_path):
                        pdmodel_file = os.path.join(model_path, "inference.pdmodel")
                        pdiparams_file = os.path.join(model_path, "inference.pdiparams")
                        if os.path.exists(pdmodel_file) and os.path.exists(pdiparams_file):
                            valid_models += 1
                
                if valid_models >= 2:  # 至少需要检测和识别模型
                    logging.info("检测到PaddleOCR v4兼容模型文件")
                    return True
        
        return False
        
    except Exception as e:
        logging.error(f"检查模型文件时出错: {e}")
        return False

def can_init_ocr_immediately():
    """检查是否可以立即初始化OCR（不需要下载）"""
    return check_paddle_available() and check_models_downloaded()

def init_ocr_async():
    """异步初始化OCR服务 - 基于PaddleOCR 3.2.0优化"""
    global ocr_service, ocr_initializing, ocr_init_error
    
    try:
        ocr_initializing = True
        ocr_init_error = None
        
        logging.info("开始初始化OCR服务（PaddleOCR 3.x）...")
        
        # 检查PaddleOCR是否可用
        if not check_paddle_available():
            raise ImportError("PaddleOCR未安装或版本不兼容")
        
        # 导入必要模块
        from paddleocr import PaddleOCR
        import paddle
        
        # 强制使用CPU模式 - PaddleOCR 3.x推荐配置
        paddle.set_device('cpu')
        
        # 基于PaddleOCR 3.x版本的优化配置 - 使用轻量级模型
        ocr_config = {
            'use_textline_orientation': True,  # 启用文字方向分类
            # 使用轻量级移动端模型提高速度
            'text_detection_model_name': 'PP-OCRv4_mobile_det',
            'text_recognition_model_name': 'PP-OCRv4_mobile_rec',
        }
        
        # 初始化OCR服务
        logging.info("正在创建PaddleOCR实例...")
        ocr_service = PaddleOCR(**ocr_config)
        
        # 模型预热 - 使用小图片进行一次识别以加载模型到内存
        logging.info("正在进行模型预热...")
        try:
            import numpy as np
            from PIL import Image
            
            # 创建一个小的测试图片进行预热
            test_img = Image.new('RGB', (100, 50), color='white')
            test_img_array = np.array(test_img)
            
            # 执行一次简单的OCR预热
            _ = ocr_service.predict(test_img_array)
            logging.info("模型预热完成")
            
        except Exception as warmup_error:
            logging.warning(f"模型预热失败，但不影响正常使用: {warmup_error}")
        
        logging.info("OCR服务初始化成功（PaddleOCR 3.x）")
        
    except Exception as e:
        logging.error(f"OCR服务初始化失败: {e}")
        ocr_init_error = str(e)
        ocr_service = None
    finally:
        ocr_initializing = False

# 创建应用
app = create_app()

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/api/status')
def api_status():
    """获取系统状态"""
    global ocr_service, ocr_initializing, ocr_init_error
    
    paddle_available = check_paddle_available()
    models_downloaded = check_models_downloaded()
    can_init_immediately = can_init_ocr_immediately()
    models_info = get_model_info()
    
    return jsonify({
        'success': True,
        'data': {
            'paddle_available': paddle_available,
            'models_downloaded': models_downloaded,
            'can_init_immediately': can_init_immediately,
            'ocr_ready': ocr_service is not None,
            'ocr_initializing': ocr_initializing,
            'ocr_error': ocr_init_error,
            'version': 'PaddleOCR 3.x',
            'models_info': models_info,
            'timestamp': time.time()
        }
    })

@app.route('/api/init-ocr', methods=['POST'])
def init_ocr():
    """初始化OCR服务"""
    global ocr_initializing
    
    if ocr_service:
        return jsonify({
            'success': True,
            'message': 'OCR服务已经初始化'
        })
    
    if ocr_initializing:
        return jsonify({
            'success': False,
            'error': {'message': 'OCR服务正在初始化中'}
        }), 409
    
    # 开始异步初始化
    thread = threading.Thread(target=init_ocr_async)
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'success': True,
        'message': 'OCR服务初始化已开始'
    })

@app.route('/api/ocr', methods=['POST'])
def process_ocr():
    """处理OCR请求 - 基于PaddleOCR 3.2.0优化"""
    global ocr_service
    
    if not ocr_service:
        return jsonify({
            'success': False,
            'error': {'message': 'OCR服务未初始化'}
        }), 503
    
    if 'file' not in request.files:
        return jsonify({
            'success': False,
            'error': {'message': '没有上传文件'}
        }), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({
            'success': False,
            'error': {'message': '文件名为空'}
        }), 400
    
    # 初始化变量
    text_content = ""
    text_lines = []
    temp_path = None
    
    try:
        # 生成唯一的临时文件名
        temp_filename = f"ocr_temp_{uuid.uuid4().hex}.jpg"
        temp_path = os.path.join(tempfile.gettempdir(), temp_filename)
        
        # 保存文件
        file.save(temp_path)
        
        # 执行OCR - 使用PaddleOCR 3.x推荐方式
        logging.info(f"开始处理图片: {file.filename}")
        start_time = time.time()
        
        # PaddleOCR 3.x推荐的调用方式
        result = ocr_service.predict(temp_path)
        
        process_time = time.time() - start_time
        logging.info(f"OCR处理完成，耗时: {process_time:.2f}秒")
        
        # 调试：打印原始结果结构
        logging.info(f"原始结果类型: {type(result)}")
        logging.info(f"原始结果长度: {len(result) if result else 0}")
        if result:
            logging.info(f"结果示例: {str(result)[:200]}...")
        
        # 提取文本 - 适配PaddleOCR 3.x的新返回格式
        if result and len(result) > 0:
            logging.info("开始解析识别结果...")
            
            try:
                # PaddleOCR 3.x新格式: 结果是字典列表，包含rec_texts和rec_scores
                for page_result in result:
                    if isinstance(page_result, dict):
                        # 获取识别的文字和置信度
                        rec_texts = page_result.get('rec_texts', [])
                        rec_scores = page_result.get('rec_scores', [])
                        
                        logging.info(f"识别到 {len(rec_texts)} 行文字")
                        
                        for i, text in enumerate(rec_texts):
                            confidence = rec_scores[i] if i < len(rec_scores) else 0.0
                            logging.info(f"文字: '{text}', 置信度: {confidence:.2f}")
                            
                            # 降低置信度阈值，确保能识别到文字
                            if confidence > 0.3 and text.strip():
                                text_lines.append(text.strip())
                
                if not text_lines:
                    logging.warning("未找到符合条件的文字")
                else:
                    logging.info(f"成功解析 {len(text_lines)} 行文字")
                        
            except Exception as parse_error:
                logging.error(f"结果解析失败: {parse_error}")
                
                # 备用解析：尝试其他可能的格式
                try:
                    logging.info("尝试备用解析方式...")
                    if isinstance(result, list):
                        for item in result:
                            if isinstance(item, str) and item.strip():
                                text_lines.append(item.strip())
                            elif isinstance(item, dict):
                                # 查找可能的文字字段
                                for key in ['text', 'content', 'result']:
                                    if key in item and isinstance(item[key], str):
                                        text_lines.append(item[key].strip())
                except Exception as backup_error:
                    logging.error(f"备用解析也失败: {backup_error}")
        
        else:
            logging.warning("OCR结果为空或无效")
        
        text_content = '\n'.join(text_lines)
        
        return jsonify({
            'success': True,
            'data': {
                'text_content': text_content,
                'line_count': len(text_lines),
                'process_time': round(process_time, 2)
            }
        })
    
    except Exception as e:
        logging.error(f"OCR处理失败: {e}")
        return jsonify({
            'success': False,
            'error': {'message': f'OCR处理失败: {str(e)}'}
        }), 500
    
    finally:
        # 确保删除临时文件
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except Exception as cleanup_error:
                logging.warning(f"清理临时文件失败: {cleanup_error}")

@app.route('/health')
def health():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'version': 'v0.2.0',
        'paddleocr_version': '3.x',
        'timestamp': time.time()
    })

if __name__ == '__main__':
    logging.info("启动PaddlePaddle OCR v0.2.0（基于PaddleOCR 3.x）...")
    logging.info("优化特性：快速启动、CPU模式、延迟初始化、使用最新API")
    app.run(host='127.0.0.1', port=5000, debug=False)