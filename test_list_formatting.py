#!/usr/bin/env python3
"""测试列表格式化功能"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.text_processing.formatters import MarkdownFormatter
from core.text_processing.analyzer import TextAnalyzer, ListItem

def test_list_formatting():
    """测试列表格式化功能"""
    print("测试列表格式化功能...")
    
    formatter = MarkdownFormatter()
    
    # 测试1: 基本无序列表格式化
    unordered_lists = [
        {'text': '第一项', 'type': 'unordered', 'level': 0, 'line_number': 1},
        {'text': '第二项', 'type': 'unordered', 'level': 0, 'line_number': 2},
        {'text': '第三项', 'type': 'unordered', 'level': 0, 'line_number': 3}
    ]
    
    result = formatter.format_lists(unordered_lists)
    expected = '- 第一项\n- 第二项\n- 第三项'
    assert result == expected, f"基本无序列表格式化失败:\n期望: {expected}\n实际: {result}"
    print("✓ 基本无序列表格式化测试通过")
    
    # 测试2: 基本有序列表格式化
    ordered_lists = [
        {'text': '第一步', 'type': 'ordered', 'level': 0, 'line_number': 1},
        {'text': '第二步', 'type': 'ordered', 'level': 0, 'line_number': 2},
        {'text': '第三步', 'type': 'ordered', 'level': 0, 'line_number': 3}
    ]
    
    result = formatter.format_lists(ordered_lists)
    expected = '1. 第一步\n1. 第二步\n1. 第三步'
    assert result == expected, f"基本有序列表格式化失败:\n期望: {expected}\n实际: {result}"
    print("✓ 基本有序列表格式化测试通过")
    
    # 测试3: 嵌套列表格式化
    nested_lists = [
        {'text': '主项目1', 'type': 'unordered', 'level': 0, 'line_number': 1},
        {'text': '子项目1.1', 'type': 'unordered', 'level': 1, 'line_number': 2},
        {'text': '子项目1.2', 'type': 'unordered', 'level': 1, 'line_number': 3},
        {'text': '主项目2', 'type': 'unordered', 'level': 0, 'line_number': 4}
    ]
    
    result = formatter.format_lists(nested_lists)
    expected = '- 主项目1\n  - 子项目1.1\n  - 子项目1.2\n- 主项目2'
    assert result == expected, f"嵌套列表格式化失败:\n期望: {expected}\n实际: {result}"
    print("✓ 嵌套列表格式化测试通过")
    
    # 测试4: 混合类型列表
    mixed_lists = [
        {'text': '有序项1', 'type': 'ordered', 'level': 0, 'line_number': 1},
        {'text': '无序子项', 'type': 'unordered', 'level': 1, 'line_number': 2},
        {'text': '有序项2', 'type': 'ordered', 'level': 0, 'line_number': 3}
    ]
    
    result = formatter.format_lists(mixed_lists)
    expected = '1. 有序项1\n  - 无序子项\n1. 有序项2'
    assert result == expected, f"混合类型列表格式化失败:\n期望: {expected}\n实际: {result}"
    print("✓ 混合类型列表格式化测试通过")
    
    # 测试5: 列表项文本清理
    dirty_lists = [
        {'text': '- 已有标记的项', 'type': 'unordered', 'level': 0, 'line_number': 1},
        {'text': '1. 已有编号的项', 'type': 'ordered', 'level': 0, 'line_number': 2},
        {'text': '• 特殊标记的项', 'type': 'unordered', 'level': 0, 'line_number': 3}
    ]
    
    result = formatter.format_lists(dirty_lists)
    expected = '- 已有标记的项\n1. 已有编号的项\n- 特殊标记的项'
    assert result == expected, f"列表项文本清理失败:\n期望: {expected}\n实际: {result}"
    print("✓ 列表项文本清理测试通过")
    
    # 测试6: 分离的列表组
    separated_lists = [
        {'text': '组1项1', 'type': 'unordered', 'level': 0, 'line_number': 1},
        {'text': '组1项2', 'type': 'unordered', 'level': 0, 'line_number': 2},
        {'text': '组2项1', 'type': 'unordered', 'level': 0, 'line_number': 10},  # 行号跳跃
        {'text': '组2项2', 'type': 'unordered', 'level': 0, 'line_number': 11}
    ]
    
    result = formatter.format_lists(separated_lists)
    expected = '- 组1项1\n- 组1项2\n\n- 组2项1\n- 组2项2'
    assert result == expected, f"分离列表组格式化失败:\n期望: {expected}\n实际: {result}"
    print("✓ 分离列表组格式化测试通过")
    
    # 测试7: 使用ListItem对象
    list_objects = [
        ListItem(text='对象项1', type='unordered', level=0, line_number=1),
        ListItem(text='对象项2', type='ordered', level=1, line_number=2)
    ]
    
    result = formatter.format_lists(list_objects)
    expected = '- 对象项1\n  1. 对象项2'
    assert result == expected, f"ListItem对象测试失败:\n期望: {expected}\n实际: {result}"
    print("✓ ListItem对象测试通过")
    
    # 测试8: 空列表和空项处理
    empty_lists = [
        {'text': '', 'type': 'unordered', 'level': 0, 'line_number': 1},
        {'text': '   ', 'type': 'unordered', 'level': 0, 'line_number': 2},
        {'text': '有效项', 'type': 'unordered', 'level': 0, 'line_number': 3}
    ]
    
    result = formatter.format_lists(empty_lists)
    expected = '- 有效项'
    assert result == expected, f"空列表处理失败:\n期望: {expected}\n实际: {result}"
    print("✓ 空列表处理测试通过")
    
    # 测试9: 单个列表项格式化方法
    single_result = formatter._format_single_list_item('测试项', 'unordered', 1)
    assert single_result == '  - 测试项', f"单个列表项格式化失败: {single_result}"
    print("✓ 单个列表项格式化测试通过")
    
    # 测试10: 列表项文本清理方法
    clean_result = formatter._clean_list_item_text('1) 已有编号的内容')
    assert clean_result == '已有编号的内容', f"列表项文本清理失败: {clean_result}"
    print("✓ 列表项文本清理方法测试通过")
    
    print("所有列表格式化测试通过！")

def test_integrated_list_conversion():
    """测试集成的列表转换功能"""
    print("\n测试集成的列表转换功能...")
    
    formatter = MarkdownFormatter()
    
    # 包含列表的文本
    text_with_lists = """购物清单：
- 苹果
- 香蕉
- 橙子

步骤说明：
1. 准备材料
2. 开始制作
3. 完成作品"""
    
    result = formatter.convert(text_with_lists)
    print(f"转换结果:\n{result}")
    
    # 验证结果包含markdown列表
    assert '- ' in result or '1. ' in result, "结果应该包含markdown列表"
    print("✓ 集成列表转换测试通过")

if __name__ == "__main__":
    test_list_formatting()
    test_integrated_list_conversion()