#!/usr/bin/env python3
"""
综合集成测试用例 - Task 9.2
测试完整的用户流程（OCR → 格式转换 → 下载）
验证不同文档类型的处理效果
测试并发用户访问场景
Requirements: 1.1, 1.2, 2.1, 2.2
"""

import unittest
import sys
import os
import json
import tempfile
import time
import threading
import concurrent.futures
import random
import string
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


class TestEndToEndUserFlows(unittest.TestCase):
    """端到端用户流程测试 - Requirements 1.1, 1.2"""
    
    def setUp(self):
        """设置测试环境"""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        
        # 创建测试图片
        self.test_images = {
            'simple': self.create_test_image(200, 100, 'Simple Document'),
            'complex': self.create_test_image(400, 300, 'Complex Report'),
            'large': self.create_test_image(800, 600, 'Large Document')
        }
    
    def tearDown(self):
        """清理测试环境"""
        self.app_context.pop()
        
        # 模拟不同类型的OCR结果
        self.ocr_results = {
            'simple_text': [
                {
                    'rec_texts': [
                        '这是一个简单的文档。',
                        '包含几个段落。',
                        '用于测试基本功能。'
                    ],
                    'rec_scores': [0.95, 0.92, 0.88]
                }
            ],
            'structured_document': [
                {
                    'rec_texts': [
                        '项目报告',
                        '概述',
                        '这是项目的概述部分，描述了项目的基本情况。',
                        '功能列表',
                        '1. 文本识别功能',
                        '2. 格式转换功能',
                        '3. 文件下载功能',
                        '详细说明',
                        '每个功能都经过了充分的测试和验证。',
                        '结论',
                        '项目达到了预期目标。'
                    ],
                    'rec_scores': [0.95, 0.92, 0.88, 0.94, 0.91, 0.89, 0.87, 0.93, 0.86, 0.90, 0.85]
                }
            ],
            'list_document': [
                {
                    'rec_texts': [
                        '购物清单',
                        '- 苹果',
                        '- 香蕉',
                        '- 橙子',
                        '- 牛奶',
                        '任务列表',
                        '1. 完成报告',
                        '2. 发送邮件',
                        '3. 安排会议',
                        '4. 更新文档'
                    ],
                    'rec_scores': [0.95, 0.92, 0.88, 0.94, 0.91, 0.89, 0.87, 0.93, 0.86, 0.90]
                }
            ]
        }
    
    def create_test_image(self, width, height, text):
        """创建测试图片"""
        img = Image.new('RGB', (width, height), color='white')
        img_bytes = BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        return img_bytes
    
    def test_complete_workflow_text_format(self):
        """测试完整工作流程 - 纯文本格式 (Requirement 1.1)"""
        with patch('app.ocr_service') as mock_ocr:
            mock_ocr.predict.return_value = self.ocr_results['simple_text']
            
            # 步骤1: OCR识别
            response = self.client.post(
                '/api/ocr',
                data={'file': (self.test_images['simple'], 'test.png')},
                content_type='multipart/form-data'
            )
            
            self.assertEqual(response.status_code, 200)
            ocr_data = json.loads(response.data)
            self.assertTrue(ocr_data['success'])
            self.assertIn('text_content', ocr_data['data'])
            self.assertIn('available_formats', ocr_data['data'])
            self.assertIn('text', ocr_data['data']['available_formats'])
            
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
            self.assertEqual(convert_data['data']['converted_text'], original_text)
            
            # 步骤3: 文件下载
            response = self.client.post(
                '/api/download-result',
                data=json.dumps({
                    'content': convert_data['data']['converted_text'],
                    'format': 'text',
                    'filename': 'test_result'
                }),
                content_type='application/json'
            )
            
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.headers['Content-Type'], 'text/plain; charset=utf-8')
            self.assertIn('attachment', response.headers['Content-Disposition'])
            self.assertIn('test_result.txt', response.headers['Content-Disposition'])
            
            # 验证下载的文件内容
            downloaded_content = response.data.decode('utf-8')
            self.assertEqual(downloaded_content, original_text)
    
    def test_complete_workflow_markdown_format(self):
        """测试完整工作流程 - Markdown格式 (Requirement 1.2)"""
        with patch('app.ocr_service') as mock_ocr:
            mock_ocr.predict.return_value = self.ocr_results['structured_document']
            
            # 步骤1: OCR识别
            response = self.client.post(
                '/api/ocr',
                data={'file': (self.test_images['complex'], 'complex.png')},
                content_type='multipart/form-data'
            )
            
            self.assertEqual(response.status_code, 200)
            ocr_data = json.loads(response.data)
            self.assertTrue(ocr_data['success'])
            self.assertIn('markdown', ocr_data['data']['available_formats'])
            
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
            self.assertNotEqual(markdown_content, original_text)  # 应该与原文不同
            
            # 验证结构信息
            if 'structure_info' in convert_data['data']:
                structure = convert_data['data']['structure_info']
                self.assertIn('headings_count', structure)
                self.assertIn('paragraphs_count', structure)
                self.assertIn('lists_count', structure)
            
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
            
            # 验证下载的Markdown内容
            downloaded_content = response.data.decode('utf-8')
            self.assertEqual(downloaded_content, markdown_content)
    
    def test_workflow_with_format_switching(self):
        """测试格式切换工作流程 (Requirements 1.1, 1.2)"""
        with patch('app.ocr_service') as mock_ocr:
            mock_ocr.predict.return_value = self.ocr_results['structured_document']
            
            # OCR识别
            response = self.client.post(
                '/api/ocr',
                data={'file': (self.test_images['complex'], 'test.png')},
                content_type='multipart/form-data'
            )
            
            original_text = json.loads(response.data)['data']['text_content']
            
            # 先转换为Markdown
            markdown_response = self.client.post(
                '/api/convert-format',
                data=json.dumps({
                    'text': original_text,
                    'target_format': 'markdown'
                }),
                content_type='application/json'
            )
            
            markdown_data = json.loads(markdown_response.data)
            self.assertTrue(markdown_data['success'])
            
            # 再转换回文本格式
            text_response = self.client.post(
                '/api/convert-format',
                data=json.dumps({
                    'text': original_text,
                    'target_format': 'text'
                }),
                content_type='application/json'
            )
            
            text_data = json.loads(text_response.data)
            self.assertTrue(text_data['success'])
            self.assertEqual(text_data['data']['converted_text'], original_text)
            
            # 验证两种格式都可以下载
            for format_type, content in [
                ('markdown', markdown_data['data']['converted_text']),
                ('text', text_data['data']['converted_text'])
            ]:
                download_response = self.client.post(
                    '/api/download-result',
                    data=json.dumps({
                        'content': content,
                        'format': format_type
                    }),
                    content_type='application/json'
                )
                
                self.assertEqual(download_response.status_code, 200)
    
    def test_workflow_error_recovery(self):
        """测试工作流程中的错误恢复 (Requirements 1.1, 1.2)"""
        with patch('app.ocr_service') as mock_ocr:
            mock_ocr.predict.return_value = self.ocr_results['simple_text']
            
            # 正常OCR识别
            response = self.client.post(
                '/api/ocr',
                data={'file': (self.test_images['simple'], 'test.png')},
                content_type='multipart/form-data'
            )
            
            original_text = json.loads(response.data)['data']['text_content']
            
            # 模拟格式转换失败，应该回退到文本格式
            with patch('core.text_processing.formatters.MarkdownFormatter.convert') as mock_convert:
                mock_convert.side_effect = Exception("Conversion failed")
                
                response = self.client.post(
                    '/api/convert-format',
                    data=json.dumps({
                        'text': original_text,
                        'target_format': 'markdown'
                    }),
                    content_type='application/json'
                )
                
                self.assertEqual(response.status_code, 200)
                data = json.loads(response.data)
                self.assertTrue(data['success'])
                
                # 应该回退到文本格式
                self.assertEqual(data['data']['target_format'], 'text')
                self.assertEqual(data['data']['converted_text'], original_text)
                self.assertIn('fallback_info', data['data'])
                
                # 回退后的内容仍然可以下载
                download_response = self.client.post(
                    '/api/download-result',
                    data=json.dumps({
                        'content': data['data']['converted_text'],
                        'format': 'text'
                    }),
                    content_type='application/json'
                )
                
                self.assertEqual(download_response.status_code, 200)


class TestDifferentDocumentTypes(unittest.TestCase):
    """测试不同文档类型的处理效果 - Requirements 2.1, 2.2"""
    
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        self.export_manager = ExportManager()
    
    def tearDown(self):
        """清理测试环境"""
        self.app_context.pop()
        
        # 定义不同类型的测试文档
        self.document_types = {
            'simple_paragraphs': {
                'text': """这是第一个段落的内容，包含了一些基本信息。

这是第二个段落，继续描述相关内容。

这是第三个段落，作为文档的结尾部分。""",
                'expected_elements': ['paragraphs']
            },
            
            'with_headings': {
                'text': """项目报告

概述
这是项目的概述部分，描述了项目的基本情况和目标。

技术细节
这里详细说明了项目使用的技术栈和实现方案。

结论
项目成功达到了预期的目标和要求。""",
                'expected_elements': ['headings', 'paragraphs']
            },
            
            'with_lists': {
                'text': """购物清单：
- 苹果
- 香蕉
- 橙子
- 牛奶

任务列表：
1. 完成项目报告
2. 发送邮件给客户
3. 安排下周的会议
4. 更新项目文档""",
                'expected_elements': ['lists', 'headings']
            },
            
            'complex_structure': {
                'text': """# 系统设计文档

## 概述
本文档描述了系统的整体架构和设计方案。

## 功能模块

### 用户管理模块
负责用户的注册、登录和权限管理。

主要功能：
- 用户注册
- 用户登录
- 权限验证
- 密码重置

### 数据处理模块
负责数据的采集、处理和存储。

处理流程：
1. 数据采集
2. 数据清洗
3. 数据转换
4. 数据存储

## 技术栈

### 后端技术
- Python 3.8+
- Flask框架
- SQLAlchemy ORM

### 前端技术
- HTML5/CSS3
- JavaScript ES6+
- Bootstrap框架

## 部署方案
系统支持多种部署方式，包括本地部署和云端部署。""",
                'expected_elements': ['headings', 'paragraphs', 'lists']
            },
            
            'special_characters': {
                'text': """特殊字符测试文档

这里包含一些特殊字符：
* 星号标记
# 井号标记
[] 方括号
() 圆括号
`代码标记`
**粗体文本**
_斜体文本_
~删除线~

转义测试：
\\* 转义星号
\\# 转义井号
\\[ 转义方括号""",
                'expected_elements': ['headings', 'paragraphs', 'special_chars']
            },
            
            'mixed_content': {
                'text': """混合内容文档

## 文本段落
这是一个包含多种内容类型的文档示例。

## 无序列表
- 第一项
- 第二项
  - 嵌套项目
  - 另一个嵌套项目
- 第三项

## 有序列表
1. 步骤一：准备工作
2. 步骤二：执行任务
3. 步骤三：验证结果

## 代码示例
```python
def hello_world():
    print("Hello, World!")
```

## 表格数据
| 列1 | 列2 | 列3 |
|-----|-----|-----|
| 数据1 | 数据2 | 数据3 |
| 数据4 | 数据5 | 数据6 |""",
                'expected_elements': ['headings', 'paragraphs', 'lists', 'code', 'tables']
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
    
    def test_special_characters_handling(self):
        """测试特殊字符处理 (Requirement 2.2)"""
        doc = self.document_types['special_characters']
        
        result = self.export_manager.convert_format(doc['text'], 'markdown')
        
        self.assertEqual(result['format'], 'markdown')
        markdown_content = result['content']
        
        # 验证特殊字符被正确处理（转义或保留）
        self.assertIn('特殊字符', markdown_content)
        
        # 验证转义字符被正确处理
        self.assertIn('转义', markdown_content)
    
    def test_mixed_content_document(self):
        """测试混合内容文档处理 (Requirements 2.1, 2.2)"""
        doc = self.document_types['mixed_content']
        
        result = self.export_manager.convert_format(doc['text'], 'markdown')
        
        self.assertEqual(result['format'], 'markdown')
        markdown_content = result['content']
        
        # 验证各种内容类型都被正确处理
        self.assertIn('#', markdown_content)  # 标题
        self.assertIn('-', markdown_content)  # 无序列表
        self.assertIn('1.', markdown_content)  # 有序列表
        self.assertIn('```', markdown_content)  # 代码块
        self.assertIn('|', markdown_content)  # 表格
    
    def test_empty_and_whitespace_documents(self):
        """测试空文档和空白文档处理 (Requirement 2.1)"""
        # 空文档
        result = self.export_manager.convert_format('', 'markdown')
        self.assertEqual(result['format'], 'markdown')
        self.assertEqual(result['content'], '')
        
        # 只有空白的文档
        result = self.export_manager.convert_format('   \n\n   \t  ', 'markdown')
        self.assertEqual(result['format'], 'markdown')
        # 应该返回空内容或处理后的空白
        self.assertTrue(len(result['content'].strip()) == 0)
        
        # 只有换行的文档
        result = self.export_manager.convert_format('\n\n\n', 'markdown')
        self.assertEqual(result['format'], 'markdown')
    
    def test_very_long_document_performance(self):
        """测试长文档处理性能 (Requirement 2.1)"""
        # 创建一个很长的文档
        long_paragraphs = []
        for i in range(100):
            long_paragraphs.append(f"这是第{i+1}段内容，包含了详细的描述信息。" * 5)
        
        long_text = '\n\n'.join(long_paragraphs)
        
        start_time = time.time()
        result = self.export_manager.convert_format(long_text, 'markdown')
        end_time = time.time()
        
        self.assertEqual(result['format'], 'markdown')
        self.assertGreater(len(result['content']), 0)
        
        # 验证转换时间合理（应该在合理时间内完成）
        conversion_time = end_time - start_time
        self.assertLess(conversion_time, 30.0)  # 应该在30秒内完成
        
        # 验证结果包含转换时间信息
        self.assertIn('conversion_time', result)
        self.assertGreater(result['conversion_time'], 0)
    
    def test_document_type_end_to_end_workflow(self):
        """测试不同文档类型的端到端工作流程 (Requirements 2.1, 2.2)"""
        for doc_type, doc_data in self.document_types.items():
            with self.subTest(document_type=doc_type):
                # 格式转换
                convert_response = self.client.post(
                    '/api/convert-format',
                    data=json.dumps({
                        'text': doc_data['text'],
                        'target_format': 'markdown'
                    }),
                    content_type='application/json'
                )
                
                self.assertEqual(convert_response.status_code, 200)
                convert_data = json.loads(convert_response.data)
                self.assertTrue(convert_data['success'])
                
                # 文件下载
                download_response = self.client.post(
                    '/api/download-result',
                    data=json.dumps({
                        'content': convert_data['data']['converted_text'],
                        'format': 'markdown',
                        'filename': f'{doc_type}_test'
                    }),
                    content_type='application/json'
                )
                
                self.assertEqual(download_response.status_code, 200)
                self.assertEqual(download_response.headers['Content-Type'], 'text/markdown; charset=utf-8')
                self.assertIn(f'{doc_type}_test.md', download_response.headers['Content-Disposition'])


class TestConcurrentUserAccess(unittest.TestCase):
    """测试并发用户访问场景 - Requirements 1.1, 1.2"""
    
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # 创建多个客户端实例模拟并发用户
        self.num_clients = 10
        self.clients = [self.app.test_client() for _ in range(self.num_clients)]
        
        # 测试数据
        self.test_texts = [
            f"并发测试文本 {i}：这是用于测试并发访问的文本内容。" * 10
            for i in range(self.num_clients)
        ]
        
        # 结果收集
        self.results = []
        self.errors = []
        self.lock = threading.Lock()
    
    def tearDown(self):
        """清理测试环境"""
        self.app_context.pop()
    
    def worker_format_conversion(self, client_id, client, text, target_format):
        """格式转换工作线程"""
        try:
            response = client.post(
                '/api/convert-format',
                data=json.dumps({
                    'text': text,
                    'target_format': target_format
                }),
                content_type='application/json'
            )
            
            with self.lock:
                if response.status_code == 200:
                    data = json.loads(response.data)
                    self.results.append({
                        'client_id': client_id,
                        'success': data['success'],
                        'format': data['data']['target_format'],
                        'conversion_time': data['data']['conversion_time'],
                        'content_length': len(data['data']['converted_text'])
                    })
                else:
                    self.errors.append({
                        'client_id': client_id,
                        'status_code': response.status_code,
                        'response': response.data.decode('utf-8')
                    })
                    
        except Exception as e:
            with self.lock:
                self.errors.append({
                    'client_id': client_id,
                    'error': str(e),
                    'error_type': type(e).__name__
                })
    
    def worker_download_file(self, client_id, client, content, format_type):
        """文件下载工作线程"""
        try:
            response = client.post(
                '/api/download-result',
                data=json.dumps({
                    'content': content,
                    'format': format_type,
                    'filename': f'concurrent_test_{client_id}'
                }),
                content_type='application/json'
            )
            
            with self.lock:
                if response.status_code == 200:
                    self.results.append({
                        'client_id': client_id,
                        'success': True,
                        'content_type': response.headers.get('Content-Type'),
                        'content_length': len(response.data),
                        'filename': f'concurrent_test_{client_id}'
                    })
                else:
                    self.errors.append({
                        'client_id': client_id,
                        'status_code': response.status_code,
                        'operation': 'download'
                    })
                    
        except Exception as e:
            with self.lock:
                self.errors.append({
                    'client_id': client_id,
                    'error': str(e),
                    'operation': 'download'
                })
    
    def test_concurrent_format_conversion_text(self):
        """测试并发文本格式转换 (Requirement 1.1)"""
        self.results.clear()
        self.errors.clear()
        
        threads = []
        
        # 创建并启动多个线程
        for i, (client, text) in enumerate(zip(self.clients, self.test_texts)):
            thread = threading.Thread(
                target=self.worker_format_conversion,
                args=(i, client, text, 'text')
            )
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join(timeout=60)  # 60秒超时
        
        # 验证结果
        self.assertEqual(len(self.errors), 0, f"并发文本转换测试出现错误: {self.errors}")
        self.assertEqual(len(self.results), self.num_clients)
        
        # 验证所有请求都成功
        for result in self.results:
            self.assertTrue(result['success'])
            self.assertEqual(result['format'], 'text')
            self.assertGreater(result['conversion_time'], 0)
            self.assertGreater(result['content_length'], 0)
    
    def test_concurrent_format_conversion_markdown(self):
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
- 功能 {i}.3

详细说明 {i}
这里是详细的说明内容。"""
            for i in range(self.num_clients)
        ]
        
        threads = []
        
        # 创建并启动多个线程
        for i, (client, text) in enumerate(zip(self.clients, structured_texts)):
            thread = threading.Thread(
                target=self.worker_format_conversion,
                args=(i, client, text, 'markdown')
            )
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join(timeout=60)
        
        # 验证结果
        self.assertEqual(len(self.errors), 0, f"并发Markdown转换测试出现错误: {self.errors}")
        self.assertEqual(len(self.results), self.num_clients)
        
        # 验证所有请求都成功
        for result in self.results:
            self.assertTrue(result['success'])
            self.assertEqual(result['format'], 'markdown')
            self.assertGreater(result['conversion_time'], 0)
            self.assertGreater(result['content_length'], 0)
    
    def test_concurrent_file_downloads(self):
        """测试并发文件下载 (Requirements 1.1, 1.2)"""
        self.results.clear()
        self.errors.clear()
        
        # 准备下载内容
        download_contents = [
            f"下载测试内容 {i}：这是用于测试并发下载的文件内容。" * 20
            for i in range(self.num_clients)
        ]
        
        threads = []
        
        # 创建并启动下载线程（混合文本和Markdown格式）
        for i, (client, content) in enumerate(zip(self.clients, download_contents)):
            format_type = 'markdown' if i % 2 == 0 else 'text'
            thread = threading.Thread(
                target=self.worker_download_file,
                args=(i, client, content, format_type)
            )
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join(timeout=60)
        
        # 验证结果
        self.assertEqual(len(self.errors), 0, f"并发下载测试出现错误: {self.errors}")
        self.assertEqual(len(self.results), self.num_clients)
        
        # 验证所有下载都成功
        for result in self.results:
            self.assertTrue(result['success'])
            self.assertIn('text/', result['content_type'])
            self.assertGreater(result['content_length'], 0)
            self.assertIn('concurrent_test_', result['filename'])
    
    def test_concurrent_mixed_operations(self):
        """测试并发混合操作 (Requirements 1.1, 1.2)"""
        self.results.clear()
        self.errors.clear()
        
        def mixed_operations_worker(client_id, client):
            """执行混合操作的工作线程"""
            try:
                text = f"混合操作测试 {client_id}：包含多种内容的文档。"
                
                # 步骤1: 格式转换
                convert_response = client.post(
                    '/api/convert-format',
                    data=json.dumps({
                        'text': text,
                        'target_format': 'markdown'
                    }),
                    content_type='application/json'
                )
                
                if convert_response.status_code != 200:
                    raise Exception(f"Format conversion failed: {convert_response.status_code}")
                
                convert_data = json.loads(convert_response.data)
                if not convert_data['success']:
                    raise Exception(f"Format conversion not successful: {convert_data}")
                
                # 步骤2: 文件下载
                download_response = client.post(
                    '/api/download-result',
                    data=json.dumps({
                        'content': convert_data['data']['converted_text'],
                        'format': 'markdown',
                        'filename': f'mixed_test_{client_id}'
                    }),
                    content_type='application/json'
                )
                
                if download_response.status_code != 200:
                    raise Exception(f"Download failed: {download_response.status_code}")
                
                with self.lock:
                    self.results.append({
                        'client_id': client_id,
                        'success': True,
                        'conversion_time': convert_data['data']['conversion_time'],
                        'download_size': len(download_response.data)
                    })
                    
            except Exception as e:
                with self.lock:
                    self.errors.append({
                        'client_id': client_id,
                        'error': str(e),
                        'operation': 'mixed'
                    })
        
        threads = []
        
        # 创建并启动混合操作线程
        for i, client in enumerate(self.clients):
            thread = threading.Thread(
                target=mixed_operations_worker,
                args=(i, client)
            )
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join(timeout=90)  # 混合操作需要更长时间
        
        # 验证结果
        self.assertEqual(len(self.errors), 0, f"并发混合操作测试出现错误: {self.errors}")
        self.assertEqual(len(self.results), self.num_clients)
        
        # 验证所有操作都成功
        for result in self.results:
            self.assertTrue(result['success'])
            self.assertGreater(result['conversion_time'], 0)
            self.assertGreater(result['download_size'], 0)
    
    def test_concurrent_stress_test(self):
        """并发压力测试 (Requirements 1.1, 1.2)"""
        # 增加并发数量进行压力测试
        stress_clients = [self.app.test_client() for _ in range(20)]
        stress_results = []
        stress_errors = []
        stress_lock = threading.Lock()
        
        def stress_worker(client_id, client):
            """压力测试工作线程"""
            try:
                # 随机选择操作类型
                operations = ['text_conversion', 'markdown_conversion', 'download']
                operation = random.choice(operations)
                
                if operation in ['text_conversion', 'markdown_conversion']:
                    target_format = 'text' if operation == 'text_conversion' else 'markdown'
                    text = f"压力测试 {client_id}：{''.join(random.choices(string.ascii_letters, k=100))}"
                    
                    response = client.post(
                        '/api/convert-format',
                        data=json.dumps({
                            'text': text,
                            'target_format': target_format
                        }),
                        content_type='application/json'
                    )
                    
                    if response.status_code == 200:
                        data = json.loads(response.data)
                        with stress_lock:
                            stress_results.append({
                                'client_id': client_id,
                                'operation': operation,
                                'success': data['success']
                            })
                    else:
                        with stress_lock:
                            stress_errors.append({
                                'client_id': client_id,
                                'operation': operation,
                                'status_code': response.status_code
                            })
                
                elif operation == 'download':
                    content = f"下载内容 {client_id}"
                    response = client.post(
                        '/api/download-result',
                        data=json.dumps({
                            'content': content,
                            'format': 'text'
                        }),
                        content_type='application/json'
                    )
                    
                    with stress_lock:
                        if response.status_code == 200:
                            stress_results.append({
                                'client_id': client_id,
                                'operation': operation,
                                'success': True
                            })
                        else:
                            stress_errors.append({
                                'client_id': client_id,
                                'operation': operation,
                                'status_code': response.status_code
                            })
                            
            except Exception as e:
                with stress_lock:
                    stress_errors.append({
                        'client_id': client_id,
                        'error': str(e)
                    })
        
        # 使用线程池执行压力测试
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = []
            for i, client in enumerate(stress_clients):
                future = executor.submit(stress_worker, i, client)
                futures.append(future)
            
            # 等待所有任务完成
            concurrent.futures.wait(futures, timeout=120)
        
        # 验证压力测试结果
        total_operations = len(stress_results) + len(stress_errors)
        success_rate = len(stress_results) / total_operations if total_operations > 0 else 0
        
        # 至少80%的操作应该成功
        self.assertGreater(success_rate, 0.8, 
                          f"压力测试成功率过低: {success_rate:.2%}, 错误: {stress_errors}")
        
        # 验证有足够的操作被执行
        self.assertGreater(total_operations, 15, "压力测试执行的操作数量不足")


class TestSystemIntegrationAndPerformance(unittest.TestCase):
    """系统集成和性能测试 - Requirements 1.1, 1.2, 2.1, 2.2"""
    
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
    
    def test_api_response_time_performance(self):
        """测试API响应时间性能"""
        test_text = "性能测试文本内容" * 100  # 创建较大的测试文本
        
        # 测试格式转换API响应时间
        start_time = time.time()
        response = self.client.post(
            '/api/convert-format',
            data=json.dumps({
                'text': test_text,
                'target_format': 'markdown'
            }),
            content_type='application/json'
        )
        end_time = time.time()
        
        self.assertEqual(response.status_code, 200)
        response_time = end_time - start_time
        
        # API响应时间应该在合理范围内（5秒内）
        self.assertLess(response_time, 5.0, f"API响应时间过长: {response_time:.2f}秒")
        
        # 测试下载API响应时间
        data = json.loads(response.data)
        content = data['data']['converted_text']
        
        start_time = time.time()
        download_response = self.client.post(
            '/api/download-result',
            data=json.dumps({
                'content': content,
                'format': 'markdown'
            }),
            content_type='application/json'
        )
        end_time = time.time()
        
        self.assertEqual(download_response.status_code, 200)
        download_time = end_time - start_time
        
        # 下载API响应时间应该很快（2秒内）
        self.assertLess(download_time, 2.0, f"下载API响应时间过长: {download_time:.2f}秒")
    
    def test_memory_usage_stability(self):
        """测试内存使用稳定性"""
        import psutil
        import gc
        
        # 获取初始内存使用
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 执行多次操作
        for i in range(50):
            test_text = f"内存测试 {i}：" + "测试内容" * 100
            
            # 格式转换
            response = self.client.post(
                '/api/convert-format',
                data=json.dumps({
                    'text': test_text,
                    'target_format': 'markdown'
                }),
                content_type='application/json'
            )
            
            self.assertEqual(response.status_code, 200)
            
            # 文件下载
            data = json.loads(response.data)
            download_response = self.client.post(
                '/api/download-result',
                data=json.dumps({
                    'content': data['data']['converted_text'],
                    'format': 'markdown'
                }),
                content_type='application/json'
            )
            
            self.assertEqual(download_response.status_code, 200)
            
            # 每10次操作检查一次内存
            if i % 10 == 0:
                gc.collect()  # 强制垃圾回收
                current_memory = process.memory_info().rss / 1024 / 1024
                memory_increase = current_memory - initial_memory
                
                # 内存增长应该在合理范围内（不超过100MB）
                self.assertLess(memory_increase, 100, 
                              f"内存使用增长过多: {memory_increase:.2f}MB")
    
    def test_error_handling_consistency(self):
        """测试错误处理一致性"""
        error_test_cases = [
            {
                'endpoint': '/api/convert-format',
                'data': 'invalid json',
                'content_type': 'application/json',
                'expected_code': 'INVALID_JSON'
            },
            {
                'endpoint': '/api/convert-format',
                'data': json.dumps({'text': 'test', 'target_format': 'invalid'}),
                'content_type': 'application/json',
                'expected_code': 'VALIDATION_ERROR'
            },
            {
                'endpoint': '/api/download-result',
                'data': json.dumps({'content': '', 'format': 'text'}),
                'content_type': 'application/json',
                'expected_code': 'VALIDATION_ERROR'
            }
        ]
        
        for test_case in error_test_cases:
            with self.subTest(endpoint=test_case['endpoint']):
                response = self.client.post(
                    test_case['endpoint'],
                    data=test_case['data'],
                    content_type=test_case['content_type']
                )
                
                self.assertEqual(response.status_code, 400)
                data = json.loads(response.data)
                
                # 验证错误响应格式一致性
                self.assertFalse(data['success'])
                self.assertIn('error', data)
                self.assertIn('message', data['error'])
                self.assertIn('code', data['error'])
                
                # 验证特定错误代码
                if 'expected_code' in test_case:
                    self.assertEqual(data['error']['code'], test_case['expected_code'])


if __name__ == '__main__':
    # 设置测试套件
    test_suite = unittest.TestSuite()
    
    # 添加测试类
    test_classes = [
        TestEndToEndUserFlows,
        TestDifferentDocumentTypes,
        TestConcurrentUserAccess,
        TestSystemIntegrationAndPerformance
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # 输出详细的测试结果摘要
    print(f"\n{'='*60}")
    print(f"综合集成测试摘要 (Task 9.2):")
    print(f"{'='*60}")
    print(f"运行测试: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    print(f"跳过: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    
    if result.failures:
        print(f"\n失败的测试:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print(f"\n错误的测试:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback.split('Exception:')[-1].strip()}")
    
    success_rate = (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100
    print(f"\n成功率: {success_rate:.1f}%")
    print(f"{'='*60}")
    
    # 测试覆盖的需求
    print(f"\n测试覆盖的需求:")
    print(f"- Requirement 1.1: 用户格式选择和实时转换 ✓")
    print(f"- Requirement 1.2: OCR结果转换为markdown格式 ✓")
    print(f"- Requirement 2.1: 智能识别文档结构元素 ✓")
    print(f"- Requirement 2.2: 处理不同类型文档内容 ✓")
    
    print(f"\n测试场景覆盖:")
    print(f"- 端到端用户流程测试 ✓")
    print(f"- 不同文档类型处理测试 ✓")
    print(f"- 并发用户访问测试 ✓")
    print(f"- 系统集成和性能测试 ✓")
    
    # 如果有失败或错误，退出时返回非零状态码
    if result.failures or result.errors:
        print(f"\n⚠️  部分测试未通过，请检查上述失败和错误信息")
        sys.exit(1)
    else:
        print(f"\n✅ 所有综合集成测试通过！")
        sys.exit(0)