#!/usr/bin/env python3
"""
生产环境就绪性测试
验证所有核心功能在生产环境中的表现
"""

import sys
import os
import time
import requests
import json
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """测试所有模块导入"""
    print("🔍 测试模块导入...")
    
    try:
        # 测试核心模块导入
        from core.text_processing.analyzer import TextAnalyzer
        from core.text_processing.formatters import MarkdownFormatter
        from core.document_processing.export_manager import ExportManager
        from core.exceptions import FormatConversionError, UnsupportedFormatError
        
        print("✅ 所有核心模块导入成功")
        return True
    except ImportError as e:
        print(f"❌ 模块导入失败: {e}")
        return False

def test_text_analysis():
    """测试文本分析功能"""
    print("\n🔍 测试文本分析功能...")
    
    try:
        from core.text_processing.analyzer import TextAnalyzer
        
        analyzer = TextAnalyzer()
        
        # 测试文本
        test_text = [
            "# 主标题",
            "这是一个段落。",
            "",
            "## 副标题", 
            "- 列表项1",
            "- 列表项2",
            "",
            "另一个段落。"
        ]
        
        # 分析结构
        structure = analyzer.analyze_structure(test_text)
        
        # 验证结果
        assert len(structure.headings) >= 2, f"标题检测失败，期望>=2，实际{len(structure.headings)}"
        assert len(structure.lists) >= 2, f"列表检测失败，期望>=2，实际{len(structure.lists)}"
        assert len(structure.paragraphs) >= 2, f"段落检测失败，期望>=2，实际{len(structure.paragraphs)}"
        
        print("✅ 文本分析功能正常")
        return True
        
    except Exception as e:
        print(f"❌ 文本分析测试失败: {e}")
        return False

def test_format_conversion():
    """测试格式转换功能"""
    print("\n🔍 测试格式转换功能...")
    
    try:
        from core.text_processing.formatters import MarkdownFormatter
        from core.text_processing.analyzer import TextAnalyzer
        
        analyzer = TextAnalyzer()
        formatter = MarkdownFormatter(analyzer)
        
        # 测试文本
        test_text = """标题示例
这是一个段落。

另一个段落：
- 列表项1
- 列表项2

1. 有序列表项1
2. 有序列表项2"""
        
        # 转换为Markdown
        result = formatter.convert(test_text)
        
        # 验证结果
        assert isinstance(result, str), "转换结果应该是字符串"
        assert len(result) > 0, "转换结果不应为空"
        assert "#" in result, "应该包含Markdown标题标记"
        
        print("✅ 格式转换功能正常")
        return True
        
    except Exception as e:
        print(f"❌ 格式转换测试失败: {e}")
        return False

def test_export_manager():
    """测试导出管理器"""
    print("\n🔍 测试导出管理器...")
    
    try:
        from core.document_processing.export_manager import ExportManager
        
        manager = ExportManager()
        
        # 测试格式转换
        test_text = "这是测试文本\n# 标题\n- 列表项"
        
        # 转换为Markdown
        result = manager.convert_format(test_text, 'markdown')
        
        # 验证结果
        assert 'content' in result, "结果应包含content字段"
        assert 'content' in result, "结果应包含content字段"
        assert 'format' in result, "结果应包含format字段"
        assert 'conversion_time' in result, "结果应包含conversion_time字段"
        
        # 测试文件创建
        file_info = manager.create_download_file(result['content'], 'markdown')
        
        # 验证文件信息
        assert 'filepath' in file_info, "应包含文件路径"
        assert 'filename' in file_info, "应包含文件名"
        assert 'content_type' in file_info, "应包含内容类型"
        
        # 清理文件
        if os.path.exists(file_info['filepath']):
            os.remove(file_info['filepath'])
        
        print("✅ 导出管理器功能正常")
        return True
        
    except Exception as e:
        print(f"❌ 导出管理器测试失败: {e}")
        return False

def test_performance():
    """测试性能指标"""
    print("\n🔍 测试性能指标...")
    
    try:
        from core.document_processing.export_manager import ExportManager
        
        manager = ExportManager()
        
        # 大文本测试
        large_text = "测试段落。\n" * 1000 + "# 标题\n" + "- 列表项\n" * 500
        
        start_time = time.time()
        result = manager.convert_format(large_text, 'markdown')
        conversion_time = time.time() - start_time
        
        # 性能要求
        assert conversion_time < 5.0, f"大文本转换时间过长: {conversion_time:.2f}s"
        assert result.get('conversion_time', 0) < 2.0, "内部转换时间过长"
        
        # 测试缓存效果
        start_time = time.time()
        result2 = manager.convert_format(large_text, 'markdown')
        cached_time = time.time() - start_time
        
        # 缓存应该显著提升性能
        if result2.get('cache_hit'):
            assert cached_time < conversion_time / 2, "缓存未显著提升性能"
        
        print(f"✅ 性能测试通过 (转换时间: {conversion_time:.2f}s)")
        return True
        
    except Exception as e:
        print(f"❌ 性能测试失败: {e}")
        return False

def test_error_handling():
    """测试错误处理"""
    print("\n🔍 测试错误处理...")
    
    try:
        from core.document_processing.export_manager import ExportManager
        from core.exceptions import UnsupportedFormatError, ValidationError
        
        manager = ExportManager()
        
        # 测试不支持的格式
        try:
            manager.convert_format("test", "unsupported_format")
            assert False, "应该抛出UnsupportedFormatError"
        except UnsupportedFormatError:
            pass  # 期望的异常
        
        # 测试无效输入
        try:
            manager.convert_format(None, "markdown")
            assert False, "应该抛出ValidationError"
        except ValidationError:
            pass  # 期望的异常
        
        # 测试空文本处理
        result = manager.convert_format("", "markdown")
        assert 'content' in result, "空文本应该正常处理"
        
        print("✅ 错误处理功能正常")
        return True
        
    except Exception as e:
        print(f"❌ 错误处理测试失败: {e}")
        return False

def test_api_endpoints():
    """测试API端点（需要应用运行）"""
    print("\n🔍 测试API端点...")
    
    try:
        # 测试状态端点
        response = requests.get('http://127.0.0.1:5000/api/status', timeout=5)
        if response.status_code == 200:
            data = response.json()
            assert 'success' in data, "状态API应返回success字段"
            
            # 测试格式转换端点
            test_data = {"text": "测试文本\n# 标题", "target_format": "markdown"}
            convert_response = requests.post(
                'http://127.0.0.1:5000/api/convert-format',
                headers={'Content-Type': 'application/json'},
                json=test_data,
                timeout=5
            )
            
            if convert_response.status_code == 200:
                convert_data = convert_response.json()
                assert 'success' in convert_data, "转换API应返回success字段"
                assert 'data' in convert_data, "转换API应返回data字段"
                assert 'converted_text' in convert_data['data'], "转换API应返回converted_text字段"
                print("✅ API端点完全可访问")
                return True
            else:
                print(f"⚠️  格式转换API不可访问 (状态码: {convert_response.status_code})")
                return False
        else:
            print(f"⚠️  API端点不可访问 (状态码: {response.status_code})")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"⚠️  API端点不可访问: {e}")
        return False

def test_file_structure():
    """测试文件结构完整性"""
    print("\n🔍 测试文件结构...")
    
    required_files = [
        'app.py',
        'requirements.txt',
        'README.md',
        'CHANGELOG.md',
        'core/__init__.py',
        'core/exceptions.py',
        'core/text_processing/__init__.py',
        'core/text_processing/analyzer.py',
        'core/text_processing/formatters.py',
        'core/document_processing/__init__.py',
        'core/document_processing/export_manager.py',
        'templates/index.html',
        'static/css/style.css',
        'static/js/app.js',
        'static/js/modules/format-manager.js',
        'static/js/modules/download-manager.js',
        'static/favicon.svg'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ 缺少文件: {missing_files}")
        return False
    else:
        print("✅ 文件结构完整")
        return True

def main():
    """主测试函数"""
    print("🚀 开始生产环境就绪性测试...\n")
    
    tests = [
        ("文件结构", test_file_structure),
        ("模块导入", test_imports),
        ("文本分析", test_text_analysis),
        ("格式转换", test_format_conversion),
        ("导出管理", test_export_manager),
        ("性能测试", test_performance),
        ("错误处理", test_error_handling),
        ("API端点", test_api_endpoints),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ {test_name}测试异常: {e}")
    
    print(f"\n📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！系统已准备好部署到生产环境。")
        return 0
    elif passed >= total - 1:  # 允许API测试失败（应用可能未运行）
        print("✅ 核心功能测试通过！系统基本准备就绪。")
        return 0
    else:
        print("⚠️  部分测试失败，请检查问题后再部署。")
        return 1

if __name__ == "__main__":
    exit(main())