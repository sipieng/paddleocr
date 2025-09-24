#!/usr/bin/env python3
"""
测试格式转换API端点的功能
"""

import unittest
import json
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app


class TestFormatConversionAPI(unittest.TestCase):
    """格式转换API测试类"""
    
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
    
    def test_convert_to_text_format(self):
        """测试转换为文本格式"""
        response = self.client.post('/api/convert-format',
                                  json={
                                      'text': self.test_text,
                                      'target_format': 'text'
                                  },
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('data', data)
        self.assertEqual(data['data']['target_format'], 'text')
        self.assertEqual(data['data']['converted_text'], self.test_text)
        self.assertIn('conversion_time', data['data'])
    
    def test_convert_to_markdown_format(self):
        """测试转换为Markdown格式"""
        response = self.client.post('/api/convert-format',
                                  json={
                                      'text': self.test_text,
                                      'target_format': 'markdown'
                                  },
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('data', data)
        self.assertEqual(data['data']['target_format'], 'markdown')
        self.assertIn('conversion_time', data['data'])
        
        # 检查是否包含markdown语法
        converted_text = data['data']['converted_text']
        self.assertIn('#', converted_text)  # 应该包含标题标记
        self.assertIn('-', converted_text)  # 应该包含列表标记
    
    def test_invalid_format(self):
        """测试不支持的格式"""
        response = self.client.post('/api/convert-format',
                                  json={
                                      'text': self.test_text,
                                      'target_format': 'pdf'
                                  },
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('error', data)
        self.assertEqual(data['error']['code'], 'VALIDATION_ERROR')
    
    def test_empty_text(self):
        """测试空文本"""
        response = self.client.post('/api/convert-format',
                                  json={
                                      'text': '',
                                      'target_format': 'markdown'
                                  },
                                  content_type='application/json')
        
        # 空文本应该成功处理，但可能有警告
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
    
    def test_missing_parameters(self):
        """测试缺少参数"""
        # 缺少text参数
        response = self.client.post('/api/convert-format',
                                  json={
                                      'target_format': 'markdown'
                                  },
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)  # 应该使用默认空字符串
        
        # 缺少target_format参数
        response = self.client.post('/api/convert-format',
                                  json={
                                      'text': self.test_text
                                  },
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)  # 应该使用默认text格式
        
        data = json.loads(response.data)
        self.assertEqual(data['data']['target_format'], 'text')
    
    def test_invalid_json(self):
        """测试无效JSON"""
        response = self.client.post('/api/convert-format',
                                  data='invalid json',
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn(data['error']['code'], ['INVALID_JSON', 'EMPTY_REQUEST_BODY'])
    
    def test_non_json_content_type(self):
        """测试非JSON内容类型"""
        response = self.client.post('/api/convert-format',
                                  data='text=hello&format=markdown',
                                  content_type='application/x-www-form-urlencoded')
        
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertEqual(data['error']['code'], 'INVALID_CONTENT_TYPE')
    
    def test_wrong_http_method(self):
        """测试错误的HTTP方法"""
        response = self.client.get('/api/convert-format')
        
        self.assertEqual(response.status_code, 405)  # Method Not Allowed
    
    def test_response_structure(self):
        """测试响应结构的完整性"""
        response = self.client.post('/api/convert-format',
                                  json={
                                      'text': self.test_text,
                                      'target_format': 'markdown'
                                  },
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        
        # 检查必需字段
        self.assertIn('success', data)
        self.assertIn('data', data)
        
        response_data = data['data']
        required_fields = [
            'original_text', 'converted_text', 'source_format', 
            'target_format', 'conversion_time'
        ]
        
        for field in required_fields:
            self.assertIn(field, response_data, f"Missing required field: {field}")
        
        # 检查数据类型
        self.assertIsInstance(response_data['original_text'], str)
        self.assertIsInstance(response_data['converted_text'], str)
        self.assertIsInstance(response_data['source_format'], str)
        self.assertIsInstance(response_data['target_format'], str)
        self.assertIsInstance(response_data['conversion_time'], (int, float))
    
    def test_large_text_handling(self):
        """测试大文本处理"""
        large_text = "这是一个很长的文本。\n" * 1000  # 约20KB
        
        response = self.client.post('/api/convert-format',
                                  json={
                                      'text': large_text,
                                      'target_format': 'markdown'
                                  },
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        
        # 检查转换时间是否合理（应该小于5秒）
        self.assertLess(data['data']['conversion_time'], 5.0)


if __name__ == '__main__':
    print("运行格式转换API测试...")
    unittest.main(verbosity=2)