#!/usr/bin/env python3
"""
错误处理机制测试用例
测试自定义异常类和错误处理逻辑
"""

import unittest
import sys
import os
import tempfile
import json
from unittest.mock import patch, MagicMock

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.exceptions import (
    FormatConversionError, UnsupportedFormatError, TextAnalysisError,
    ValidationError, FileOperationError, APIError, RequestValidationError,
    ResourceNotFoundError, ServiceUnavailableError, RateLimitError
)
from core.document_processing.export_manager import ExportManager
from app import create_app


class TestCustomExceptions(unittest.TestCase):
    """测试自定义异常类"""
    
    def test_format_conversion_error_basic(self):
        """测试基本格式转换错误"""
        error = FormatConversionError("Test error message")
        
        self.assertEqual(error.message, "Test error message")
        self.assertEqual(error.error_code, "FORMAT_CONVERSION_ERROR")
        self.assertEqual(error.details, {})
        
        error_dict = error.to_dict()
        self.assertIn('message', error_dict)
        self.assertIn('code', error_dict)
        self.assertIn('details', error_dict)
        self.assertIn('type', error_dict)
    
    def test_format_conversion_error_with_details(self):
        """测试带详细信息的格式转换错误"""
        details = {'line_number': 5, 'column': 10}
        error = FormatConversionError(
            "Test error with details",
            error_code="CUSTOM_ERROR",
            details=details
        )
        
        self.assertEqual(error.error_code, "CUSTOM_ERROR")
        self.assertEqual(error.details, details)
    
    def test_unsupported_format_error(self):
        """测试不支持格式错误"""
        supported_formats = ['text', 'markdown']
        error = UnsupportedFormatError('pdf', supported_formats)
        
        self.assertEqual(error.format_name, 'pdf')
        self.assertEqual(error.supported_formats, supported_formats)
        self.assertIn('pdf', error.message)
        self.assertIn('text, markdown', error.message)
        
        error_dict = error.to_dict()
        self.assertEqual(error_dict['code'], 'UNSUPPORTED_FORMAT')
        self.assertEqual(error_dict['details']['requested_format'], 'pdf')
    
    def test_text_analysis_error(self):
        """测试文本分析错误"""
        original_error = ValueError("Invalid input")
        error = TextAnalysisError(
            "Analysis failed",
            analysis_stage="heading_detection",
            original_error=original_error
        )
        
        self.assertEqual(error.analysis_stage, "heading_detection")
        self.assertEqual(error.original_error, original_error)
        
        error_dict = error.to_dict()
        self.assertEqual(error_dict['details']['analysis_stage'], "heading_detection")
        self.assertEqual(error_dict['details']['original_error_type'], "ValueError")
    
    def test_validation_error(self):
        """测试验证错误"""
        error = ValidationError(
            "Invalid field value",
            field_name="target_format",
            field_value="invalid_format"
        )
        
        self.assertEqual(error.field_name, "target_format")
        self.assertEqual(error.field_value, "invalid_format")
        
        error_dict = error.to_dict()
        self.assertEqual(error_dict['details']['field_name'], "target_format")
    
    def test_file_operation_error(self):
        """测试文件操作错误"""
        original_error = OSError("Permission denied")
        error = FileOperationError(
            "File creation failed",
            operation="create_file",
            filepath="/tmp/test.txt",
            original_error=original_error
        )
        
        self.assertEqual(error.operation, "create_file")
        self.assertEqual(error.filepath, "/tmp/test.txt")
        self.assertEqual(error.original_error, original_error)
    
    def test_api_error(self):
        """测试API错误"""
        error = APIError(
            "API request failed",
            status_code=400,
            error_code="BAD_REQUEST",
            details={'param': 'invalid'}
        )
        
        self.assertEqual(error.status_code, 400)
        self.assertEqual(error.error_code, "BAD_REQUEST")
        
        error_dict = error.to_dict()
        self.assertEqual(error_dict['details']['param'], 'invalid')
    
    def test_request_validation_error(self):
        """测试请求验证错误"""
        validation_errors = ["Field 'text' is required", "Invalid format"]
        error = RequestValidationError(
            "Request validation failed",
            validation_errors=validation_errors
        )
        
        self.assertEqual(error.status_code, 400)
        self.assertEqual(error.validation_errors, validation_errors)
        
        error_dict = error.to_dict()
        self.assertEqual(error_dict['details']['validation_errors'], validation_errors)


class TestExportManagerErrorHandling(unittest.TestCase):
    """测试ExportManager的错误处理"""
    
    def setUp(self):
        self.export_manager = ExportManager()
    
    def test_convert_format_invalid_text_type(self):
        """测试无效文本类型"""
        with self.assertRaises(ValidationError) as context:
            self.export_manager.convert_format(123, 'text')
        
        error = context.exception
        self.assertEqual(error.field_name, 'text')
        self.assertIn('string', error.message)
    
    def test_convert_format_invalid_format_type(self):
        """测试无效格式类型"""
        with self.assertRaises(ValidationError) as context:
            self.export_manager.convert_format('test text', 123)
        
        error = context.exception
        self.assertEqual(error.field_name, 'target_format')
    
    def test_convert_format_unsupported_format(self):
        """测试不支持的格式"""
        with self.assertRaises(UnsupportedFormatError) as context:
            self.export_manager.convert_format('test text', 'pdf')
        
        error = context.exception
        self.assertEqual(error.format_name, 'pdf')
        self.assertIn('text', error.supported_formats)
        self.assertIn('markdown', error.supported_formats)
    
    def test_convert_format_fallback_on_error(self):
        """测试格式转换失败时的回退机制"""
        # 模拟格式转换器抛出异常
        with patch.object(self.export_manager.formatters['markdown'], 'convert') as mock_convert:
            mock_convert.side_effect = Exception("Conversion failed")
            
            result = self.export_manager.convert_format('test text', 'markdown')
            
            # 应该回退到文本格式
            self.assertEqual(result['format'], 'text')
            self.assertEqual(result['content'], 'test text')
            self.assertIn('error', result)
            self.assertTrue(result['error']['fallback_applied'])
    
    def test_create_download_file_invalid_content_type(self):
        """测试创建下载文件时的无效内容类型"""
        with self.assertRaises(ValidationError) as context:
            self.export_manager.create_download_file(123, 'text')
        
        error = context.exception
        self.assertEqual(error.field_name, 'content')
    
    def test_create_download_file_unsupported_format(self):
        """测试创建下载文件时的不支持格式"""
        with self.assertRaises(UnsupportedFormatError) as context:
            self.export_manager.create_download_file('test content', 'pdf')
        
        error = context.exception
        self.assertEqual(error.format_name, 'pdf')
    
    def test_create_download_file_success(self):
        """测试成功创建下载文件"""
        content = "Test content for download"
        result = self.export_manager.create_download_file(content, 'text')
        
        self.assertIn('filepath', result)
        self.assertIn('filename', result)
        self.assertIn('content_type', result)
        self.assertIn('file_size', result)
        self.assertEqual(result['format'], 'text')
        
        # 验证文件确实被创建
        self.assertTrue(os.path.exists(result['filepath']))
        
        # 验证文件内容
        with open(result['filepath'], 'r', encoding='utf-8') as f:
            file_content = f.read()
        self.assertEqual(file_content, content)
        
        # 清理文件
        self.export_manager.cleanup_download_file(result['filepath'])
    
    def test_validation_request_empty_text(self):
        """测试验证空文本请求"""
        result = self.export_manager.validate_conversion_request('', 'text')
        
        self.assertTrue(result['valid'])  # 空文本是有效的，但会有警告
        self.assertIn('warnings', result)
        self.assertTrue(len(result['warnings']) > 0)
    
    def test_validation_request_invalid_format(self):
        """测试验证无效格式请求"""
        result = self.export_manager.validate_conversion_request('test', 'invalid_format')
        
        self.assertFalse(result['valid'])
        self.assertIn('errors', result)
        self.assertTrue(len(result['errors']) > 0)
    
    def test_validation_request_large_text(self):
        """测试验证大文本请求"""
        large_text = 'x' * 200000  # 200KB
        result = self.export_manager.validate_conversion_request(large_text, 'text')
        
        self.assertTrue(result['valid'])
        self.assertIn('warnings', result)
        # 应该有关于大文本的警告
        warning_messages = ' '.join(result['warnings'])
        self.assertIn('large', warning_messages.lower())


class TestAPIErrorHandling(unittest.TestCase):
    """测试API错误处理"""
    
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
    
    def tearDown(self):
        self.app_context.pop()
    
    def test_convert_format_invalid_json(self):
        """测试格式转换API的无效JSON"""
        response = self.client.post(
            '/api/convert-format',
            data='invalid json',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertEqual(data['error']['code'], 'INVALID_JSON')
    
    def test_convert_format_missing_content_type(self):
        """测试格式转换API缺少Content-Type"""
        response = self.client.post(
            '/api/convert-format',
            data=json.dumps({'text': 'test', 'target_format': 'markdown'})
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertEqual(data['error']['code'], 'INVALID_CONTENT_TYPE')
    
    def test_convert_format_empty_request_body(self):
        """测试格式转换API空请求体"""
        response = self.client.post(
            '/api/convert-format',
            data='',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertEqual(data['error']['code'], 'EMPTY_REQUEST_BODY')
    
    def test_convert_format_unsupported_format(self):
        """测试格式转换API不支持的格式"""
        response = self.client.post(
            '/api/convert-format',
            data=json.dumps({
                'text': 'test text',
                'target_format': 'pdf'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertEqual(data['error']['code'], 'UNSUPPORTED_FORMAT')
        self.assertIn('supported_formats', data['error']['details'])
    
    def test_convert_format_success(self):
        """测试格式转换API成功"""
        response = self.client.post(
            '/api/convert-format',
            data=json.dumps({
                'text': 'Test text content',
                'target_format': 'text'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('data', data)
        self.assertEqual(data['data']['target_format'], 'text')
    
    def test_download_result_invalid_json(self):
        """测试下载API的无效JSON"""
        response = self.client.post(
            '/api/download-result',
            data='invalid json',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertEqual(data['error']['code'], 'INVALID_JSON')
    
    def test_download_result_empty_content(self):
        """测试下载API空内容"""
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
    
    def test_download_result_unsupported_format(self):
        """测试下载API不支持的格式"""
        response = self.client.post(
            '/api/download-result',
            data=json.dumps({
                'content': 'test content',
                'format': 'pdf'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertEqual(data['error']['code'], 'UNSUPPORTED_FORMAT')


class TestErrorRecoveryMechanisms(unittest.TestCase):
    """测试错误恢复机制"""
    
    def setUp(self):
        self.export_manager = ExportManager()
    
    def test_format_conversion_fallback(self):
        """测试格式转换失败时的回退机制"""
        # 模拟markdown转换器失败
        with patch.object(self.export_manager.formatters['markdown'], 'convert') as mock_convert:
            mock_convert.side_effect = Exception("Markdown conversion failed")
            
            result = self.export_manager.convert_format('test text', 'markdown')
            
            # 验证回退到文本格式
            self.assertEqual(result['format'], 'text')
            self.assertEqual(result['content'], 'test text')
            self.assertIn('error', result)
            self.assertTrue(result['error']['fallback_applied'])
            self.assertIn('Markdown conversion failed', result['error']['message'])
    
    def test_structure_analysis_fallback(self):
        """测试结构分析失败时的回退机制"""
        # 模拟分析器失败
        with patch.object(self.export_manager.analyzer, 'analyze_structure') as mock_analyze:
            mock_analyze.side_effect = Exception("Analysis failed")
            
            # 转换应该仍然成功，但没有结构信息
            result = self.export_manager.convert_format('test text', 'markdown')
            
            # 应该成功转换（可能使用基本格式）
            self.assertEqual(result['format'], 'markdown')
            # 不应该有structure_info，因为分析失败了
            self.assertNotIn('structure_info', result)
    
    def test_file_creation_error_handling(self):
        """测试文件创建错误处理"""
        # 模拟文件创建失败
        with patch('tempfile.gettempdir') as mock_tempdir:
            mock_tempdir.return_value = '/nonexistent/directory'
            
            with self.assertRaises(FileOperationError) as context:
                self.export_manager.create_download_file('test content', 'text')
            
            error = context.exception
            self.assertEqual(error.operation, 'create_file')
            self.assertIn('Failed to create download file', error.message)


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)