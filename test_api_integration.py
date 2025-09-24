#!/usr/bin/env python3
"""
API集成测试 - 验证所有新增API端点的集成功能
"""

import unittest
import json
import sys
import os
from unittest.mock import patch
from io import BytesIO

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app


class TestAPIIntegration(unittest.TestCase):
    """API集成测试类"""
    
    def setUp(self):
        """测试前设置"""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        # 测试数据
        self.test_text = """项目报告
概述
这是项目的概述部分。

功能列表：
- 功能一
- 功能二
- 功能三

详细说明
每个功能的详细说明..."""
    
    @patch('app.ocr_service')
    def test_complete_workflow_text_to_markdown(self, mock_ocr_service):
        """测试完整工作流：OCR → 格式转换 → 下载"""
        # 步骤1：模拟OCR识别
        mock_ocr_service.predict.return_value = [
            {
                'rec_texts': self.test_text.split('\n'),
                'rec_scores': [0.95] * len(self.test_text.split('\n'))
            }
        ]
        
        # 创建测试图片文件
        test_image_data = b'fake_image_data'
        test_file = (BytesIO(test_image_data), 'test.jpg')
        
        # 执行OCR
        ocr_response = self.client.post('/api/ocr',
                                      data={'file': test_file},
                                      content_type='multipart/form-data')
        
        self.assertEqual(ocr_response.status_code, 200)
        ocr_data = json.loads(ocr_response.data)
        self.assertTrue(ocr_data['success'])
        self.assertIn('available_formats', ocr_data['data'])
        
        # 获取OCR识别的文本
        ocr_text = ocr_data['data']['text_content']
        
        # 步骤2：格式转换为Markdown
        convert_response = self.client.post('/api/convert-format',
                                          json={
                                              'text': ocr_text,
                                              'target_format': 'markdown'
                                          },
                                          content_type='application/json')
        
        self.assertEqual(convert_response.status_code, 200)
        convert_data = json.loads(convert_response.data)
        self.assertTrue(convert_data['success'])
        self.assertEqual(convert_data['data']['target_format'], 'markdown')
        
        # 获取转换后的Markdown文本
        markdown_text = convert_data['data']['converted_text']
        self.assertIn('#', markdown_text)  # 应该包含Markdown标题语法
        
        # 步骤3：下载Markdown文件
        download_response = self.client.post('/api/download-result',
                                           json={
                                               'content': markdown_text,
                                               'format': 'markdown'
                                           },
                                           content_type='application/json')
        
        self.assertEqual(download_response.status_code, 200)
        self.assertEqual(download_response.mimetype, 'text/markdown')
        self.assertIn('attachment', download_response.headers.get('Content-Disposition', ''))
        self.assertIn('.md', download_response.headers.get('Content-Disposition', ''))
    
    def test_format_conversion_api_comprehensive(self):
        """测试格式转换API的全面功能"""
        # 测试转换为文本格式
        response = self.client.post('/api/convert-format',
                                  json={
                                      'text': self.test_text,
                                      'target_format': 'text'
                                  },
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['target_format'], 'text')
        self.assertEqual(data['data']['converted_text'], self.test_text)
        
        # 测试转换为Markdown格式
        response = self.client.post('/api/convert-format',
                                  json={
                                      'text': self.test_text,
                                      'target_format': 'markdown'
                                  },
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['target_format'], 'markdown')
        self.assertIn('#', data['data']['converted_text'])
        
        # 测试不支持的格式
        response = self.client.post('/api/convert-format',
                                  json={
                                      'text': self.test_text,
                                      'target_format': 'pdf'
                                  },
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertEqual(data['error']['code'], 'VALIDATION_ERROR')
    
    def test_download_api_comprehensive(self):
        """测试下载API的全面功能"""
        # 测试下载文本文件
        response = self.client.post('/api/download-result',
                                  json={
                                      'content': self.test_text,
                                      'format': 'text'
                                  },
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'text/plain')
        self.assertIn('.txt', response.headers.get('Content-Disposition', ''))
        
        # 测试下载Markdown文件
        markdown_content = "# 标题\n\n这是内容。"
        response = self.client.post('/api/download-result',
                                  json={
                                      'content': markdown_content,
                                      'format': 'markdown'
                                  },
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'text/markdown')
        self.assertIn('.md', response.headers.get('Content-Disposition', ''))
        
        # 测试自定义文件名
        response = self.client.post('/api/download-result',
                                  json={
                                      'content': self.test_text,
                                      'format': 'text',
                                      'filename': 'custom_report'
                                  },
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('custom_report.txt', response.headers.get('Content-Disposition', ''))
    
    def test_api_error_handling_consistency(self):
        """测试API错误处理的一致性"""
        # 测试格式转换API的错误处理
        response = self.client.post('/api/convert-format',
                                  data='invalid json',
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('error', data)
        self.assertIn('code', data['error'])
        
        # 测试下载API的错误处理
        response = self.client.post('/api/download-result',
                                  data='invalid json',
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('error', data)
        self.assertIn('code', data['error'])
        
        # 测试非JSON请求
        response = self.client.post('/api/convert-format',
                                  data='text=hello',
                                  content_type='application/x-www-form-urlencoded')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['error']['code'], 'INVALID_CONTENT_TYPE')
    
    def test_api_response_structure_consistency(self):
        """测试API响应结构的一致性"""
        # 成功响应结构
        response = self.client.post('/api/convert-format',
                                  json={
                                      'text': 'test',
                                      'target_format': 'text'
                                  },
                                  content_type='application/json')
        
        data = json.loads(response.data)
        self.assertIn('success', data)
        self.assertIn('data', data)
        self.assertTrue(data['success'])
        
        # 错误响应结构
        response = self.client.post('/api/convert-format',
                                  json={
                                      'text': 'test',
                                      'target_format': 'invalid'
                                  },
                                  content_type='application/json')
        
        data = json.loads(response.data)
        self.assertIn('success', data)
        self.assertIn('error', data)
        self.assertFalse(data['success'])
        self.assertIn('message', data['error'])
        self.assertIn('code', data['error'])
    
    def test_api_http_methods(self):
        """测试API HTTP方法限制"""
        # 格式转换API只支持POST
        response = self.client.get('/api/convert-format')
        self.assertEqual(response.status_code, 405)
        
        response = self.client.put('/api/convert-format')
        self.assertEqual(response.status_code, 405)
        
        # 下载API只支持POST
        response = self.client.get('/api/download-result')
        self.assertEqual(response.status_code, 405)
        
        response = self.client.put('/api/download-result')
        self.assertEqual(response.status_code, 405)
    
    @patch('app.ocr_service')
    def test_ocr_api_integration_with_new_features(self, mock_ocr_service):
        """测试OCR API与新功能的集成"""
        # 模拟OCR服务
        mock_ocr_service.predict.return_value = [
            {
                'rec_texts': ['集成测试', '新功能验证'],
                'rec_scores': [0.95, 0.90]
            }
        ]
        
        # 创建测试图片文件
        test_image_data = b'fake_image_data'
        test_file = (BytesIO(test_image_data), 'test.jpg')
        
        # 执行OCR
        response = self.client.post('/api/ocr',
                                  data={'file': test_file},
                                  content_type='multipart/form-data')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        # 验证OCR响应包含新字段
        self.assertIn('available_formats', data['data'])
        available_formats = data['data']['available_formats']
        self.assertIn('text', available_formats)
        self.assertIn('markdown', available_formats)
        
        # 验证可以直接使用OCR结果进行格式转换
        ocr_text = data['data']['text_content']
        
        convert_response = self.client.post('/api/convert-format',
                                          json={
                                              'text': ocr_text,
                                              'target_format': 'markdown'
                                          },
                                          content_type='application/json')
        
        self.assertEqual(convert_response.status_code, 200)
        convert_data = json.loads(convert_response.data)
        self.assertTrue(convert_data['success'])


if __name__ == '__main__':
    print("运行API集成测试...")
    unittest.main(verbosity=2)