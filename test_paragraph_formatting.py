#!/usr/bin/env python3
"""测试段落格式化功能"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.text_processing.formatters import MarkdownFormatter

def test_paragraph_formatting():
    """测试段落格式化功能"""
    print("测试段落格式化功能...")
    
    formatter = MarkdownFormatter()
    
    # 测试1: 基本段落格式化
    paragraphs = [
        "这是第一个段落。",
        "这是第二个段落，包含更多内容。",
        "这是第三个段落。"
    ]
    
    result = formatter.format_paragraphs(paragraphs)
    expected = "这是第一个段落。\n\n这是第二个段落，包含更多内容。\n\n这是第三个段落。"
    assert result == expected, f"基本段落格式化失败:\n期望: {expected}\n实际: {result}"
    print("✓ 基本段落格式化测试通过")
    
    # 测试2: 包含换行的段落处理
    paragraphs_with_newlines = [
        "这是一个\n包含换行的段落。",
        "这是另一个\n\n包含双换行的段落。"
    ]
    
    result = formatter.format_paragraphs(paragraphs_with_newlines)
    expected = "这是一个 包含换行的段落。\n\n这是另一个 包含双换行的段落。"
    assert result == expected, f"换行处理失败:\n期望: {expected}\n实际: {result}"
    print("✓ 换行处理测试通过")
    
    # 测试3: 多余空格处理
    paragraphs_with_spaces = [
        "  这是一个   包含多余空格   的段落。  ",
        "这是另一个\t包含制表符\t的段落。"
    ]
    
    result = formatter.format_paragraphs(paragraphs_with_spaces)
    expected = "这是一个 包含多余空格 的段落。\n\n这是另一个 包含制表符 的段落。"
    assert result == expected, f"空格处理失败:\n期望: {expected}\n实际: {result}"
    print("✓ 空格处理测试通过")
    
    # 测试4: Markdown特殊字符转义
    paragraphs_with_special = [
        "这个段落包含#标题标记",
        "1.这是行首数字列表标记",
        "- 这是行首列表标记",
        "这个段落包含`代码标记`"
    ]
    
    result = formatter.format_paragraphs(paragraphs_with_special)
    # 验证特殊字符被正确转义
    assert "\\#标题标记" in result, "标题标记应该被转义"
    assert "1\\.这是行首数字列表标记" in result, "行首数字列表标记应该被转义"
    assert "\\- 这是行首列表标记" in result, "行首列表标记应该被转义"
    assert "\\`代码标记\\`" in result, "代码标记应该被转义"
    print("✓ Markdown特殊字符转义测试通过")
    
    # 测试5: 空段落和空白段落处理
    paragraphs_with_empty = [
        "有效段落1",
        "",
        "   ",
        "有效段落2"
    ]
    
    result = formatter.format_paragraphs(paragraphs_with_empty)
    expected = "有效段落1\n\n有效段落2"
    assert result == expected, f"空段落处理失败:\n期望: {expected}\n实际: {result}"
    print("✓ 空段落处理测试通过")
    
    # 测试6: 行列表输入处理
    line_lists = [
        ["第一行", "第二行", "第三行"],
        ["单独一行"]
    ]
    
    result = formatter.format_paragraphs(line_lists)
    expected = "第一行 第二行 第三行\n\n单独一行"
    assert result == expected, f"行列表处理失败:\n期望: {expected}\n实际: {result}"
    print("✓ 行列表处理测试通过")
    
    # 测试7: 段落文本清理方法
    clean_result = formatter._clean_paragraph_text("  这是一个\n包含换行和   多余空格的文本  ")
    expected_clean = "这是一个 包含换行和 多余空格的文本"
    assert clean_result == expected_clean, f"段落文本清理失败: {clean_result}"
    print("✓ 段落文本清理方法测试通过")
    
    # 测试8: Markdown字符转义方法
    escape_result = formatter._escape_markdown_characters("# 标题 和 `代码` 和 1. 列表")
    assert "\\#" in escape_result, "标题标记应该被转义"
    assert "\\`" in escape_result, "代码标记应该被转义"
    print("✓ Markdown字符转义方法测试通过")
    
    # 测试行首数字转义
    escape_result2 = formatter._escape_markdown_characters("1. 这是行首列表")
    assert "1\\." in escape_result2, "行首列表标记应该被转义"
    print("✓ 行首数字转义测试通过")
    
    print("所有段落格式化测试通过！")

def test_integrated_paragraph_conversion():
    """测试集成的段落转换功能"""
    print("\n测试集成的段落转换功能...")
    
    formatter = MarkdownFormatter()
    
    # 包含段落的文本
    text_with_paragraphs = """这是第一个段落，包含一些基本内容。

这是第二个段落，
包含换行符。

这是第三个段落，包含#特殊字符和`代码`。"""
    
    result = formatter.convert(text_with_paragraphs)
    print(f"转换结果:\n{result}")
    
    # 验证结果包含正确格式化的段落
    assert "这是第一个段落" in result, "应该包含第一个段落"
    assert "这是第二个段落" in result, "应该包含第二个段落"
    assert "这是第三个段落" in result, "应该包含第三个段落"
    print("✓ 集成段落转换测试通过")

if __name__ == "__main__":
    test_paragraph_formatting()
    test_integrated_paragraph_conversion()