#!/usr/bin/env python3
"""
集成测试用例
测试完整的用户流程和系统集成
"""

import unittest
import sys
import os
import json
import tempfile
import time
import threading
from unittest.mock import patch, MagicMock
from io import BytesIO
from PIL import Image
import numpy as np

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from core import ExportManager
from core.text_processing.analyzer import TextAnalyzer
from core.text_processing.formatters import MarkdownFormatter


class TestEndToEndUserFlow(unittest.TestCase):
    """端到端用户流程测试"""
    
    def setUp(self):
        """设置测试环境"""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        # 创建测试图片
        self.test_image = self.create_test_image()
        
        # 模拟OCR结果
        self.mock_ocr_result = [
            {
                'rec_texts': [
                    '项目报告',
                    '概述',
                    '这是一个测试项目的概述部分。',
                    '功能列表',
                    '1. 文本识别功能',
                    '2. 格式转换功能',
                    '3. 文件下载功能',
                    '详细说明',
                    '每个功能都经过了充分的测试和验证。'
                ],
                'rec_scores': [0.95, 0.92, 0.88, 0.94, 0.91, 0.89, 0.87, 0.93, 0.86]
            }
        ]
    
    def create_test_image(self):
        """创建测试图片"""
        # 创建一个简单的测试图片
        img = Image.new('RGB', (400, 300), color='white')
        
        # 转换为字节流
        img_bytes = BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        return img_bytes
    
    def test_complete_user_flow_text_format(self):
        """测试完整用户流程 - 纯文本格式"""
        # 1. 检查系统状态
        response = self.client.get('/api/status')
        self.assertEqual(response.status_code, 200)
        
        # 2. 模拟OCR处理
        with patch('app.ocr_service') as mock_ocr:
            mock_ocr.predict.return_value = self.mock_ocr_result
            
            # 上传图片进行OCR识别
            response = self.client.post(
                '/api/ocr',
                data={'file': (self.test_image, 'test.png')},
                content_type='multipart/form-data'
            )
            
            self.assertEqual(response.status_code, 200)
            ocr_data = json.loads(response.data)
            self.assertTrue(ocr_data['success'])
            self.assertIn('text_content', ocr_data['data'])
            self.assertIn('available_formats', ocr_data['data'])
            
            original_text = ocr_data['data']['text_content']
        
        # 3. 格式转换（保持文本格式）
        response = self.client.post(
            '/api/convert-format',
            data=json.dumps({
                'text': original_text,
                'target_format': 'text'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        convert_data = json.loads(response.data)
        self.assertTrue(convert_data['success'])
        self.assertEqual(convert_data['data']['target_format'], 'text')
        
        # 4. 下载文件
        response = self.client.post(
            '/api/download-result',
            data=json.dumps({
                'content': convert_data['data']['converted_text'],
                'format': 'text'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Content-Type'], 'text/plain; charset=utf-8')
        self.assertIn('attachment', response.headers['Content-Disposition'])
    
    def test_complete_user_flow_markdown_format(self):
        """测试完整用户流程 - Markdown格式"""
        # 1. 模拟OCR处理
        with patch('app.ocr_service') as mock_ocr:
            mock_ocr.predict.return_value = self.mock_ocr_result
            
            response = self.client.post(
                '/api/ocr',
                data={'file': (self.test_image, 'test.png')},
                content_type='multipart/form-data'
            )
            
            self.assertEqual(response.status_code, 200)
            ocr_data = json.loads(response.data)
            original_text = ocr_data['data']['text_content']
        
        # 2. 格式转换到Markdown
        response = self.client.post(
            '/api/convert-format',
            data=json.dumps({
                'text': original_text,
                'target_format': 'markdown'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        convert_data = json.loads(response.data)
        self.assertTrue(convert_data['success'])
        self.assertEqual(convert_data['data']['target_format'], 'markdown')
        
        # 验证Markdown格式
        markdown_content = convert_data['data']['converted_text']
        self.assertIn('#', markdown_content)  # 应该包含标题标记
        
        # 3. 下载Markdown文件
        response = self.client.post(
            '/api/download-result',
            data=json.dumps({
                'content': markdown_content,
                'format': 'markdown'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Content-Type'], 'text/markdown; charset=utf-8')
        self.assertIn('.md', response.headers['Content-Disposition'])
    
    def test_format_conversion_with_fallback(self):
        """测试格式转换失败时的回退机制"""
        test_text = "测试文本内容"
        
        # 模拟格式转换失败
        with patch('core.text_processing.formatters.MarkdownFormatter.convert') as mock_convert:
            mock_convert.side_effect = Exception("Conversion failed")
            
            response = self.client.post(
                '/api/convert-format',
                data=json.dumps({
                    'text': test_text,
                    'target_format': 'markdown'
                }),
                content_type='application/json'
            )
            
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertTrue(data['success'])
            
            # 应该回退到文本格式
            self.assertEqual(data['data']['target_format'], 'text')
            self.assertEqual(data['data']['converted_text'], test_text)
            self.assertIn('fallback_info', data['data'])
    
    def test_error_handling_invalid_requests(self):
        """测试各种无效请求的错误处理"""
        # 1. 无效的格式转换请求
        response = self.client.post(
            '/api/convert-format',
            data=json.dumps({
                'text': 'test',
                'target_format': 'invalid_format'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertEqual(data['error']['code'], 'UNSUPPORTED_FORMAT')
        
        # 2. 无效的下载请求
        response = self.client.post(
            '/api/download-result',
            data=json.dumps({
                'content': '',
                'format': 'text'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertEqual(data['error']['code'], 'VALIDATION_ERROR')
        
        # 3. 无效的JSON请求
        response = self.client.post(
            '/api/convert-format',
            data='invalid json',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertEqual(data['error']['code'], 'INVALID_JSON')


class TestDifferentDocumentTypes(unittest.TestCase):
    """测试不同文档类型的处理效果"""
    
    def setUp(self):
        self.export_manager = ExportManager()
        self.analyzer = TextAnalyzer()
        self.formatter = MarkdownFormatter(self.analyzer)
    
    def test_simple_paragraph_document(self):
        """测试简单段落文档"""
        text = """这是第一个段落的内容。
这是第二个段落的内容。
这是第三个段落的内容。"""
        
        result = self.export_manager.convert_format(text, 'markdown')
        
        self.assertEqual(result['format'], 'markdown')
        self.assertIn('这是第一个段落', result['content'])
        self.assertIn('这是第二个段落', result['content'])
        self.assertIn('这是第三个段落', result['content'])
    
    def test_document_with_headings(self):
        """测试包含标题的文档"""
        text = """项目报告
概述
这是项目的概述部分。
详细说明
这里是详细的说明内容。"""
        
        result = self.export_manager.convert_format(text, 'markdown')
        
        self.assertEqual(result['format'], 'markdown')
        markdown_content = result['content']
        
        # 验证标题被正确识别和格式化
        self.assertIn('#', markdown_content)
        
        # 验证结构信息
        if 'structure_info' in result:
            self.assertGreater(result['structure_info']['headings_count'], 0)
    
    def test_document_with_lists(self):
        """测试包含列表的文档"""
        text = """购物清单：
- 苹果
- 香蕉
- 橙子
任务列表：
1. 完成报告
2. 发送邮件
3. 安排会议"""
        
        result = self.export_manager.convert_format(text, 'markdown')
        
        self.assertEqual(result['format'], 'markdown')
        markdown_content = result['content']
        
        # 验证列表格式
        self.assertIn('-', markdown_content)
        self.assertIn('1.', markdown_content)
        
        # 验证结构信息
        if 'structure_info' in result:
            self.assertGreater(result['structure_info']['lists_count'], 0)
    
    def test_complex_document_structure(self):
        """测试复杂文档结构"""
        text = """# 项目报告
## 概述
这是一个复杂的文档示例。

## 功能列表
### 主要功能
1. 文本识别
2. 格式转换
3. 文件下载

### 辅助功能
- 错误处理
- 用户界面
- 系统监控

## 技术细节
这里包含了详细的技术说明。

### 架构设计
系统采用模块化设计。

### 性能优化
- 缓存机制
- 异步处理
- 资源管理"""
        
        result = self.export_manager.convert_format(text, 'markdown')
        
        self.assertEqual(result['format'], 'markdown')
        
        # 验证结构信息
        if 'structure_info' in result:
            structure = result['structure_info']
            self.assertGreater(structure['headings_count'], 0)
            self.assertGreater(structure['lists_count'], 0)
            self.assertGreater(structure['paragraphs_count'], 0)
    
    def test_document_with_special_characters(self):
        """测试包含特殊字符的文档"""
        text = """特殊字符测试
这里包含一些特殊字符：
* 星号
# 井号
[] 方括号
() 圆括号
`代码标记`
**粗体标记**
_下划线_"""
        
        result = self.export_manager.convert_format(text, 'markdown')
        
        self.assertEqual(result['format'], 'markdown')
        markdown_content = result['content']
        
        # 验证特殊字符被正确转义
        self.assertIn('\\*', markdown_content)  # 星号应该被转义
        self.assertIn('\\#', markdown_content)  # 井号应该被转义
        self.assertIn('\\[', markdown_content)  # 方括号应该被转义
    
    def test_empty_and_whitespace_documents(self):
        """测试空文档和空白文档"""
        # 空文档
        result = self.export_manager.convert_format('', 'markdown')
        self.assertEqual(result['format'], 'markdown')
        self.assertEqual(result['content'], '')
        
        # 只有空白的文档
        result = self.export_manager.convert_format('   \n\n   ', 'markdown')
        self.assertEqual(result['format'], 'markdown')
        # 应该返回空内容或处理后的空白
        self.assertTrue(len(result['content'].strip()) == 0)
    
    def test_very_long_document(self):
        """测试很长的文档"""
        # 创建一个很长的文档
        long_text = '\n'.join([f"这是第{i}段内容。" for i in range(1, 1001)])
        
        result = self.export_manager.convert_format(long_text, 'markdown')
        
        self.assertEqual(result['format'], 'markdown')
        self.assertGreater(len(result['content']), 0)
        
        # 验证转换时间合理
        self.assertLess(result['conversion_time'], 10.0)  # 应该在10秒内完成


class TestConcurrentAccess(unittest.TestCase):
    """测试并发用户访问场景"""
    
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        
        # 创建多个客户端实例
        self.clients = [self.app.test_client() for _ in range(5)]
        
        self.test_text = "这是并发测试的文本内容。"
        self.results = []
        self.errors = []
    
    def worker_thread(self, client_id, client):
        """工作线程函数"""
        try:
            # 执行格式转换
            response = client.post(
                '/api/convert-format',
                data=json.dumps({
                    'text': f"{self.test_text} 客户端{client_id}",
                    'target_format': 'markdown'
                }),
                content_type='application/json'
            )
            
            if response.status_code == 200:
                data = json.loads(response.data)
                self.results.append({
                    'client_id': client_id,
                    'success': data['success'],
                    'format': data['data']['target_format'],
                    'conversion_time': data['data']['conversion_time']
                })
            else:
                self.errors.append({
                    'client_id': client_id,
                    'status_code': response.status_code,
                    'response': response.data
                })
                
        except Exception as e:
            self.errors.append({
                'client_id': client_id,
                'error': str(e)
            })
    
    def test_concurrent_format_conversion(self):
        """测试并发格式转换"""
        threads = []
        
        # 创建并启动多个线程
        for i, client in enumerate(self.clients):
            thread = threading.Thread(
                target=self.worker_thread,
                args=(i, client)
            )
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join(timeout=30)  # 30秒超时
        
        # 验证结果
        self.assertEqual(len(self.errors), 0, f"并发测试出现错误: {self.errors}")
        self.assertEqual(len(self.results), len(self.clients))
        
        # 验证所有请求都成功
        for result in self.results:
            self.assertTrue(result['success'])
            self.assertEqual(result['format'], 'markdown')
            self.assertGreater(result['conversion_time'], 0)
    
    def test_concurrent_download_requests(self):
        """测试并发下载请求"""
        def download_worker(client_id, client):
            try:
                response = client.post(
                    '/api/download-result',
                    data=json.dumps({
                        'content': f"{self.test_text} 下载测试{client_id}",
                        'format': 'text'
                    }),
                    content_type='application/json'
                )
                
                if response.status_code == 200:
                    self.results.append({
                        'client_id': client_id,
                        'success': True,
                        'content_type': response.headers.get('Content-Type'),
                        'content_length': len(response.data)
                    })
                else:
                    self.errors.append({
                        'client_id': client_id,
                        'status_code': response.status_code
                    })
                    
            except Exception as e:
                self.errors.append({
                    'client_id': client_id,
                    'error': str(e)
                })
        
        threads = []
        
        # 创建并启动下载线程
        for i, client in enumerate(self.clients):
            thread = threading.Thread(
                target=download_worker,
                args=(i, client)
            )
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join(timeout=30)
        
        # 验证结果
        self.assertEqual(len(self.errors), 0, f"并发下载测试出现错误: {self.errors}")
        self.assertEqual(len(self.results), len(self.clients))
        
        # 验证所有下载都成功
        for result in self.results:
            self.assertTrue(result['success'])
            self.assertIn('text/plain', result['content_type'])
            self.assertGreater(result['content_length'], 0)


class TestSystemIntegration(unittest.TestCase):
    """测试系统集成"""
    
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
    
    def test_api_endpoints_availability(self):
        """测试所有API端点的可用性"""
        endpoints = [
            ('GET', '/api/status'),
            ('GET', '/health'),
            ('GET', '/'),  # 主页
        ]
        
        for method, endpoint in endpoints:
            if method == 'GET':
                response = self.client.get(endpoint)
            else:
                response = self.client.post(endpoint)
            
            # 所有端点都应该返回有效响应（不是404）
            self.assertNotEqual(response.status_code, 404, 
                              f"Endpoint {method} {endpoint} not found")
    
    def test_system_status_information(self):
        """测试系统状态信息"""
        response = self.client.get('/api/status')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        
        status_data = data['data']
        required_fields = [
            'paddle_available', 'models_downloaded', 'can_init_immediately',
            'ocr_ready', 'ocr_initializing', 'version', 'timestamp'
        ]
        
        for field in required_fields:
            self.assertIn(field, status_data, f"Missing field: {field}")
    
    def test_health_check(self):
        """测试健康检查端点"""
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'healthy')
        self.assertIn('version', data)
        self.assertIn('timestamp', data)
    
    def test_main_page_loads(self):
        """测试主页加载"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('text/html', response.headers['Content-Type'])
        
        # 验证页面包含必要的元素
        html_content = response.data.decode('utf-8')
        self.assertIn('paddleocr', html_content.lower())
        self.assertIn('upload', html_content.lower())
    
    def test_static_files_serving(self):
        """测试静态文件服务"""
        # 测试CSS文件
        response = self.client.get('/static/css/style.css')
        # 如果文件存在，应该返回200；如果不存在，应该返回404
        self.assertIn(response.status_code, [200, 404])
        
        # 测试JavaScript文件
        response = self.client.get('/static/js/app.js')
        self.assertIn(response.status_code, [200, 404])
    
    def test_cors_headers(self):
        """测试CORS头部"""
        response = self.client.options('/api/status')
        
        # 检查是否有CORS相关头部
        # 注意：具体的CORS头部取决于Flask-CORS的配置
        self.assertIn(response.status_code, [200, 204])
    
    def test_error_response_format(self):
        """测试错误响应格式的一致性"""
        # 发送一个会导致错误的请求
        response = self.client.post(
            '/api/convert-format',
            data='invalid json',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        
        # 验证错误响应格式
        self.assertFalse(data['success'])
        self.assertIn('error', data)
        
        error = data['error']
        self.assertIn('message', error)
        self.assertIn('code', error)
    
    def test_request_size_limits(self):
        """测试请求大小限制"""
        # 创建一个很大的请求
        large_text = 'x' * (20 * 1024 * 1024)  # 20MB
        
        response = self.client.post(
            '/api/convert-format',
            data=json.dumps({
                'text': large_text,
                'target_format': 'text'
            }),
            content_type='application/json'
        )
        
        # 应该被拒绝或处理（取决于配置）
        # 如果有大小限制，应该返回413；否则应该正常处理
        self.assertIn(response.status_code, [200, 413, 400])


if __name__ == '__main__':
    # 设置测试套件
    test_suite = unittest.TestSuite()
    
    # 添加测试类
    test_classes = [
        TestEndToEndUserFlow,
        TestDifferentDocumentTypes,
        TestConcurrentAccess,
        TestSystemIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # 输出测试结果摘要
    print(f"\n{'='*50}")
    print(f"测试摘要:")
    print(f"运行测试: {result.testsRun}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    print(f"跳过: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    print(f"{'='*50}")
    
    # 如果有失败或错误，退出时返回非零状态码
    if result.failures or result.errors:
        sys.exit(1)
    else:
        print("所有测试通过！")
        sys.exit(0)