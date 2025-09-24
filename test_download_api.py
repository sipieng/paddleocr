#!/usr/bin/env python3
"""
测试文件下载API端点的功能
"""

import unittest
import json
import sys
import os
import tempfile

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app


class TestDownloadAPI(unittest.TestCase):
    """文件下载API测试类"""
    
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
        
        self.test_markdown = """# 项目报告

## 概述
这是项目的概述部分。

## 功能列表：
- 功能一
- 功能二
- 功能三

## 详细说明
每个功能的详细说明..."""
    
    def test_download_text_file(self):
        """测试下载文本文件"""
        response = self.client.post('/api/download-result',
                                  json={
                                      'content': self.test_text,
                                      'format': 'text'
                                  },
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        # 检查响应头
        self.assertEqual(response.mimetype, 'text/plain')
        self.assertIn('attachment', response.headers.get('Content-Disposition', ''))
        self.assertIn('.txt', response.headers.get('Content-Disposition', ''))
        self.assertEqual(response.headers.get('X-File-Format'), 'text')
        
        # 检查文件内容（处理Windows换行符）
        actual_content = response.data.decode('utf-8').replace('\r\n', '\n')
        self.assertEqual(actual_content, self.test_text)
    
    def test_download_markdown_file(self):
        """测试下载Markdown文件"""
        response = self.client.post('/api/download-result',
                                  json={
                                      'content': self.test_markdown,
                                      'format': 'markdown'
                                  },
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        # 检查响应头
        self.assertEqual(response.mimetype, 'text/markdown')
        self.assertIn('attachment', response.headers.get('Content-Disposition', ''))
        self.assertIn('.md', response.headers.get('Content-Disposition', ''))
        self.assertEqual(response.headers.get('X-File-Format'), 'markdown')
        
        # 检查文件内容（处理Windows换行符）
        actual_content = response.data.decode('utf-8').replace('\r\n', '\n')
        self.assertEqual(actual_content, self.test_markdown)
    
    def test_download_with_custom_filename(self):
        """测试使用自定义文件名下载"""
        custom_filename = "my_report"
        
        response = self.client.post('/api/download-result',
                                  json={
                                      'content': self.test_text,
                                      'format': 'text',
                                      'filename': custom_filename
                                  },
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        # 检查文件名
        content_disposition = response.headers.get('Content-Disposition', '')
        self.assertIn(f'{custom_filename}.txt', content_disposition)
    
    def test_download_unsupported_format(self):
        """测试不支持的格式"""
        response = self.client.post('/api/download-result',
                                  json={
                                      'content': self.test_text,
                                      'format': 'pdf'
                                  },
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertEqual(data['error']['code'], 'UNSUPPORTED_FORMAT')
        self.assertIn('supported_formats', data['error'])
    
    def test_download_empty_content(self):
        """测试空内容"""
        response = self.client.post('/api/download-result',
                                  json={
                                      'content': '',
                                      'format': 'text'
                                  },
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertEqual(data['error']['code'], 'EMPTY_CONTENT')
    
    def test_download_whitespace_only_content(self):
        """测试只有空白字符的内容"""
        response = self.client.post('/api/download-result',
                                  json={
                                      'content': '   \n\t  ',
                                      'format': 'text'
                                  },
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertEqual(data['error']['code'], 'EMPTY_CONTENT')
    
    def test_download_missing_content(self):
        """测试缺少content参数"""
        response = self.client.post('/api/download-result',
                                  json={
                                      'format': 'text'
                                  },
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertEqual(data['error']['code'], 'EMPTY_CONTENT')
    
    def test_download_missing_format(self):
        """测试缺少format参数（应该使用默认值）"""
        response = self.client.post('/api/download-result',
                                  json={
                                      'content': self.test_text
                                  },
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        # 应该默认使用text格式
        self.assertEqual(response.mimetype, 'text/plain')
        self.assertEqual(response.headers.get('X-File-Format'), 'text')
    
    def test_download_invalid_content_type(self):
        """测试无效的content类型"""
        response = self.client.post('/api/download-result',
                                  json={
                                      'content': 123,  # 应该是字符串
                                      'format': 'text'
                                  },
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertEqual(data['error']['code'], 'INVALID_CONTENT_TYPE')
    
    def test_download_invalid_format_type(self):
        """测试无效的format类型"""
        response = self.client.post('/api/download-result',
                                  json={
                                      'content': self.test_text,
                                      'format': 123  # 应该是字符串
                                  },
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertEqual(data['error']['code'], 'INVALID_FORMAT_TYPE')
    
    def test_download_non_json_request(self):
        """测试非JSON请求"""
        response = self.client.post('/api/download-result',
                                  data='content=hello&format=text',
                                  content_type='application/x-www-form-urlencoded')
        
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertEqual(data['error']['code'], 'INVALID_CONTENT_TYPE')
    
    def test_download_invalid_json(self):
        """测试无效JSON"""
        response = self.client.post('/api/download-result',
                                  data='invalid json',
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn(data['error']['code'], ['INVALID_JSON', 'EMPTY_REQUEST_BODY'])
    
    def test_download_wrong_http_method(self):
        """测试错误的HTTP方法"""
        response = self.client.get('/api/download-result')
        
        self.assertEqual(response.status_code, 405)  # Method Not Allowed
    
    def test_download_large_content(self):
        """测试大内容下载"""
        large_content = "这是一个很长的文本。\n" * 1000  # 约20KB
        
        response = self.client.post('/api/download-result',
                                  json={
                                      'content': large_content,
                                      'format': 'text'
                                  },
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        # 检查内容长度
        content_length = int(response.headers.get('Content-Length', 0))
        self.assertGreater(content_length, 10000)  # 应该大于10KB
        
        # 检查文件内容（处理Windows换行符）
        actual_content = response.data.decode('utf-8').replace('\r\n', '\n')
        self.assertEqual(actual_content, large_content)
    
    def test_download_response_headers(self):
        """测试下载响应头的完整性"""
        response = self.client.post('/api/download-result',
                                  json={
                                      'content': self.test_text,
                                      'format': 'markdown'
                                  },
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        # 检查必需的响应头
        required_headers = [
            'Content-Disposition',
            'Content-Type',
            'Content-Length',
            'X-File-Format',
            'X-Generated-Timestamp'
        ]
        
        for header in required_headers:
            self.assertIn(header, response.headers, f"Missing required header: {header}")
        
        # 检查Content-Disposition格式
        content_disposition = response.headers.get('Content-Disposition')
        self.assertIn('attachment', content_disposition)
        self.assertIn('filename=', content_disposition)
        
        # 检查时间戳格式
        timestamp = response.headers.get('X-Generated-Timestamp')
        self.assertTrue(timestamp.isdigit())
        self.assertGreater(int(timestamp), 1600000000)  # 应该是合理的时间戳


if __name__ == '__main__':
    print("运行文件下载API测试...")
    unittest.main(verbosity=2)