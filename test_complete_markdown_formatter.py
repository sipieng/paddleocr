#!/usr/bin/env python3
"""完整的MarkdownFormatter测试"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.text_processing.formatters import MarkdownFormatter

def test_complete_markdown_conversion():
    """测试完整的markdown转换功能"""
    print("测试完整的MarkdownFormatter功能...")
    
    formatter = MarkdownFormatter()
    
    # 复杂的测试文本，包含标题、列表、段落
    complex_text = """第一章 项目概述
这是项目的概述段落，包含基本信息。

主要功能：
- 文本识别功能
- 格式转换功能
- 文件下载功能

实施步骤：
1. 需求分析
2. 系统设计
3. 编码实现
4. 测试验证

1.1 技术架构
系统采用模块化设计，包含以下组件：
- 前端界面模块
- 后端API模块
- 文本处理模块

这是另一个段落，
包含换行符和特殊字符#。

总结
项目将按计划完成所有功能。"""
    
    result = formatter.convert(complex_text)
    print("转换结果:")
    print("=" * 50)
    print(result)
    print("=" * 50)
    
    # 验证结果包含各种元素
    assert "# 项目概述" in result, "应该包含转换后的标题"
    assert "- 文本识别功能" in result, "应该包含无序列表"
    assert "1. 需求分析" in result, "应该包含有序列表"
    assert "这是项目的概述段落" in result, "应该包含段落内容"
    assert "\\#" in result, "特殊字符应该被转义"
    
    print("✓ 完整markdown转换测试通过")

def test_edge_cases():
    """测试边界情况"""
    print("\n测试边界情况...")
    
    formatter = MarkdownFormatter()
    
    # 测试空文本
    result = formatter.convert("")
    assert result == "", "空文本应该返回空字符串"
    print("✓ 空文本测试通过")
    
    # 测试只有空白的文本
    result = formatter.convert("   \n\n   ")
    assert result == "", "只有空白的文本应该返回空字符串"
    print("✓ 空白文本测试通过")
    
    # 测试单行文本
    result = formatter.convert("这是一行简单的文本")
    assert "这是一行简单的文本" in result, "应该包含原文本"
    print("✓ 单行文本测试通过")
    
    print("✓ 所有边界情况测试通过")

def test_performance():
    """测试性能"""
    print("\n测试性能...")
    
    import time
    
    formatter = MarkdownFormatter()
    
    # 生成大量文本
    large_text = "\n".join([f"第{i}章 标题{i}" for i in range(1, 101)])
    large_text += "\n\n" + "\n".join([f"- 列表项{i}" for i in range(1, 101)])
    large_text += "\n\n" + "\n".join([f"这是第{i}个段落的内容。" for i in range(1, 101)])
    
    start_time = time.time()
    result = formatter.convert(large_text)
    end_time = time.time()
    
    processing_time = end_time - start_time
    print(f"处理{len(large_text)}字符的文本耗时: {processing_time:.3f}秒")
    
    assert len(result) > 0, "应该有转换结果"
    assert processing_time < 5.0, "处理时间应该在合理范围内"
    
    print("✓ 性能测试通过")

if __name__ == "__main__":
    test_complete_markdown_conversion()
    test_edge_cases()
    test_performance()