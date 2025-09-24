#!/usr/bin/env python3
"""
API格式转换功能测试
"""
import requests
import json

def test_format_conversion_api():
    """测试格式转换API"""
    print("🔍 测试格式转换API...")
    
    test_data = {
        "text": """第一章 项目介绍
这是一个基于PaddleOCR的项目。

主要功能包括：
- OCR文字识别
- 格式转换
- 文件下载

1. 安装依赖
2. 启动应用
3. 使用功能""",
        "target_format": "markdown"
    }
    
    try:
        response = requests.post(
            'http://127.0.0.1:5000/api/convert-format',
            headers={'Content-Type': 'application/json'},
            json=test_data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 格式转换API测试成功")
            print(f"   转换时间: {result.get('conversion_time', 0):.3f}秒")
            print(f"   缓存命中: {result.get('cache_hit', False)}")
            if 'structure_info' in result:
                info = result['structure_info']
                print(f"   结构分析: {info.get('headings_count', 0)}个标题, {info.get('lists_count', 0)}个列表")
            return True
        else:
            print(f"❌ API返回错误状态码: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ API测试失败: {e}")
        return False

def test_download_api():
    """测试下载API"""
    print("\n🔍 测试下载API...")
    
    test_data = {
        "content": "# 测试文档\n\n这是测试内容。",
        "format": "markdown",
        "filename": "test_document"
    }
    
    try:
        response = requests.post(
            'http://127.0.0.1:5000/api/download-result',
            headers={'Content-Type': 'application/json'},
            json=test_data,
            timeout=10
        )
        
        if response.status_code == 200:
            # 检查是否返回文件
            if 'attachment' in response.headers.get('Content-Disposition', ''):
                print("✅ 下载API测试成功")
                print(f"   文件大小: {len(response.content)} 字节")
                return True
            else:
                result = response.json()
                if 'filepath' in result:
                    print("✅ 下载API测试成功")
                    print(f"   文件路径: {result['filepath']}")
                    return True
        
        print(f"❌ 下载API返回异常: {response.status_code}")
        return False
        
    except Exception as e:
        print(f"❌ 下载API测试失败: {e}")
        return False

if __name__ == "__main__":
    print("🚀 开始API功能测试...\n")
    
    tests_passed = 0
    total_tests = 2
    
    if test_format_conversion_api():
        tests_passed += 1
    
    if test_download_api():
        tests_passed += 1
    
    print(f"\n📊 API测试结果: {tests_passed}/{total_tests} 通过")
    
    if tests_passed == total_tests:
        print("🎉 所有API测试通过！")
    else:
        print("⚠️  部分API测试失败")