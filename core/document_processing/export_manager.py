"""导出管理器模块"""
from ..text_processing.formatters import MarkdownFormatter, BaseFormatter
from ..text_processing.analyzer import TextAnalyzer
from ..exceptions import (
    FormatConversionError, UnsupportedFormatError, TextAnalysisError,
    ValidationError, FileOperationError
)
from typing import Dict, List, Optional
import tempfile
import os
import datetime
import logging


class ExportManager:
    """导出管理器 - 统一的导出接口"""
    
    def __init__(self):
        # 初始化文本分析器
        self.analyzer = TextAnalyzer()
        
        # 初始化格式转换器，传入分析器实例
        self.formatters = {
            'markdown': MarkdownFormatter(self.analyzer),
            # 'html': HTMLFormatter(),  # 未来扩展
            # 'pdf': PDFFormatter(),    # 未来扩展
        }
        
        # 格式转换结果缓存
        self._conversion_cache = {}
        self._cache_max_size = 50
        self._cache_stats = {
            'hits': 0,
            'misses': 0,
            'total_requests': 0
        }
        
        # 性能监控
        self._performance_monitor = {
            'conversion_times': [],
            'large_text_threshold': 5000,  # 5KB
            'large_text_conversions': 0,
            'total_conversions': 0
        }
    
    def convert_format(self, text: str, target_format: str) -> Dict:
        """转换文本格式（带缓存和性能监控）
        
        Args:
            text: 要转换的原始文本
            target_format: 目标格式 ('text' 或 'markdown')
            
        Returns:
            Dict: 包含转换结果的字典
            {
                'content': str,           # 转换后的内容
                'format': str,            # 实际使用的格式
                'original_text': str,     # 原始文本
                'conversion_time': float, # 转换耗时（秒）
                'structure_info': dict,   # 可选，结构分析信息
                'cache_hit': bool         # 是否命中缓存
            }
            
        Raises:
            ValueError: 当目标格式不支持时
            TypeError: 当输入参数类型错误时
        """
        import time
        import hashlib
        
        start_time = time.time()
        self._cache_stats['total_requests'] += 1
        self._performance_monitor['total_conversions'] += 1
        
        # 输入验证
        if not isinstance(text, str):
            raise ValidationError("Text must be a string", field_name="text", field_value=type(text).__name__)
        
        if not isinstance(target_format, str):
            raise ValidationError("Target format must be a string", field_name="target_format", field_value=type(target_format).__name__)
        
        target_format = target_format.lower().strip()
        
        # 如果目标格式是纯文本，直接返回
        if target_format == 'text':
            conversion_time = time.time() - start_time
            self._update_performance_stats(conversion_time)
            return {
                'content': text,
                'format': 'text',
                'original_text': text,
                'conversion_time': conversion_time,
                'cache_hit': False
            }
        
        # 检查格式是否支持
        if target_format not in self.formatters:
            supported_formats = ['text'] + list(self.formatters.keys())
            raise UnsupportedFormatError(target_format, supported_formats)
        
        # 检查缓存
        cache_key = self._generate_cache_key(text, target_format)
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            self._cache_stats['hits'] += 1
            conversion_time = time.time() - start_time
            cached_result['conversion_time'] = conversion_time
            cached_result['cache_hit'] = True
            return cached_result
        
        self._cache_stats['misses'] += 1
        
        # 性能监控：检测大文本
        if len(text) > self._performance_monitor['large_text_threshold']:
            self._performance_monitor['large_text_conversions'] += 1
        
        try:
            # 获取格式转换器
            formatter = self.formatters[target_format]
            
            # 执行格式转换
            converted_content = formatter.convert(text)
            
            # 如果是markdown格式，获取结构分析信息
            structure_info = None
            if target_format == 'markdown' and hasattr(formatter, 'analyzer'):
                try:
                    lines = text.split('\n')
                    structure = formatter.analyzer.analyze_structure(lines)
                    structure_info = {
                        'headings_count': len(structure.headings),
                        'paragraphs_count': len(structure.paragraphs),
                        'lists_count': len(structure.lists),
                        'tables_count': len(structure.tables) if structure.tables else 0
                    }
                except Exception:
                    # 如果结构分析失败，不影响主要转换功能
                    structure_info = None
            
            conversion_time = time.time() - start_time
            self._update_performance_stats(conversion_time)
            
            result = {
                'content': converted_content,
                'format': target_format,
                'original_text': text,
                'conversion_time': conversion_time,
                'cache_hit': False
            }
            
            if structure_info:
                result['structure_info'] = structure_info
            
            # 缓存结果（不包含时间信息）
            cache_result = result.copy()
            cache_result.pop('conversion_time', None)
            cache_result.pop('cache_hit', None)
            self._add_to_cache(cache_key, cache_result)
            
            return result
            
        except FormatConversionError:
            # 重新抛出格式转换相关的错误
            raise
        except Exception as e:
            # 转换失败时的错误处理
            conversion_time = time.time() - start_time
            self._update_performance_stats(conversion_time)
            
            # 记录错误
            logging.error(f"Format conversion failed: {e}")
            
            # 包装为格式转换错误并回退到原始文本
            fallback_result = {
                'content': text,
                'format': 'text',  # 回退到文本格式
                'original_text': text,
                'conversion_time': conversion_time,
                'cache_hit': False,
                'error': {
                    'message': str(e),
                    'type': type(e).__name__,
                    'fallback_applied': True
                }
            }
            
            return fallback_result
    
    def get_supported_formats(self) -> List[str]:
        """获取支持的格式列表
        
        Returns:
            List[str]: 支持的格式列表
        """
        return ['text'] + list(self.formatters.keys())
    
    def is_format_supported(self, format_name: str) -> bool:
        """检查格式是否支持
        
        Args:
            format_name: 格式名称
            
        Returns:
            bool: 是否支持该格式
        """
        if not isinstance(format_name, str):
            return False
        
        format_name = format_name.lower().strip()
        return format_name in self.get_supported_formats()
    
    def validate_conversion_request(self, text: str, target_format: str) -> Dict:
        """验证转换请求的有效性
        
        Args:
            text: 要转换的文本
            target_format: 目标格式
            
        Returns:
            Dict: 验证结果
            {
                'valid': bool,
                'errors': List[str],
                'warnings': List[str]
            }
        """
        errors = []
        warnings = []
        
        # 检查文本参数
        if not isinstance(text, str):
            errors.append("Text must be a string")
        elif not text.strip():
            warnings.append("Input text is empty or contains only whitespace")
        
        # 检查格式参数
        if not isinstance(target_format, str):
            errors.append("Target format must be a string")
        elif not self.is_format_supported(target_format):
            supported = ', '.join(self.get_supported_formats())
            errors.append(f"Unsupported format '{target_format}'. Supported formats: {supported}")
        
        # 检查文本长度
        if isinstance(text, str) and len(text) > 100000:  # 100KB limit
            warnings.append("Input text is very large, conversion may take longer")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def create_download_file(self, content: str, format_type: str, filename: str = None) -> Dict:
        """创建下载文件
        
        Args:
            content: 文件内容
            format_type: 文件格式类型 ('text' 或 'markdown')
            filename: 可选的文件名，如果不提供则自动生成
            
        Returns:
            Dict: 包含文件信息的字典
            {
                'filepath': str,      # 临时文件路径
                'filename': str,      # 文件名
                'content_type': str,  # MIME类型
                'file_size': int,     # 文件大小（字节）
                'format': str         # 文件格式
            }
            
        Raises:
            ValueError: 当格式类型不支持时
            OSError: 当文件创建失败时
        """
        # 输入验证
        if not isinstance(content, str):
            raise ValidationError("Content must be a string", field_name="content", field_value=type(content).__name__)
        
        if not isinstance(format_type, str):
            raise ValidationError("Format type must be a string", field_name="format_type", field_value=type(format_type).__name__)
        
        format_type = format_type.lower().strip()
        
        # 检查格式是否支持
        if not self.is_format_supported(format_type):
            raise UnsupportedFormatError(format_type, self.get_supported_formats())
        
        try:
            # 生成文件名
            if not filename:
                filename = self._generate_filename(format_type)
            else:
                # 确保文件名有正确的扩展名
                filename = self._ensure_file_extension(filename, format_type)
            
            # 获取文件扩展名和MIME类型
            file_extension, content_type = self._get_file_info(format_type)
            
            # 创建临时文件
            temp_dir = tempfile.gettempdir()
            filepath = os.path.join(temp_dir, filename)
            
            # 写入文件内容
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # 获取文件大小
            file_size = os.path.getsize(filepath)
            
            return {
                'filepath': filepath,
                'filename': filename,
                'content_type': content_type,
                'file_size': file_size,
                'format': format_type
            }
            
        except OSError as e:
            raise FileOperationError(
                message="Failed to create download file",
                operation="create_file",
                filepath=filepath if 'filepath' in locals() else None,
                original_error=e
            )
        except Exception as e:
            raise FileOperationError(
                message="Unexpected error creating download file",
                operation="create_file",
                filepath=filepath if 'filepath' in locals() else None,
                original_error=e
            )
    
    def _generate_filename(self, format_type: str) -> str:
        """生成文件名（包含时间戳）
        
        Args:
            format_type: 文件格式类型
            
        Returns:
            str: 生成的文件名
        """
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        file_extension, _ = self._get_file_info(format_type)
        return f"ocr_result_{timestamp}{file_extension}"
    
    def _ensure_file_extension(self, filename: str, format_type: str) -> str:
        """确保文件名有正确的扩展名
        
        Args:
            filename: 原始文件名
            format_type: 文件格式类型
            
        Returns:
            str: 带有正确扩展名的文件名
        """
        file_extension, _ = self._get_file_info(format_type)
        
        # 移除现有扩展名（如果有）
        name_without_ext = os.path.splitext(filename)[0]
        
        return f"{name_without_ext}{file_extension}"
    
    def _get_file_info(self, format_type: str) -> tuple:
        """获取文件扩展名和MIME类型
        
        Args:
            format_type: 文件格式类型
            
        Returns:
            tuple: (文件扩展名, MIME类型)
        """
        format_info = {
            'text': ('.txt', 'text/plain'),
            'markdown': ('.md', 'text/markdown')
        }
        
        return format_info.get(format_type, ('.txt', 'text/plain'))
    
    def cleanup_download_file(self, filepath: str) -> bool:
        """清理下载文件
        
        Args:
            filepath: 要删除的文件路径
            
        Returns:
            bool: 是否成功删除
        """
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                return True
            return False
        except OSError:
            return False
    
    def get_download_file_info(self, filepath: str) -> Dict:
        """获取下载文件信息
        
        Args:
            filepath: 文件路径
            
        Returns:
            Dict: 文件信息
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")
        
        stat = os.stat(filepath)
        filename = os.path.basename(filepath)
        file_extension = os.path.splitext(filename)[1]
        
        # 根据扩展名确定格式和MIME类型
        format_type = 'text'
        content_type = 'text/plain'
        
        if file_extension == '.md':
            format_type = 'markdown'
            content_type = 'text/markdown'
        
        return {
            'filepath': filepath,
            'filename': filename,
            'content_type': content_type,
            'file_size': stat.st_size,
            'format': format_type,
            'created_time': stat.st_ctime,
            'modified_time': stat.st_mtime
        }
    
    # 缓存和性能监控方法
    def _generate_cache_key(self, text: str, target_format: str) -> str:
        """生成缓存键"""
        import hashlib
        content = f"{text}:{target_format}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _get_from_cache(self, cache_key: str) -> Optional[Dict]:
        """从缓存获取结果"""
        return self._conversion_cache.get(cache_key)
    
    def _add_to_cache(self, cache_key: str, result: Dict):
        """添加结果到缓存"""
        if len(self._conversion_cache) >= self._cache_max_size:
            # 简单的LRU：删除最旧的条目
            oldest_key = next(iter(self._conversion_cache))
            del self._conversion_cache[oldest_key]
        
        self._conversion_cache[cache_key] = result
    
    def _update_performance_stats(self, conversion_time: float):
        """更新性能统计"""
        self._performance_monitor['conversion_times'].append(conversion_time)
        
        # 保持最近100次转换的记录
        if len(self._performance_monitor['conversion_times']) > 100:
            self._performance_monitor['conversion_times'].pop(0)
    
    def get_cache_stats(self) -> Dict:
        """获取缓存统计信息"""
        stats = self._cache_stats.copy()
        if stats['total_requests'] > 0:
            stats['hit_rate'] = stats['hits'] / stats['total_requests']
        else:
            stats['hit_rate'] = 0.0
        
        stats['cache_size'] = len(self._conversion_cache)
        stats['max_cache_size'] = self._cache_max_size
        return stats
    
    def get_performance_stats(self) -> Dict:
        """获取性能统计信息"""
        stats = self._performance_monitor.copy()
        
        if stats['conversion_times']:
            stats['average_conversion_time'] = sum(stats['conversion_times']) / len(stats['conversion_times'])
            stats['max_conversion_time'] = max(stats['conversion_times'])
            stats['min_conversion_time'] = min(stats['conversion_times'])
        else:
            stats['average_conversion_time'] = 0.0
            stats['max_conversion_time'] = 0.0
            stats['min_conversion_time'] = 0.0
        
        if stats['total_conversions'] > 0:
            stats['large_text_ratio'] = stats['large_text_conversions'] / stats['total_conversions']
        else:
            stats['large_text_ratio'] = 0.0
        
        # 添加分析器性能统计
        if hasattr(self.analyzer, 'get_performance_stats'):
            stats['analyzer_stats'] = self.analyzer.get_performance_stats()
        
        return stats
    
    def clear_cache(self):
        """清空缓存"""
        self._conversion_cache.clear()
        self._cache_stats = {
            'hits': 0,
            'misses': 0,
            'total_requests': 0
        }
    
    def reset_performance_stats(self):
        """重置性能统计"""
        self._performance_monitor = {
            'conversion_times': [],
            'large_text_threshold': 5000,
            'large_text_conversions': 0,
            'total_conversions': 0
        }
        
        if hasattr(self.analyzer, 'reset_performance_stats'):
            self.analyzer.reset_performance_stats()
    
    def optimize_cache_size(self, new_size: int):
        """优化缓存大小"""
        if new_size < 1:
            raise ValueError("Cache size must be at least 1")
        
        self._cache_max_size = new_size
        
        # 如果当前缓存超过新大小，删除最旧的条目
        while len(self._conversion_cache) > new_size:
            oldest_key = next(iter(self._conversion_cache))
            del self._conversion_cache[oldest_key]