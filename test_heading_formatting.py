#!/usr/bin/env python3
"""测试标题格式化功能"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.text_processing.formatters import MarkdownFormatter
from core.text_processing.analyzer import TextAnalyzer, Heading

def test_heading_formatting():
    """测试标题格式化功能"""
    print("测试标题格式化功能...")
    
    formatter = MarkdownFormatter()
    
    # 测试1: 基本标题格式化
    headings = [
        {'text': '主标题', 'level': 1},
        {'text': '副标题', 'level': 2},
        {'text': '子标题', 'level': 3}
    ]
    
    result = formatter.format_headings(headings)
    expected_lines = ['# 主标题', '## 副标题', '### 子标题']
    expected = '\n\n'.join(expected_lines)
    
    assert result == expected, f"基本标题格式化失败:\n期望: {expected}\n实际: {result}"
    print("✓ 基本标题格式化测试通过")
    
    # 测试2: 边界情况 - 超出范围的level
    headings_boundary = [
        {'text': '超大标题', 'level': 0},  # 应该变成level 1
        {'text': '超小标题', 'level': 10}  # 应该变成level 6
    ]
    
    result = formatter.format_headings(headings_boundary)
    expected = '# 超大标题\n\n###### 超小标题'
    assert result == expected, f"边界情况测试失败:\n期望: {expected}\n实际: {result}"
    print("✓ 边界情况测试通过")
    
    # 测试3: 标题文本清理
    headings_dirty = [
        {'text': '1. 第一章 概述。', 'level': 1},
        {'text': '第二节 详细说明：', 'level': 2},
        {'text': '  三、  总结  ', 'level': 3}
    ]
    
    result = formatter.format_headings(headings_dirty)
    expected = '# 概述\n\n## 详细说明\n\n### 总结'
    assert result == expected, f"文本清理测试失败:\n期望: {expected}\n实际: {result}"
    print("✓ 标题文本清理测试通过")
    
    # 测试4: 空标题处理
    headings_empty = [
        {'text': '', 'level': 1},
        {'text': '   ', 'level': 2},
        {'text': '有效标题', 'level': 3}
    ]
    
    result = formatter.format_headings(headings_empty)
    expected = '### 有效标题'
    assert result == expected, f"空标题处理测试失败:\n期望: {expected}\n实际: {result}"
    print("✓ 空标题处理测试通过")
    
    # 测试5: 使用Heading对象
    heading_objects = [
        Heading(text='对象标题1', level=1, line_number=0, confidence=0.9),
        Heading(text='对象标题2', level=2, line_number=1, confidence=0.8)
    ]
    
    result = formatter.format_headings(heading_objects)
    expected = '# 对象标题1\n\n## 对象标题2'
    assert result == expected, f"Heading对象测试失败:\n期望: {expected}\n实际: {result}"
    print("✓ Heading对象测试通过")
    
    # 测试6: 单个标题格式化方法
    single_result = formatter._format_single_heading('测试标题', 2)
    assert single_result == '## 测试标题', f"单个标题格式化失败: {single_result}"
    print("✓ 单个标题格式化测试通过")
    
    # 测试7: 标题文本清理方法
    clean_result = formatter._clean_heading_text('1.2 第三章 测试内容。')
    assert clean_result == '测试内容', f"标题文本清理失败: {clean_result}"
    print("✓ 标题文本清理方法测试通过")
    
    print("所有标题格式化测试通过！")

def test_integrated_heading_conversion():
    """测试集成的标题转换功能"""
    print("\n测试集成的标题转换功能...")
    
    formatter = MarkdownFormatter()
    
    # 包含标题的文本
    text_with_headings = """第一章 概述
这是概述内容。

1.1 背景介绍
这是背景介绍的内容。

二、详细说明
这是详细说明的内容。"""
    
    result = formatter.convert(text_with_headings)
    print(f"转换结果:\n{result}")
    
    # 验证结果包含markdown标题
    assert '# 概述' in result or '#' in result, "结果应该包含markdown标题"
    print("✓ 集成标题转换测试通过")

if __name__ == "__main__":
    test_heading_formatting()
    test_integrated_heading_conversion()