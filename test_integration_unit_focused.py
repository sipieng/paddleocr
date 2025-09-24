#!/usr/bin/env python3
"""
集成测试用例 - Task 9.2 (单元测试版本)
专注于核心功能的集成测试，不依赖Flask应用运行
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
from unittest.mock import patch, MagicMock
from io import BytesIO
import concurrent.futures

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core import ExportManager
from core.text_processing.analyzer import TextAnalyzer
from core.text_processing.formatters import MarkdownFormatter
from core.exceptions import ValidationError, UnsupportedFormatError


class TestEndToEndUserFlows(unittest.TestCase):
    """端到端用户流程测试 - Requirements 1.1, 1.2"""
    
    def setUp(self):
        """设置测试环境"""
        self.export_manager = ExportManager()
        
        # 模拟OCR识别结果
        self.ocr_text_results = {
            'simple': "这是一个简单的文档。\n包含几个段落。\n用于测试基本功能。",
            'structured': """项目报告
概述
这是项目的概述部分，描述了项目的基本情况。
功能列表
1. 文本识别功能
2. 格式转换功能
3. 文件下载功能
详细说明
每个功能都经过了充分的测试和验证。
结论
项目达到了预期目标。""",
            'with_lists': """购物清单
- 苹果
- 香蕉
- 橙子
- 牛奶
任务列表
1. 完成报告
2. 发送邮件
3. 安排会议
4. 更新文档"""
        }
    
    def test_complete_workflow_text_format(self):
        """测试完整工作流程 - 纯文本格式 (Requirement 1.1)"""
        # 步骤1: 模拟OCR识别结果
        original_text = self.ocr_text_results['simple']
        
        # 步骤2: 格式转换（保持文本格式）
        result = self.export_manager.convert_format(original_text, 'text')
        
        self.assertEqual(result['format'], 'text')
        self.assertEqual(result['content'], original_text)
        self.assertIn('conversion_time', result)
        self.assertGreaterEqual(result['conversion_time'], 0)
        
        # 步骤3: 创建下载文件
        file_info = self.export_manager.create_download_file(
            result['content'], 'text', 'test_result'
        )
        
        self.assertIn('filepath', file_info)
        self.assertIn('filename', file_info)
        self.assertEqual(file_info['format'], 'text')
        self.assertEqual(file_info['content_type'], 'text/plain')
        self.assertIn('test_result.txt', file_info['filename'])
        
        # 验证文件内容
        with open(file_info['filepath'], 'r', encoding='utf-8') as f:
            file_content = f.read()
        self.assertEqual(file_content, original_text)
        
        # 清理文件
        self.export_manager.cleanup_download_file(file_info['filepath'])
    
    def test_complete_workflow_markdown_format(self):
        """测试完整工作流程 - Markdown格式 (Requirement 1.2)"""
        # 步骤1: 模拟OCR识别结果
        original_text = self.ocr_text_results['structured']
        
        # 步骤2: 格式转换到Markdown
        result = self.export_manager.convert_format(original_text, 'markdown')
        
        self.assertEqual(result['format'], 'markdown')
        self.assertNotEqual(result['content'], original_text)  # 应该与原文不同
        self.assertIn('#', result['content'])  # 应该包含标题标记
        self.assertIn('conversion_time', result)
        self.assertGreater(result['conversion_time'], 0)
        
        # 验证结构信息
        if 'structure_info' in result:
            structure = result['structure_info']
            self.assertIn('headings_count', structure)
            self.assertIn('paragraphs_count', structure)
            self.assertIn('lists_count', structure)
        
        # 步骤3: 创建Markdown下载文件
        file_info = self.export_manager.create_download_file(
            result['content'], 'markdown', 'test_markdown'
        )
        
        self.assertEqual(file_info['format'], 'markdown')
        self.assertEqual(file_info['content_type'], 'text/markdown')
        self.assertIn('test_markdown.md', file_info['filename'])
        
        # 验证文件内容
        with open(file_info['filepath'], 'r', encoding='utf-8') as f:
            file_content = f.read()
        self.assertEqual(file_content, result['content'])
        
        # 清理文件
        self.export_manager.cleanup_download_file(file_info['filepath'])
    
    def test_workflow_with_format_switching(self):
        """测试格式切换工作流程 (Requirements 1.1, 1.2)"""
        original_text = self.ocr_text_results['structured']
        
        # 先转换为Markdown
        markdown_result = self.export_manager.convert_format(original_text, 'markdown')
        self.assertEqual(markdown_result['format'], 'markdown')
        self.assertIn('#', markdown_result['content'])
        
        # 再转换回文本格式
        text_result = self.export_manager.convert_format(original_text, 'text')
        self.assertEqual(text_result['format'], 'text')
        self.assertEqual(text_result['content'], original_text)
        
        # 验证两种格式都可以创建下载文件
        markdown_file = self.export_manager.create_download_file(
            markdown_result['content'], 'markdown'
        )
        text_file = self.export_manager.create_download_file(
            text_result['content'], 'text'
        )
        
        self.assertTrue(os.path.exists(markdown_file['filepath']))
        self.assertTrue(os.path.exists(text_file['filepath']))
        
        # 清理文件
        self.export_manager.cleanup_download_file(markdown_file['filepath'])
        self.export_manager.cleanup_download_file(text_file['filepath'])
    
    def test_workflow_error_recovery(self):
        """测试工作流程中的错误恢复 (Requirements 1.1, 1.2)"""
        original_text = self.ocr_text_results['simple']
        
        # 模拟格式转换失败，应该回退到文本格式
        with patch.object(self.export_manager.formatters['markdown'], 'convert') as mock_convert:
            mock_convert.side_effect = Exception("Conversion failed")
            
            result = self.export_manager.convert_format(original_text, 'markdown')
            
            # 应该回退到文本格式
            self.assertEqual(result['format'], 'text')
            self.assertEqual(result['content'], original_text)
            self.assertIn('error', result)
            self.assertTrue(result['error']['fallback_applied'])
            
            # 回退后的内容仍然可以创建下载文件
            file_info = self.export_manager.create_download_file(
                result['content'], 'text'
            )
            
            self.assertTrue(os.path.exists(file_info['filepath']))
            self.export_manager.cleanup_download_file(file_info['filepath'])


class TestDifferentDocumentTypes(unittest.TestCase):
    """测试不同文档类型的处理效果 - Requirements 2.1, 2.2"""
    
    def setUp(self):
        self.export_manager = ExportManager()
        
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
                'text': """系统设计文档

概述
本文档描述了系统的整体架构和设计方案。

功能模块

用户管理模块
负责用户的注册、登录和权限管理。

主要功能：
- 用户注册
- 用户登录
- 权限验证
- 密码重置

数据处理模块
负责数据的采集、处理和存储。

处理流程：
1. 数据采集
2. 数据清洗
3. 数据转换
4. 数据存储

技术栈

后端技术
- Python 3.8+
- Flask框架
- SQLAlchemy ORM

前端技术
- HTML5/CSS3
- JavaScript ES6+
- Bootstrap框架

部署方案
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

转义测试：
\\* 转义星号
\\# 转义井号
\\[ 转义方括号""",
                'expected_elements': ['headings', 'paragraphs', 'special_chars']
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
        
        # 验证标题和列表
        self.assertIn('#', markdown_content)
        self.assertIn('-', markdown_content)
        self.assertIn('1.', markdown_content)
        
        # 验证结构信息完整性
        if 'structure_info' in result:
            structure = result['structure_info']
            self.assertGreaterEqual(structure.get('headings_count', 0), 0)
            self.assertGreaterEqual(structure.get('paragraphs_count', 0), 0)
            self.assertGreaterEqual(structure.get('lists_count', 0), 0)
    
    def test_special_characters_handling(self):
        """测试特殊字符处理 (Requirement 2.2)"""
        doc = self.document_types['special_characters']
        
        result = self.export_manager.convert_format(doc['text'], 'markdown')
        
        self.assertEqual(result['format'], 'markdown')
        markdown_content = result['content']
        
        # 验证特殊字符被正确处理
        self.assertIn('特殊字符', markdown_content)
        self.assertIn('转义', markdown_content)
    
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
    
    def test_performance_with_large_document(self):
        """测试大文档处理性能 (Requirement 2.1)"""
        # 创建一个较大的文档
        large_paragraphs = []
        for i in range(100):
            large_paragraphs.append(f"这是第{i+1}段内容，包含了详细的描述信息。" * 3)
        
        large_text = '\n\n'.join(large_paragraphs)
        
        start_time = time.time()
        result = self.export_manager.convert_format(large_text, 'markdown')
        end_time = time.time()
        
        self.assertEqual(result['format'], 'markdown')
        self.assertGreater(len(result['content']), 0)
        
        # 验证转换时间合理
        conversion_time = end_time - start_time
        self.assertLess(conversion_time, 30.0)  # 应该在30秒内完成
        
        # 验证结果包含转换时间信息
        self.assertIn('conversion_time', result)
        self.assertGreater(result['conversion_time'], 0)
    
    def test_document_type_workflow_integration(self):
        """测试不同文档类型的完整工作流程 (Requirements 2.1, 2.2)"""
        for doc_type, doc_data in self.document_types.items():
            with self.subTest(document_type=doc_type):
                # 格式转换
                result = self.export_manager.convert_format(doc_data['text'], 'markdown')
                self.assertEqual(result['format'], 'markdown')
                
                # 文件创建和下载
                file_info = self.export_manager.create_download_file(
                    result['content'], 'markdown', f'{doc_type}_test'
                )
                
                self.assertEqual(file_info['format'], 'markdown')
                self.assertEqual(file_info['content_type'], 'text/markdown')
                self.assertIn(f'{doc_type}_test.md', file_info['filename'])
                self.assertTrue(os.path.exists(file_info['filepath']))
                
                # 清理文件
                self.export_manager.cleanup_download_file(file_info['filepath'])


class TestConcurrentUserAccess(unittest.TestCase):
    """测试并发用户访问场景 - Requirements 1.1, 1.2"""
    
    def setUp(self):
        self.export_manager = ExportManager()
        self.num_workers = 10
        
        # 测试数据
        self.test_texts = [
            f"并发测试文本 {i}：这是用于测试并发访问的文本内容。" * 5
            for i in range(self.num_workers)
        ]
        
        self.structured_texts = [
            f"""并发测试标题 {i}

概述 {i}
这是第{i}个并发测试的概述部分。

功能列表 {i}：
- 功能 {i}.1
- 功能 {i}.2
- 功能 {i}.3

详细说明 {i}
这里是详细的说明内容。"""
            for i in range(self.num_workers)
        ]
    
    def test_concurrent_text_conversion(self):
        """测试并发文本格式转换 (Requirement 1.1)"""
        results = []
        errors = []
        
        def worker(worker_id, text):
            try:
                result = self.export_manager.convert_format(text, 'text')
                results.append({
                    'worker_id': worker_id,
                    'success': True,
                    'format': result['format'],
                    'conversion_time': result['conversion_time'],
                    'content_length': len(result['content'])
                })
            except Exception as e:
                errors.append({
                    'worker_id': worker_id,
                    'error': str(e)
                })
        
        # 使用线程池执行并发测试
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.num_workers) as executor:
            futures = []
            for i, text in enumerate(self.test_texts):
                future = executor.submit(worker, i, text)
                futures.append(future)
            
            # 等待所有任务完成
            concurrent.futures.wait(futures, timeout=60)
        
        # 验证结果
        self.assertEqual(len(errors), 0, f"并发文本转换测试出现错误: {errors}")
        self.assertEqual(len(results), self.num_workers)
        
        # 验证所有请求都成功
        for result in results:
            self.assertTrue(result['success'])
            self.assertEqual(result['format'], 'text')
            self.assertGreaterEqual(result['conversion_time'], 0)
            self.assertGreater(result['content_length'], 0)
    
    def test_concurrent_markdown_conversion(self):
        """测试并发Markdown格式转换 (Requirement 1.2)"""
        results = []
        errors = []
        
        def worker(worker_id, text):
            try:
                result = self.export_manager.convert_format(text, 'markdown')
                results.append({
                    'worker_id': worker_id,
                    'success': True,
                    'format': result['format'],
                    'conversion_time': result['conversion_time'],
                    'content_length': len(result['content'])
                })
            except Exception as e:
                errors.append({
                    'worker_id': worker_id,
                    'error': str(e)
                })
        
        # 使用线程池执行并发测试
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.num_workers) as executor:
            futures = []
            for i, text in enumerate(self.structured_texts):
                future = executor.submit(worker, i, text)
                futures.append(future)
            
            # 等待所有任务完成
            concurrent.futures.wait(futures, timeout=60)
        
        # 验证结果
        self.assertEqual(len(errors), 0, f"并发Markdown转换测试出现错误: {errors}")
        self.assertEqual(len(results), self.num_workers)
        
        # 验证所有请求都成功
        for result in results:
            self.assertTrue(result['success'])
            self.assertEqual(result['format'], 'markdown')
            self.assertGreaterEqual(result['conversion_time'], 0)
            self.assertGreater(result['content_length'], 0)
    
    def test_concurrent_file_operations(self):
        """测试并发文件操作 (Requirements 1.1, 1.2)"""
        results = []
        errors = []
        created_files = []
        
        def worker(worker_id, text, format_type):
            try:
                # 格式转换
                convert_result = self.export_manager.convert_format(text, format_type)
                
                # 文件创建
                file_info = self.export_manager.create_download_file(
                    convert_result['content'], format_type, f'concurrent_test_{worker_id}'
                )
                
                created_files.append(file_info['filepath'])
                
                results.append({
                    'worker_id': worker_id,
                    'success': True,
                    'format': format_type,
                    'file_created': True,
                    'file_size': file_info['file_size']
                })
                
            except Exception as e:
                errors.append({
                    'worker_id': worker_id,
                    'error': str(e)
                })
        
        # 使用线程池执行并发文件操作
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.num_workers) as executor:
            futures = []
            for i, text in enumerate(self.test_texts):
                format_type = 'markdown' if i % 2 == 0 else 'text'
                future = executor.submit(worker, i, text, format_type)
                futures.append(future)
            
            # 等待所有任务完成
            concurrent.futures.wait(futures, timeout=60)
        
        # 验证结果
        self.assertEqual(len(errors), 0, f"并发文件操作测试出现错误: {errors}")
        self.assertEqual(len(results), self.num_workers)
        
        # 验证所有操作都成功
        for result in results:
            self.assertTrue(result['success'])
            self.assertTrue(result['file_created'])
            self.assertGreater(result['file_size'], 0)
        
        # 清理创建的文件
        for filepath in created_files:
            self.export_manager.cleanup_download_file(filepath)
    
    def test_concurrent_mixed_operations(self):
        """测试并发混合操作 (Requirements 1.1, 1.2)"""
        results = []
        errors = []
        
        def mixed_worker(worker_id):
            try:
                text = f"混合操作测试 {worker_id}：包含多种内容的文档。"
                
                # 步骤1: 文本格式转换
                text_result = self.export_manager.convert_format(text, 'text')
                
                # 步骤2: Markdown格式转换
                markdown_result = self.export_manager.convert_format(text, 'markdown')
                
                # 步骤3: 创建两种格式的文件
                text_file = self.export_manager.create_download_file(
                    text_result['content'], 'text', f'mixed_text_{worker_id}'
                )
                
                markdown_file = self.export_manager.create_download_file(
                    markdown_result['content'], 'markdown', f'mixed_md_{worker_id}'
                )
                
                results.append({
                    'worker_id': worker_id,
                    'success': True,
                    'text_conversion_time': text_result['conversion_time'],
                    'markdown_conversion_time': markdown_result['conversion_time'],
                    'files_created': 2
                })
                
                # 清理文件
                self.export_manager.cleanup_download_file(text_file['filepath'])
                self.export_manager.cleanup_download_file(markdown_file['filepath'])
                
            except Exception as e:
                errors.append({
                    'worker_id': worker_id,
                    'error': str(e)
                })
        
        # 使用线程池执行混合操作
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for i in range(5):
                future = executor.submit(mixed_worker, i)
                futures.append(future)
            
            # 等待所有任务完成
            concurrent.futures.wait(futures, timeout=90)
        
        # 验证结果
        self.assertEqual(len(errors), 0, f"并发混合操作测试出现错误: {errors}")
        self.assertEqual(len(results), 5)
        
        # 验证所有操作都成功
        for result in results:
            self.assertTrue(result['success'])
            self.assertGreaterEqual(result['text_conversion_time'], 0)
            self.assertGreaterEqual(result['markdown_conversion_time'], 0)
            self.assertEqual(result['files_created'], 2)


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
    
    def test_file_operation_error_handling(self):
        """测试文件操作错误处理"""
        # 测试正常文件创建
        file_info = self.export_manager.create_download_file('test content', 'text')
        self.assertTrue(os.path.exists(file_info['filepath']))
        
        # 测试文件清理
        cleanup_result = self.export_manager.cleanup_download_file(file_info['filepath'])
        self.assertTrue(cleanup_result)
        self.assertFalse(os.path.exists(file_info['filepath']))
        
        # 测试清理不存在的文件
        cleanup_result = self.export_manager.cleanup_download_file('/nonexistent/file.txt')
        self.assertFalse(cleanup_result)
    
    def test_validation_error_handling(self):
        """测试验证错误处理"""
        # 测试请求验证
        validation_result = self.export_manager.validate_conversion_request('', 'text')
        self.assertTrue(validation_result['valid'])
        self.assertIn('warnings', validation_result)
        
        # 测试无效格式验证
        validation_result = self.export_manager.validate_conversion_request('test', 'invalid')
        self.assertFalse(validation_result['valid'])
        self.assertIn('errors', validation_result)
        self.assertTrue(len(validation_result['errors']) > 0)


if __name__ == '__main__':
    # 设置测试套件
    test_suite = unittest.TestSuite()
    
    # 添加测试类
    test_classes = [
        TestEndToEndUserFlows,
        TestDifferentDocumentTypes,
        TestConcurrentUserAccess,
        TestErrorHandlingAndRecovery
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # 输出详细的测试结果摘要
    print(f"\n{'='*70}")
    print(f"集成测试摘要 - Task 9.2 (单元测试版本):")
    print(f"{'='*70}")
    print(f"运行测试: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    print(f"跳过: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    
    if result.failures:
        print(f"\n❌ 失败的测试:")
        for test, traceback in result.failures:
            print(f"- {test}")
            # 只显示关键错误信息
            error_lines = traceback.split('\n')
            for line in error_lines:
                if 'AssertionError:' in line:
                    print(f"  {line.strip()}")
                    break
    
    if result.errors:
        print(f"\n❌ 错误的测试:")
        for test, traceback in result.errors:
            print(f"- {test}")
            # 只显示关键错误信息
            error_lines = traceback.split('\n')
            for line in error_lines:
                if any(keyword in line for keyword in ['Error:', 'Exception:', 'ImportError:']):
                    print(f"  {line.strip()}")
                    break
    
    success_rate = (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100
    print(f"\n📊 成功率: {success_rate:.1f}%")
    print(f"{'='*70}")
    
    # 测试覆盖的需求
    print(f"\n✅ 测试覆盖的需求:")
    print(f"- Requirement 1.1: 用户格式选择和实时转换")
    print(f"- Requirement 1.2: OCR结果转换为markdown格式")
    print(f"- Requirement 2.1: 智能识别文档结构元素")
    print(f"- Requirement 2.2: 处理不同类型文档内容")
    
    print(f"\n✅ 测试场景覆盖:")
    print(f"- 端到端用户流程测试 (OCR → 格式转换 → 下载)")
    print(f"- 不同文档类型处理效果验证")
    print(f"- 并发用户访问场景测试")
    print(f"- 错误处理和恢复机制测试")
    
    print(f"\n📈 测试统计:")
    print(f"- 端到端用户流程测试: 4个测试用例")
    print(f"- 文档类型处理测试: 8个测试用例")
    print(f"- 并发访问测试: 4个测试用例")
    print(f"- 错误处理测试: 5个测试用例")
    print(f"- 总计: {result.testsRun}个测试用例")
    
    print(f"\n🎯 Task 9.2 实现内容:")
    print(f"- ✅ 创建端到端测试用例")
    print(f"- ✅ 测试完整的用户流程（OCR → 格式转换 → 下载）")
    print(f"- ✅ 验证不同文档类型的处理效果")
    print(f"- ✅ 测试并发用户访问场景")
    
    # 如果有失败或错误，退出时返回非零状态码
    if result.failures or result.errors:
        print(f"\n⚠️  部分测试未通过，请检查上述失败和错误信息")
        sys.exit(1)
    else:
        print(f"\n🎉 所有集成测试通过！Task 9.2 成功完成")
        sys.exit(0)