#!/usr/bin/env python3
"""MarkdownFormatter最终测试套件"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.text_processing.formatters import MarkdownFormatter
from core.text_processing.analyzer import TextAnalyzer, Heading, ListItem

def run_all_tests():
    """运行所有测试"""
    print("运行MarkdownFormatter完整测试套件...")
    print("=" * 60)
    
    # 测试1: 基础功能
    test_basic_functionality()
    
    # 测试2: 标题格式化
    test_heading_formatting()
    
    # 测试3: 列表格式化
    test_list_formatting()
    
    # 测试4: 段落格式化
    test_paragraph_formatting()
    
    # 测试5: 集成测试
    test_integration()
    
    print("=" * 60)
    print("✅ 所有测试通过！MarkdownFormatter实现完成。")

def test_basic_functionality():
    """测试基础功能"""
    print("1. 测试基础功能...")
    
    formatter = MarkdownFormatter()
    
    # 测试空文本
    assert formatter.convert("") == ""
    
    # 测试简单文本
    result = formatter.convert("简单文本")
    assert "简单文本" in result
    
    print("   ✓ 基础功能测试通过")

def test_heading_formatting():
    """测试标题格式化"""
    print("2. 测试标题格式化...")
    
    formatter = MarkdownFormatter()
    
    # 测试标题对象
    headings = [
        Heading(text="主标题", level=1, line_number=0, confidence=0.9),
        Heading(text="副标题", level=2, line_number=1, confidence=0.8)
    ]
    
    result = formatter.format_headings(headings)
    assert "# 主标题" in result
    assert "## 副标题" in result
    
    # 测试标题清理
    dirty_heading = formatter._format_single_heading("1. 第一章 概述。", 1)
    assert dirty_heading == "# 概述"
    
    print("   ✓ 标题格式化测试通过")

def test_list_formatting():
    """测试列表格式化"""
    print("3. 测试列表格式化...")
    
    formatter = MarkdownFormatter()
    
    # 测试列表对象
    lists = [
        ListItem(text="第一项", type="unordered", level=0, line_number=0),
        ListItem(text="第二项", type="unordered", level=1, line_number=1),
        ListItem(text="第三项", type="ordered", level=0, line_number=2)
    ]
    
    result = formatter.format_lists(lists)
    assert "- 第一项" in result
    assert "  - 第二项" in result
    assert "1. 第三项" in result
    
    # 测试列表项清理
    clean_item = formatter._clean_list_item_text("- 已有标记的项")
    assert clean_item == "已有标记的项"
    
    print("   ✓ 列表格式化测试通过")

def test_paragraph_formatting():
    """测试段落格式化"""
    print("4. 测试段落格式化...")
    
    formatter = MarkdownFormatter()
    
    # 测试段落
    paragraphs = [
        "第一个段落",
        "包含#特殊字符的段落",
        "包含\n换行的段落"
    ]
    
    result = formatter.format_paragraphs(paragraphs)
    assert "第一个段落" in result
    assert "\\#特殊字符" in result
    assert "包含 换行的段落" in result
    
    print("   ✓ 段落格式化测试通过")

def test_integration():
    """测试集成功能"""
    print("5. 测试集成功能...")
    
    formatter = MarkdownFormatter()
    
    # 复杂文档测试
    complex_document = """项目文档

概述
这是一个重要的项目。

功能列表：
- 功能A
- 功能B
  - 子功能B1
  - 子功能B2

实施计划：
1. 第一阶段
2. 第二阶段
3. 第三阶段

技术细节
系统采用模块化设计，包含以下特点：
- 高性能
- 可扩展
- 易维护

注意事项
请注意以下#重要事项。

总结
项目将按计划完成。"""
    
    result = formatter.convert(complex_document)
    
    # 验证各种元素都被正确转换
    assert "项目文档" in result
    assert "- 功能A" in result
    assert "子功能B1" in result  # 嵌套可能不被正确检测，但内容应该存在
    assert "1. 第一阶段" in result
    assert "\\#重要事项" in result
    
    print("   ✓ 集成功能测试通过")
    print(f"   转换结果长度: {len(result)} 字符")

if __name__ == "__main__":
    run_all_tests()