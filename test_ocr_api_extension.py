#!/usr/bin/env python3
"""
测试OCR API扩展功能 - 验证available_formats字段
"""

import unittest
import json
import sys
import os
from unittest.mock import patch, MagicMock
from io import BytesIO

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app


class TestOCRAPIExtension(unittest.TestCase):
    """OCR API扩展测试类"""
    
    def setUp(self):
        """测试前设置"""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
    
    @patch('app.ocr_service')
    def test_ocr_response_includes_available_formats(self, mock_ocr_service):
        """测试OCR响应包含available_formats字段"""
        # 模拟OCR服务
        mock_ocr_service.predict.return_value = [
            {
                'rec_texts': ['测试文本', '第二行文本'],
                'rec_scores': [0.95, 0.90]
            }
        ]
        
        # 创建测试图片文件
        test_image_data = b'fake_image_data'
        test_file = (BytesIO(test_image_data), 'test.jpg')
        
        # 发送OCR请求
        response = self.client.post('/api/ocr',
                                  data={'file': test_file},
                                  content_type='multipart/form-data')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('data', data)
        
        response_data = data['data']
        
        # 检查原有字段仍然存在
        required_fields = ['text_content', 'line_count', 'process_time']
        for field in required_fields:
            self.assertIn(field, response_data, f"Missing required field: {field}")
        
        # 检查新增的available_formats字段
        self.assertIn('available_formats', response_data, "Missing available_formats field")
        
        # 验证available_formats的内容
        available_formats = response_data['available_formats']
        self.assertIsInstance(available_formats, list, "available_formats should be a list")
        self.assertIn('text', available_formats, "available_formats should include 'text'")
        self.assertIn('markdown', available_formats, "available_formats should include 'markdown'")
        
        # 验证格式列表不为空
        self.assertGreater(len(available_formats), 0, "available_formats should not be empty")
    
    @patch('app.ocr_service')
    def test_ocr_backward_compatibility(self, mock_ocr_service):
        """测试OCR API的向后兼容性"""
        # 模拟OCR服务
        mock_ocr_service.predict.return_value = [
            {
                'rec_texts': ['兼容性测试'],
                'rec_scores': [0.98]
            }
        ]
        
        # 创建测试图片文件
        test_image_data = b'fake_image_data'
        test_file = (BytesIO(test_image_data), 'test.jpg')
        
        # 发送OCR请求
        response = self.client.post('/api/ocr',
                                  data={'file': test_file},
                                  content_type='multipart/form-data')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        
        response_data = data['data']
        
        # 验证所有原有字段的数据类型和内容
        self.assertIsInstance(response_data['text_content'], str)
        self.assertIsInstance(response_data['line_count'], int)
        self.assertIsInstance(response_data['process_time'], (int, float))
        
        # 验证文本内容正确
        self.assertEqual(response_data['text_content'], '兼容性测试')
        self.assertEqual(response_data['line_count'], 1)
        self.assertGreaterEqual(response_data['process_time'], 0)
    
    @patch('app.ocr_service')
    def test_ocr_empty_result_includes_formats(self, mock_ocr_service):
        """测试OCR空结果也包含available_formats"""
        # 模拟OCR服务返回空结果
        mock_ocr_service.predict.return_value = []
        
        # 创建测试图片文件
        test_image_data = b'fake_image_data'
        test_file = (BytesIO(test_image_data), 'test.jpg')
        
        # 发送OCR请求
        response = self.client.post('/api/ocr',
                                  data={'file': test_file},
                                  content_type='multipart/form-data')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        
        response_data = data['data']
        
        # 即使OCR结果为空，也应该包含available_formats
        self.assertIn('available_formats', response_data)
        self.assertIsInstance(response_data['available_formats'], list)
        self.assertIn('text', response_data['available_formats'])
        self.assertIn('markdown', response_data['available_formats'])
        
        # 验证空结果的其他字段
        self.assertEqual(response_data['text_content'], '')
        self.assertEqual(response_data['line_count'], 0)
    
    def test_ocr_without_service_initialized(self):
        """测试OCR服务未初始化时的响应"""
        # 确保OCR服务未初始化
        with patch('app.ocr_service', None):
            # 创建测试图片文件
            test_image_data = b'fake_image_data'
            test_file = (BytesIO(test_image_data), 'test.jpg')
            
            # 发送OCR请求
            response = self.client.post('/api/ocr',
                                      data={'file': test_file},
                                      content_type='multipart/form-data')
            
            self.assertEqual(response.status_code, 503)
            
            data = json.loads(response.data)
            self.assertFalse(data['success'])
            self.assertIn('error', data)
            self.assertEqual(data['error']['message'], 'OCR服务未初始化')
    
    @patch('app.ocr_service')
    def test_ocr_no_file_uploaded(self, mock_ocr_service):
        """测试未上传文件的情况"""
        # 模拟OCR服务已初始化
        mock_ocr_service.predict.return_value = []
        
        response = self.client.post('/api/ocr')
        
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('error', data)
        self.assertEqual(data['error']['message'], '没有上传文件')
    
    @patch('app.ocr_service')
    def test_ocr_response_structure_completeness(self, mock_ocr_service):
        """测试OCR响应结构的完整性"""
        # 模拟OCR服务
        mock_ocr_service.predict.return_value = [
            {
                'rec_texts': ['结构测试', '完整性验证'],
                'rec_scores': [0.95, 0.92]
            }
        ]
        
        # 创建测试图片文件
        test_image_data = b'fake_image_data'
        test_file = (BytesIO(test_image_data), 'test.jpg')
        
        # 发送OCR请求
        response = self.client.post('/api/ocr',
                                  data={'file': test_file},
                                  content_type='multipart/form-data')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        
        # 验证顶级结构
        self.assertIn('success', data)
        self.assertIn('data', data)
        self.assertTrue(data['success'])
        
        response_data = data['data']
        
        # 验证所有必需字段
        expected_fields = [
            'text_content',
            'line_count', 
            'process_time',
            'available_formats'
        ]
        
        for field in expected_fields:
            self.assertIn(field, response_data, f"Missing field: {field}")
        
        # 验证字段类型
        self.assertIsInstance(response_data['text_content'], str)
        self.assertIsInstance(response_data['line_count'], int)
        self.assertIsInstance(response_data['process_time'], (int, float))
        self.assertIsInstance(response_data['available_formats'], list)
        
        # 验证available_formats内容
        formats = response_data['available_formats']
        self.assertGreater(len(formats), 0)
        for format_name in formats:
            self.assertIsInstance(format_name, str)
        
        # 验证必需的格式存在
        self.assertIn('text', formats)
        self.assertIn('markdown', formats)


if __name__ == '__main__':
    print("运行OCR API扩展测试...")
    unittest.main(verbosity=2)