#!/usr/bin/env python3
"""
最终集成测试用例 - Task 9.2
专注于核心功能的集成测试，避免复杂的并发测试
测试完整的用户流程（OCR → 格式转换 → 下载）
验证不同文档类型的处理效果
Requirements: 1.1, 1.2, 2.1, 2.2
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


class TestEndToEndIntegration(unittest.TestCase):
    """端到端集成测试 - Requirements 1.1, 1.2"""
    
    def setUp(self):
        """设置测试环境"""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app_context = self.app.app_context()
        self.app_context.push()
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
    
    def tearDown(self):
        """清理测试环境"""
        self.app_context.pop()
    
    def create_test_image(self):
        """创建测试图片"""
        img = Image.new('RGB', (400, 300), color='white')
        img_bytes = BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        return img_bytes
    
    @patch('app.ocr_service')
    def test_complete_workflow_text_format(self, mock_ocr):
        """测试完整工作流程 - 纯文本格式 (Requirement 1.1)"""
        mock_ocr.predict.return_value = self.mock_ocr_result
        
        # 步骤1: OCR识别
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
        self.assertGreater(len(original_text), 0)
        
        # 步骤2: 格式转换（保持文本格式）
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
        
        # 步骤3: 文件下载
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
    
    @patch('app.ocr_service')
    def test_complete_workflow_markdown_format(self, mock_ocr):
        """测试完整工作流程 - Markdown格式 (Requirement 1.2)"""
        mock_ocr.predict.return_value = self.mock_ocr_result
        
        # 步骤1: OCR识别
        response = self.client.post(
            '/api/ocr',
            data={'file': (self.test_image, 'test.png')},
            content_type='multipart/form-data'
        )
        
        self.assertEqual(response.status_code, 200)
        ocr_data = json.loads(response.data)
        original_text = ocr_data['data']['text_content']
        
        # 步骤2: 格式转换到Markdown
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
        
        # 验证Markdown格式转换
        markdown_content = convert_data['data']['converted_text']
        self.assertIn('#', markdown_content)  # 应该包含标题标记
        
        # 步骤3: 下载Markdown文件
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
    
    def test_format_conversion_fallback(self):
        """测试格式转换失败时的回退机制 (Requirements 1.1, 1.2)"""
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


class TestDocumentTypeProcessing(unittest.TestCase):
    """测试不同文档类型的处理效果 - Requirements 2.1, 2.2"""
    
    def setUp(self):
        self.export_manager = ExportManager()
        self.analyzer = TextAnalyzer()
        self.formatter = MarkdownFormatter(self.analyzer)
        
        # 定义不同类型的测试文档
        self.document_types = {
            'simple_paragraphs': {
                'text': """这是第一个段落的内容。
这是第二个段落的内容。
这是第三个段落的内容。""",
                'expected_elements': ['paragraphs']
            },
            
            'with_headings': {
                'text': """项目报告
概述
这是项目的概述部分。
详细说明
这里是详细的说明内容。""",
                'expected_elements': ['headings', 'paragraphs']
            },
            
            'with_lists': {
                'text': """购物清单：
- 苹果
- 香蕉
- 橙子
任务列表：
1. 完成报告
2. 发送邮件
3. 安排会议""",
                'expected_elements': ['lists', 'headings']
            },
            
            'complex_structure': {
                'text': """# 系统设计文档
## 概述
本文档描述了系统的整体架构。

## 功能模块
### 用户管理
负责用户的注册和登录。

主要功能：
- 用户注册
- 用户登录
- 权限验证

### 数据处理
负责数据的处理和存储。

处理流程：
1. 数据采集
2. 数据清洗
3. 数据存储""",
                'expected_elements': ['headings', 'paragraphs', 'lists']
            }
        }
    
    def test_simple_paragraph_processing(self):
        """测试简单段落文档处理 (Requirement 2.1)"""
        doc = self.document_types['simple_paragraphs']
        
        result = self.export_manager.convert_format(doc['text'], 'markdown')
        
        self.assertEqual(result['format'], 'markdown')
        self.assertGreater(len(result['content']), 0)
        self.assertIn('conversion_time', result)
        
        # 验证段落被正确处理
        markdown_content = result['content']
        self.assertIn('第一个段落', markdown_content)
        self.assertIn('第二个段落', markdown_content)
        self.assertIn('第三个段落', markdown_content)
    
    def test_heading_detection_and_formatting(self):
        """测试标题检测和格式化 (Requirement 2.2)"""
        doc = self.document_types['with_headings']
        
        result = self.export_manager.convert_format(doc['text'], 'markdown')
        
        self.assertEqual(result['format'], 'markdown')
        markdown_content = result['content']
        
        # 验证标题被正确识别和格式化
        self.assertIn('#', markdown_content)
        
        # 验证结构信息
        if 'structure_info' in result:
            structure = result['structure_info']
            self.assertGreater(structure.get('headings_count', 0), 0)
            self.assertGreater(structure.get('paragraphs_count', 0), 0)
    
    def test_list_detection_and_formatting(self):
        """测试列表检测和格式化 (Requirement 2.2)"""
        doc = self.document_types['with_lists']
        
        result = self.export_manager.convert_format(doc['text'], 'markdown')
        
        self.assertEqual(result['format'], 'markdown')
        markdown_content = result['content']
        
        # 验证列表格式
        self.assertIn('-', markdown_content)  # 无序列表
        self.assertIn('1.', markdown_content)  # 有序列表
        
        # 验证结构信息
        if 'structure_info' in result:
            structure = result['structure_info']
            self.assertGreater(structure.get('lists_count', 0), 0)
    
    def test_complex_document_structure(self):
        """测试复杂文档结构处理 (Requirements 2.1, 2.2)"""
        doc = self.document_types['complex_structure']
        
        result = self.export_manager.convert_format(doc['text'], 'markdown')
        
        self.assertEqual(result['format'], 'markdown')
        markdown_content = result['content']
        
        # 验证多级标题
        self.assertIn('#', markdown_content)
        self.assertIn('##', markdown_content)
        self.assertIn('###', markdown_content)
        
        # 验证列表和段落
        self.assertIn('-', markdown_content)
        self.assertIn('1.', markdown_content)
        
        # 验证结构信息完整性
        if 'structure_info' in result:
            structure = result['structure_info']
            self.assertGreater(structure.get('headings_count', 0), 0)
            self.assertGreater(structure.get('paragraphs_count', 0), 0)
            self.assertGreater(structure.get('lists_count', 0), 0)
    
    def test_empty_and_whitespace_documents(self):
        """测试空文档和空白文档处理 (Requirement 2.1)"""
        # 空文档
        result = self.export_manager.convert_format('', 'markdown')
        self.assertEqual(result['format'], 'markdown')
        self.assertEqual(result['content'], '')
        
        # 只有空白的文档
        result = self.export_manager.convert_format('   \n\n   ', 'markdown')
        self.assertEqual(result['format'], 'markdown')
        # 应该返回空内容或处理后的空白
        self.assertTrue(len(result['content'].strip()) == 0)
    
    def test_performance_with_large_document(self):
        """测试大文档处理性能 (Requirement 2.1)"""
        # 创建一个较大的文档
        large_paragraphs = []
        for i in range(50):
            large_paragraphs.append(f"这是第{i+1}段内容，包含了详细的描述信息。" * 3)
        
        large_text = '\n\n'.join(large_paragraphs)
        
        start_time = time.time()
        result = self.export_manager.convert_format(large_text, 'markdown')
        end_time = time.time()
        
        self.assertEqual(result['format'], 'markdown')
        self.assertGreater(len(result['content']), 0)
        
        # 验证转换时间合理
        conversion_time = end_time - start_time
        self.assertLess(conversion_time, 10.0)  # 应该在10秒内完成
        
        # 验证结果包含转换时间信息
        self.assertIn('conversion_time', result)
        self.assertGreater(result['conversion_time'], 0)


class TestConcurrentAccessBasic(unittest.TestCase):
    """基础并发访问测试 - Requirements 1.1, 1.2"""
    
    def setUp(self):
        self.export_manager = ExportManager()
        self.test_texts = [
            f"并发测试文本 {i}：这是用于测试并发访问的文本内容。"
            for i in range(5)
        ]
        self.results = []
        self.errors = []
        self.lock = threading.Lock()
    
    def worker_format_conversion(self, worker_id, text, target_format):
        """格式转换工作线程"""
        try:
            result = self.export_manager.convert_format(text, target_format)
            
            with self.lock:
                self.results.append({
                    'worker_id': worker_id,
                    'success': True,
                    'format': result['format'],
                    'conversion_time': result['conversion_time'],
                    'content_length': len(result['content'])
                })
                
        except Exception as e:
            with self.lock:
                self.errors.append({
                    'worker_id': worker_id,
                    'error': str(e),
                    'error_type': type(e).__name__
                })
    
    def test_concurrent_text_conversion(self):
        """测试并发文本格式转换 (Requirement 1.1)"""
        self.results.clear()
        self.errors.clear()
        
        threads = []
        
        # 创建并启动多个线程
        for i, text in enumerate(self.test_texts):
            thread = threading.Thread(
                target=self.worker_format_conversion,
                args=(i, text, 'text')
            )
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join(timeout=30)
        
        # 验证结果
        self.assertEqual(len(self.errors), 0, f"并发文本转换测试出现错误: {self.errors}")
        self.assertEqual(len(self.results), len(self.test_texts))
        
        # 验证所有请求都成功
        for result in self.results:
            self.assertTrue(result['success'])
            self.assertEqual(result['format'], 'text')
            self.assertGreater(result['conversion_time'], 0)
            self.assertGreater(result['content_length'], 0)
    
    def test_concurrent_markdown_conversion(self):
        """测试并发Markdown格式转换 (Requirement 1.2)"""
        self.results.clear()
        self.errors.clear()
        
        # 使用结构化文本进行Markdown转换测试
        structured_texts = [
            f"""标题 {i}
            
概述 {i}
这是第{i}个并发测试的概述部分。

功能列表 {i}：
- 功能 {i}.1
- 功能 {i}.2
- 功能 {i}.3"""
            for i in range(len(self.test_texts))
        ]
        
        threads = []
        
        # 创建并启动多个线程
        for i, text in enumerate(structured_texts):
            thread = threading.Thread(
                target=self.worker_format_conversion,
                args=(i, text, 'markdown')
            )
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join(timeout=30)
        
        # 验证结果
        self.assertEqual(len(self.errors), 0, f"并发Markdown转换测试出现错误: {self.errors}")
        self.assertEqual(len(self.results), len(structured_texts))
        
        # 验证所有请求都成功
        for result in self.results:
            self.assertTrue(result['success'])
            self.assertEqual(result['format'], 'markdown')
            self.assertGreater(result['conversion_time'], 0)
            self.assertGreater(result['content_length'], 0)


class TestSystemIntegration(unittest.TestCase):
    """系统集成测试 - Requirements 1.1, 1.2, 2.1, 2.2"""
    
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
    
    def tearDown(self):
        """清理测试环境"""
        self.app_context.pop()
    
    def test_system_health_and_status(self):
        """测试系统健康状态和状态信息"""
        # 健康检查
        health_response = self.client.get('/health')
        self.assertEqual(health_response.status_code, 200)
        
        health_data = json.loads(health_response.data)
        self.assertEqual(health_data['status'], 'healthy')
        self.assertIn('version', health_data)
        
        # 系统状态
        status_response = self.client.get('/api/status')
        self.assertEqual(status_response.status_code, 200)
        
        status_data = json.loads(status_response.data)
        self.assertTrue(status_data['success'])
        self.assertIn('data', status_data)
    
    def test_api_error_handling_consistency(self):
        """测试API错误处理一致性"""
        # 测试格式转换API的错误处理
        response = self.client.post(
            '/api/convert-format',
            data='invalid json',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('error', data)
        self.assertIn('code', data['error'])
        
        # 测试下载API的错误处理
        response = self.client.post(
            '/api/download-result',
            data='invalid json',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('error', data)
        self.assertIn('code', data['error'])
    
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
    
    def test_format_conversion_api_functionality(self):
        """测试格式转换API功能"""
        test_text = "这是一个测试文档。\n包含多个段落。"
        
        # 测试转换为文本格式
        response = self.client.post(
            '/api/convert-format',
            data=json.dumps({
                'text': test_text,
                'target_format': 'text'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['target_format'], 'text')
        
        # 测试转换为Markdown格式
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
        self.assertEqual(data['data']['target_format'], 'markdown')
    
    def test_download_api_functionality(self):
        """测试下载API功能"""
        test_content = "这是测试下载的内容。"
        
        # 测试下载文本文件
        response = self.client.post(
            '/api/download-result',
            data=json.dumps({
                'content': test_content,
                'format': 'text'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Content-Type'], 'text/plain; charset=utf-8')
        self.assertIn('.txt', response.headers.get('Content-Disposition', ''))
        
        # 测试下载Markdown文件
        response = self.client.post(
            '/api/download-result',
            data=json.dumps({
                'content': test_content,
                'format': 'markdown'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Content-Type'], 'text/markdown; charset=utf-8')
        self.assertIn('.md', response.headers.get('Content-Disposition', ''))


class TestErrorHandlingAndRecovery(unittest.TestCase):
    """错误处理和恢复测试 - Requirements 1.1, 1.2"""
    
    def setUp(self):
        self.export_manager = ExportManager()
    
    def test_format_conversion_error_recovery(self):
        """测试格式转换错误恢复"""
        # 模拟markdown转换器失败
        with patch.object(self.export_manager.formatters['markdown'], 'convert') as mock_convert:
            mock_convert.side_effect = Exception("Markdown conversion failed")
            
            result = self.export_manager.convert_format('test text', 'markdown')
            
            # 验证回退到文本格式
            self.assertEqual(result['format'], 'text')
            self.assertEqual(result['content'], 'test text')
            self.assertIn('error', result)
            self.assertTrue(result['error']['fallback_applied'])
    
    def test_invalid_input_handling(self):
        """测试无效输入处理"""
        from core.exceptions import ValidationError, UnsupportedFormatError
        
        # 测试无效文本类型
        with self.assertRaises(ValidationError):
            self.export_manager.convert_format(123, 'text')
        
        # 测试不支持的格式
        with self.assertRaises(UnsupportedFormatError):
            self.export_manager.convert_format('test', 'pdf')
    
    def test_empty_content_handling(self):
        """测试空内容处理"""
        # 空文本应该正常处理
        result = self.export_manager.convert_format('', 'text')
        self.assertEqual(result['format'], 'text')
        self.assertEqual(result['content'], '')
        
        # 空白文本应该正常处理
        result = self.export_manager.convert_format('   \n\n   ', 'markdown')
        self.assertEqual(result['format'], 'markdown')


if __name__ == '__main__':
    # 设置测试套件
    test_suite = unittest.TestSuite()
    
    # 添加测试类
    test_classes = [
        TestEndToEndIntegration,
        TestDocumentTypeProcessing,
        TestConcurrentAccessBasic,
        TestSystemIntegration,
        TestErrorHandlingAndRecovery
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # 输出详细的测试结果摘要
    print(f"\n{'='*60}")
    print(f"最终集成测试摘要 (Task 9.2):")
    print(f"{'='*60}")
    print(f"运行测试: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    print(f"跳过: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    
    if result.failures:
        print(f"\n失败的测试:")
        for test, traceback in result.failures:
            print(f"- {test}")
            # 只显示关键错误信息
            error_lines = traceback.split('\n')
            for line in error_lines:
                if 'AssertionError:' in line:
                    print(f"  {line.strip()}")
                    break
    
    if result.errors:
        print(f"\n错误的测试:")
        for test, traceback in result.errors:
            print(f"- {test}")
            # 只显示关键错误信息
            error_lines = traceback.split('\n')
            for line in error_lines:
                if any(keyword in line for keyword in ['Error:', 'Exception:', 'ImportError:']):
                    print(f"  {line.strip()}")
                    break
    
    success_rate = (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100
    print(f"\n成功率: {success_rate:.1f}%")
    print(f"{'='*60}")
    
    # 测试覆盖的需求
    print(f"\n✅ 测试覆盖的需求:")
    print(f"- Requirement 1.1: 用户格式选择和实时转换")
    print(f"- Requirement 1.2: OCR结果转换为markdown格式")
    print(f"- Requirement 2.1: 智能识别文档结构元素")
    print(f"- Requirement 2.2: 处理不同类型文档内容")
    
    print(f"\n✅ 测试场景覆盖:")
    print(f"- 端到端用户流程测试 (OCR → 格式转换 → 下载)")
    print(f"- 不同文档类型处理效果验证")
    print(f"- 基础并发用户访问场景")
    print(f"- 系统集成和错误处理测试")
    
    print(f"\n📊 测试统计:")
    print(f"- 端到端集成测试: 3个测试用例")
    print(f"- 文档类型处理测试: 6个测试用例")
    print(f"- 并发访问测试: 2个测试用例")
    print(f"- 系统集成测试: 5个测试用例")
    print(f"- 错误处理测试: 3个测试用例")
    
    # 如果有失败或错误，退出时返回非零状态码
    if result.failures or result.errors:
        print(f"\n⚠️  部分测试未通过，请检查上述失败和错误信息")
        sys.exit(1)
    else:
        print(f"\n🎉 所有集成测试通过！Task 9.2 完成")
        sys.exit(0)