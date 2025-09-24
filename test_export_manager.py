"""ExportManager单元测试"""
import unittest
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.document_processing.export_manager import ExportManager


class TestExportManager(unittest.TestCase):
    """ExportManager测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.export_manager = ExportManager()
        self.sample_text = """第一章 概述
这是一个测试文档。

主要功能包括：
- 文本分析
- 格式转换
- 文件导出

1. 第一个功能
2. 第二个功能

这是结尾段落。"""
    
    def test_init(self):
        """测试初始化"""
        self.assertIsNotNone(self.export_manager.analyzer)
        self.assertIsNotNone(self.export_manager.formatters)
        self.assertIn('markdown', self.export_manager.formatters)
    
    def test_get_supported_formats(self):
        """测试获取支持的格式列表"""
        formats = self.export_manager.get_supported_formats()
        self.assertIsInstance(formats, list)
        self.assertIn('text', formats)
        self.assertIn('markdown', formats)
    
    def test_is_format_supported(self):
        """测试格式支持检查"""
        # 支持的格式
        self.assertTrue(self.export_manager.is_format_supported('text'))
        self.assertTrue(self.export_manager.is_format_supported('markdown'))
        self.assertTrue(self.export_manager.is_format_supported('TEXT'))  # 大小写不敏感
        self.assertTrue(self.export_manager.is_format_supported(' markdown '))  # 空格处理
        
        # 不支持的格式
        self.assertFalse(self.export_manager.is_format_supported('pdf'))
        self.assertFalse(self.export_manager.is_format_supported('html'))
        self.assertFalse(self.export_manager.is_format_supported(''))
        self.assertFalse(self.export_manager.is_format_supported(None))
        self.assertFalse(self.export_manager.is_format_supported(123))
    
    def test_validate_conversion_request(self):
        """测试转换请求验证"""
        # 有效请求
        result = self.export_manager.validate_conversion_request("test text", "markdown")
        self.assertTrue(result['valid'])
        self.assertEqual(len(result['errors']), 0)
        
        # 无效文本类型
        result = self.export_manager.validate_conversion_request(123, "markdown")
        self.assertFalse(result['valid'])
        self.assertIn("Text must be a string", result['errors'])
        
        # 无效格式
        result = self.export_manager.validate_conversion_request("test", "pdf")
        self.assertFalse(result['valid'])
        self.assertIn("Unsupported format", result['errors'][0])
        
        # 空文本警告
        result = self.export_manager.validate_conversion_request("   ", "text")
        self.assertTrue(result['valid'])
        self.assertIn("empty or contains only whitespace", result['warnings'][0])
    
    def test_convert_format_to_text(self):
        """测试转换为文本格式"""
        result = self.export_manager.convert_format(self.sample_text, "text")
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result['content'], self.sample_text)
        self.assertEqual(result['format'], 'text')
        self.assertEqual(result['original_text'], self.sample_text)
        self.assertIn('conversion_time', result)
        self.assertIsInstance(result['conversion_time'], float)
    
    def test_convert_format_to_markdown(self):
        """测试转换为Markdown格式"""
        result = self.export_manager.convert_format(self.sample_text, "markdown")
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result['format'], 'markdown')
        self.assertEqual(result['original_text'], self.sample_text)
        self.assertIn('conversion_time', result)
        self.assertIsInstance(result['conversion_time'], float)
        
        # 检查转换后的内容
        content = result['content']
        self.assertIsInstance(content, str)
        self.assertGreater(len(content), 0)
        
        # 检查结构信息
        if 'structure_info' in result:
            structure_info = result['structure_info']
            self.assertIsInstance(structure_info, dict)
            self.assertIn('headings_count', structure_info)
            self.assertIn('paragraphs_count', structure_info)
            self.assertIn('lists_count', structure_info)
    
    def test_convert_format_case_insensitive(self):
        """测试格式转换大小写不敏感"""
        result1 = self.export_manager.convert_format(self.sample_text, "MARKDOWN")
        result2 = self.export_manager.convert_format(self.sample_text, "markdown")
        result3 = self.export_manager.convert_format(self.sample_text, " Markdown ")
        
        self.assertEqual(result1['format'], 'markdown')
        self.assertEqual(result2['format'], 'markdown')
        self.assertEqual(result3['format'], 'markdown')
    
    def test_convert_format_unsupported(self):
        """测试不支持的格式转换"""
        with self.assertRaises(ValueError) as context:
            self.export_manager.convert_format(self.sample_text, "pdf")
        
        self.assertIn("Unsupported format", str(context.exception))
        self.assertIn("pdf", str(context.exception))
    
    def test_convert_format_invalid_input_type(self):
        """测试无效输入类型"""
        with self.assertRaises(TypeError):
            self.export_manager.convert_format(123, "markdown")
        
        with self.assertRaises(TypeError):
            self.export_manager.convert_format("test", 123)
    
    def test_convert_format_empty_text(self):
        """测试空文本转换"""
        result = self.export_manager.convert_format("", "markdown")
        self.assertEqual(result['content'], "")
        self.assertEqual(result['format'], 'markdown')
    
    def test_convert_format_whitespace_only(self):
        """测试仅包含空白字符的文本"""
        result = self.export_manager.convert_format("   \n\t  ", "markdown")
        self.assertEqual(result['format'], 'markdown')
        # 内容可能为空或保持原样，取决于formatter的实现
    
    def test_conversion_time_measurement(self):
        """测试转换时间测量"""
        result = self.export_manager.convert_format(self.sample_text, "markdown")
        
        self.assertIn('conversion_time', result)
        self.assertIsInstance(result['conversion_time'], float)
        self.assertGreaterEqual(result['conversion_time'], 0)
        self.assertLess(result['conversion_time'], 10)  # 应该在10秒内完成
    
    def test_error_handling_with_fallback(self):
        """测试错误处理和回退机制"""
        # 创建一个会抛出异常的mock formatter
        class FailingFormatter:
            def convert(self, text):
                raise Exception("Conversion failed")
        
        # 临时替换formatter来测试错误处理
        original_formatter = self.export_manager.formatters['markdown']
        self.export_manager.formatters['markdown'] = FailingFormatter()
        
        try:
            result = self.export_manager.convert_format(self.sample_text, "markdown")
            
            # 应该回退到文本格式
            self.assertEqual(result['format'], 'text')
            self.assertEqual(result['content'], self.sample_text)
            self.assertIn('error', result)
            self.assertTrue(result['error']['fallback_applied'])
            
        finally:
            # 恢复原始formatter
            self.export_manager.formatters['markdown'] = original_formatter
    
    def test_create_download_file_text(self):
        """测试创建文本下载文件"""
        content = "这是测试内容"
        result = self.export_manager.create_download_file(content, "text")
        
        self.assertIsInstance(result, dict)
        self.assertIn('filepath', result)
        self.assertIn('filename', result)
        self.assertIn('content_type', result)
        self.assertIn('file_size', result)
        self.assertIn('format', result)
        
        # 检查文件信息
        self.assertEqual(result['format'], 'text')
        self.assertEqual(result['content_type'], 'text/plain')
        self.assertTrue(result['filename'].endswith('.txt'))
        self.assertGreater(result['file_size'], 0)
        
        # 检查文件是否真的创建了
        self.assertTrue(os.path.exists(result['filepath']))
        
        # 检查文件内容
        with open(result['filepath'], 'r', encoding='utf-8') as f:
            file_content = f.read()
        self.assertEqual(file_content, content)
        
        # 清理文件
        self.export_manager.cleanup_download_file(result['filepath'])
    
    def test_create_download_file_markdown(self):
        """测试创建Markdown下载文件"""
        content = "# 标题\n\n这是内容"
        result = self.export_manager.create_download_file(content, "markdown")
        
        self.assertEqual(result['format'], 'markdown')
        self.assertEqual(result['content_type'], 'text/markdown')
        self.assertTrue(result['filename'].endswith('.md'))
        
        # 检查文件内容
        with open(result['filepath'], 'r', encoding='utf-8') as f:
            file_content = f.read()
        self.assertEqual(file_content, content)
        
        # 清理文件
        self.export_manager.cleanup_download_file(result['filepath'])
    
    def test_create_download_file_with_custom_filename(self):
        """测试使用自定义文件名创建下载文件"""
        content = "测试内容"
        custom_filename = "my_document"
        
        result = self.export_manager.create_download_file(content, "text", custom_filename)
        
        self.assertEqual(result['filename'], "my_document.txt")
        self.assertTrue(os.path.exists(result['filepath']))
        
        # 清理文件
        self.export_manager.cleanup_download_file(result['filepath'])
    
    def test_create_download_file_invalid_format(self):
        """测试使用无效格式创建下载文件"""
        with self.assertRaises(ValueError) as context:
            self.export_manager.create_download_file("content", "pdf")
        
        self.assertIn("Unsupported format", str(context.exception))
    
    def test_create_download_file_invalid_input_type(self):
        """测试无效输入类型"""
        with self.assertRaises(TypeError):
            self.export_manager.create_download_file(123, "text")
        
        with self.assertRaises(TypeError):
            self.export_manager.create_download_file("content", 123)
    
    def test_generate_filename(self):
        """测试文件名生成"""
        filename_text = self.export_manager._generate_filename("text")
        filename_md = self.export_manager._generate_filename("markdown")
        
        self.assertTrue(filename_text.startswith("ocr_result_"))
        self.assertTrue(filename_text.endswith(".txt"))
        self.assertTrue(filename_md.endswith(".md"))
        
        # 检查时间戳格式
        import re
        pattern = r"ocr_result_\d{8}_\d{6}\.(txt|md)"
        self.assertTrue(re.match(pattern, filename_text))
        self.assertTrue(re.match(pattern, filename_md))
    
    def test_ensure_file_extension(self):
        """测试文件扩展名确保"""
        # 没有扩展名的情况
        result = self.export_manager._ensure_file_extension("document", "text")
        self.assertEqual(result, "document.txt")
        
        # 有错误扩展名的情况
        result = self.export_manager._ensure_file_extension("document.pdf", "markdown")
        self.assertEqual(result, "document.md")
        
        # 有正确扩展名的情况
        result = self.export_manager._ensure_file_extension("document.txt", "text")
        self.assertEqual(result, "document.txt")
    
    def test_get_file_info(self):
        """测试获取文件信息"""
        ext, mime = self.export_manager._get_file_info("text")
        self.assertEqual(ext, ".txt")
        self.assertEqual(mime, "text/plain")
        
        ext, mime = self.export_manager._get_file_info("markdown")
        self.assertEqual(ext, ".md")
        self.assertEqual(mime, "text/markdown")
        
        # 未知格式应该回退到text
        ext, mime = self.export_manager._get_file_info("unknown")
        self.assertEqual(ext, ".txt")
        self.assertEqual(mime, "text/plain")
    
    def test_cleanup_download_file(self):
        """测试清理下载文件"""
        # 创建一个文件
        content = "测试内容"
        result = self.export_manager.create_download_file(content, "text")
        filepath = result['filepath']
        
        # 确认文件存在
        self.assertTrue(os.path.exists(filepath))
        
        # 清理文件
        success = self.export_manager.cleanup_download_file(filepath)
        self.assertTrue(success)
        self.assertFalse(os.path.exists(filepath))
        
        # 尝试清理不存在的文件
        success = self.export_manager.cleanup_download_file(filepath)
        self.assertFalse(success)
    
    def test_get_download_file_info(self):
        """测试获取下载文件信息"""
        # 创建一个文件
        content = "测试内容"
        result = self.export_manager.create_download_file(content, "markdown")
        filepath = result['filepath']
        
        try:
            # 获取文件信息
            info = self.export_manager.get_download_file_info(filepath)
            
            self.assertIsInstance(info, dict)
            self.assertEqual(info['filepath'], filepath)
            self.assertTrue(info['filename'].endswith('.md'))
            self.assertEqual(info['content_type'], 'text/markdown')
            self.assertEqual(info['format'], 'markdown')
            self.assertGreater(info['file_size'], 0)
            self.assertIn('created_time', info)
            self.assertIn('modified_time', info)
            
        finally:
            # 清理文件
            self.export_manager.cleanup_download_file(filepath)
    
    def test_get_download_file_info_not_found(self):
        """测试获取不存在文件的信息"""
        with self.assertRaises(FileNotFoundError):
            self.export_manager.get_download_file_info("/nonexistent/file.txt")


if __name__ == '__main__':
    unittest.main()