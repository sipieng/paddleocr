"""格式转换器模块"""
from .analyzer import TextAnalyzer, TextStructure, Heading, ListItem
from abc import ABC, abstractmethod
from typing import List, Dict
import re


class BaseFormatter(ABC):
    """格式转换器基类"""
    
    @abstractmethod
    def convert(self, text: str) -> str:
        """转换文本格式"""
        pass


class MarkdownFormatter(BaseFormatter):
    """Markdown格式转换器"""
    
    def __init__(self, analyzer: TextAnalyzer = None):
        self.analyzer = analyzer or TextAnalyzer()
    
    def convert(self, text: str) -> str:
        """将纯文本转换为Markdown格式"""
        if not text or not text.strip():
            return ""
        
        # 将文本分割为行
        lines = text.split('\n')
        
        # 分析文本结构
        structure = self.analyzer.analyze_structure(lines)
        
        # 构建markdown内容
        markdown_parts = []
        
        # 处理标题
        if structure.headings:
            heading_lines = self._get_heading_lines(structure.headings, lines)
            markdown_parts.extend(heading_lines)
        
        # 处理列表
        if structure.lists:
            list_lines = self._get_list_lines(structure.lists, lines)
            markdown_parts.extend(list_lines)
        
        # 处理段落
        if structure.paragraphs:
            formatted_paragraphs = self.format_paragraphs(structure.paragraphs)
            if formatted_paragraphs:
                markdown_parts.append(formatted_paragraphs)
        
        # 如果没有识别到任何结构，直接返回格式化的段落
        if not markdown_parts:
            return self.format_paragraphs(lines)
        
        # 合并所有部分，确保适当的间距
        return self._merge_markdown_parts(markdown_parts)
    
    def _get_heading_lines(self, headings: List, lines: List[str]) -> List[str]:
        """获取标题对应的markdown行"""
        heading_lines = []
        for heading in headings:
            if hasattr(heading, 'text') and hasattr(heading, 'level'):
                formatted = self._format_single_heading(heading.text, heading.level)
                heading_lines.append(formatted)
        return heading_lines
    
    def _get_list_lines(self, lists: List, lines: List[str]) -> List[str]:
        """获取列表对应的markdown行"""
        list_lines = []
        for list_item in lists:
            if hasattr(list_item, 'text') and hasattr(list_item, 'type'):
                formatted = self._format_single_list_item(
                    list_item.text, 
                    list_item.type, 
                    getattr(list_item, 'level', 0)
                )
                list_lines.append(formatted)
        return list_lines
    
    def _get_paragraph_lines(self, paragraphs: List[str]) -> List[str]:
        """获取段落对应的markdown行"""
        paragraph_lines = []
        for paragraph in paragraphs:
            if paragraph.strip():
                paragraph_lines.append(paragraph.strip())
        return paragraph_lines
    
    def _merge_markdown_parts(self, parts: List[str]) -> str:
        """合并markdown部分，确保适当的间距"""
        if not parts:
            return ""
        
        result = []
        for i, part in enumerate(parts):
            if part.strip():
                result.append(part)
                # 在标题后添加空行
                if part.startswith('#') and i < len(parts) - 1:
                    result.append("")
        
        return '\n'.join(result)
    
    def format_headings(self, headings: List[Dict]) -> str:
        """格式化标题"""
        if not headings:
            return ""
        
        formatted_headings = []
        for heading in headings:
            if isinstance(heading, dict):
                text = heading.get('text', '')
                level = heading.get('level', 1)
            else:
                # 处理Heading对象
                text = getattr(heading, 'text', '')
                level = getattr(heading, 'level', 1)
            
            if text.strip():
                formatted = self._format_single_heading(text, level)
                formatted_headings.append(formatted)
        
        return '\n\n'.join(formatted_headings)
    
    def format_lists(self, lists: List[Dict]) -> str:
        """格式化列表"""
        if not lists:
            return ""
        
        formatted_lists = []
        current_group = []
        last_line_number = -1
        
        for list_item in lists:
            if isinstance(list_item, dict):
                text = list_item.get('text', '')
                item_type = list_item.get('type', 'unordered')
                level = list_item.get('level', 0)
                line_number = list_item.get('line_number', 0)
            else:
                # 处理ListItem对象
                text = getattr(list_item, 'text', '')
                item_type = getattr(list_item, 'type', 'unordered')
                level = getattr(list_item, 'level', 0)
                line_number = getattr(list_item, 'line_number', 0)
            
            if not text.strip():
                continue
            
            # 检查是否是连续的列表项（行号相差不超过2）
            if last_line_number >= 0 and line_number - last_line_number > 2:
                # 结束当前列表组
                if current_group:
                    formatted_lists.append('\n'.join(current_group))
                    current_group = []
            
            # 格式化当前列表项
            formatted_item = self._format_single_list_item(text, item_type, level)
            current_group.append(formatted_item)
            last_line_number = line_number
        
        # 添加最后一个列表组
        if current_group:
            formatted_lists.append('\n'.join(current_group))
        
        return '\n\n'.join(formatted_lists)
    
    def format_paragraphs(self, paragraphs: List[str]) -> str:
        """格式化段落"""
        if not paragraphs:
            return ""
        
        formatted_paragraphs = []
        
        for paragraph in paragraphs:
            if isinstance(paragraph, str):
                cleaned_paragraph = self._clean_paragraph_text(paragraph)
                if cleaned_paragraph:
                    formatted_paragraphs.append(cleaned_paragraph)
            elif isinstance(paragraph, list):
                # 如果传入的是行列表，合并为段落
                combined_text = ' '.join(line.strip() for line in paragraph if line.strip())
                cleaned_paragraph = self._clean_paragraph_text(combined_text)
                if cleaned_paragraph:
                    formatted_paragraphs.append(cleaned_paragraph)
        
        # 段落之间用双换行分隔
        return '\n\n'.join(formatted_paragraphs)
    
    def _clean_paragraph_text(self, text: str) -> str:
        """清理段落文本，处理换行和特殊字符"""
        import re
        
        if not text or not text.strip():
            return ""
        
        # 去除首尾空白
        text = text.strip()
        
        # 处理内部换行：将单个换行替换为空格，保留双换行
        # 先标记双换行，然后替换单换行，最后恢复双换行
        text = text.replace('\n\n', '<<DOUBLE_NEWLINE>>')
        text = text.replace('\n', ' ')
        text = text.replace('<<DOUBLE_NEWLINE>>', '\n\n')
        
        # 处理多个连续空格
        text = re.sub(r'\s+', ' ', text)
        
        # 转义markdown特殊字符（但保留基本标点）
        text = self._escape_markdown_characters(text)
        
        return text.strip()
    
    def _escape_markdown_characters(self, text: str) -> str:
        """转义markdown特殊字符"""
        # 需要转义的markdown特殊字符
        # 注意：我们只转义可能造成格式问题的字符，保留基本的标点符号
        special_chars = {
            '\\': '\\\\',  # 反斜杠必须首先转义
            '`': '\\`',    # 代码标记
            '*': '\\*',    # 强调标记（但在中文环境中可能不需要）
            '_': '\\_',    # 强调标记
            '[': '\\[',    # 链接标记
            ']': '\\]',    # 链接标记
            '(': '\\(',    # 链接标记
            ')': '\\)',    # 链接标记
            '#': '\\#',    # 标题标记（行首）
            '+': '\\+',    # 列表标记
            '-': '\\-',    # 列表标记（但需要谨慎，可能是正常的连字符）
            '.': '\\.',    # 有序列表标记（数字后的点）
            '!': '\\!',    # 图片标记
        }
        
        # 只转义行首的特殊字符或明确会造成格式问题的字符
        result = text
        
        # 转义所有的#（避免被误认为标题）
        result = result.replace('#', '\\#')
        
        # 转义行首的数字+点（避免被误认为有序列表）
        result = re.sub(r'^(\d+)\.', r'\1\\.', result, flags=re.MULTILINE)
        
        # 转义行首的-、+、*（避免被误认为无序列表）
        result = re.sub(r'^([-+*])\s', r'\\\1 ', result, flags=re.MULTILINE)
        
        # 转义代码标记
        result = result.replace('`', '\\`')
        
        # 转义链接标记（但要小心不要转义正常的括号）
        result = re.sub(r'\[([^\]]*)\]\(([^)]*)\)', r'\\[\1\\]\\(\2\\)', result)
        
        return result
    
    def _format_single_heading(self, text: str, level: int) -> str:
        """格式化单个标题（内部辅助方法）"""
        if not text or not text.strip():
            return ""
        
        # 确保level在1-6范围内（Markdown标准）
        level = max(1, min(6, level))
        
        # 清理标题文本
        clean_text = self._clean_heading_text(text)
        
        # 生成markdown标题
        return f"{'#' * level} {clean_text}"
    
    def _clean_heading_text(self, text: str) -> str:
        """清理标题文本，移除不必要的标点和格式"""
        import re
        
        # 去除首尾空白
        text = text.strip()
        
        # 移除常见的标题编号格式
        # 移除 "1." "1.1" "1.2.3" 等数字编号
        text = re.sub(r'^\d+(\.\d+)*\.?\s*', '', text)  # 移除数字编号（包括多级编号）
        # 移除 "第一章" "第二节" 等中文编号
        text = re.sub(r'^第[一二三四五六七八九十]+[章节部分]\.?\s*', '', text)  
        # 移除 "一、" "二、" 等中文数字编号
        text = re.sub(r'^[一二三四五六七八九十]+[、\.]\s*', '', text)  
        # 移除单独的中文数字后跟空格
        text = re.sub(r'^[一二三四五六七八九十]+\s+', '', text)
        
        # 移除末尾的标点符号（标题通常不需要句号）
        text = re.sub(r'[。！？：；]+$', '', text)
        
        # 移除多余的空格
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def _format_single_list_item(self, text: str, item_type: str, level: int = 0) -> str:
        """格式化单个列表项（内部辅助方法）"""
        if not text or not text.strip():
            return ""
        
        # 清理列表项文本
        clean_text = self._clean_list_item_text(text)
        
        # 计算缩进（每级2个空格）
        indent = "  " * max(0, level)
        
        # 根据类型生成markdown列表项
        if item_type == 'ordered':
            return f"{indent}1. {clean_text}"
        else:
            return f"{indent}- {clean_text}"
    
    def _clean_list_item_text(self, text: str) -> str:
        """清理列表项文本，移除原有的列表标记"""
        import re
        
        # 去除首尾空白
        text = text.strip()
        
        # 移除原有的列表标记
        # 移除无序列表标记：- • * ·
        text = re.sub(r'^[-•*·]\s*', '', text)
        
        # 移除有序列表标记：1. 1) a. A. 一. 等
        text = re.sub(r'^\d+[\.)\s]\s*', '', text)  # 数字编号
        text = re.sub(r'^[a-zA-Z][\.)\s]\s*', '', text)  # 字母编号
        text = re.sub(r'^[一二三四五六七八九十]+[\.)\s]\s*', '', text)  # 中文数字编号
        
        # 移除多余的空格
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()


class HTMLFormatter(BaseFormatter):
    """HTML格式转换器（为未来扩展预留）"""
    
    def convert(self, text: str) -> str:
        """将纯文本转换为HTML格式"""
        # 未来扩展功能
        return text