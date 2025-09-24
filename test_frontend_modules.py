#!/usr/bin/env python3
"""
前端模块完整性测试
"""
import os
import re

def test_frontend_files():
    """测试前端文件完整性"""
    print("🔍 测试前端文件完整性...")
    
    # 检查关键文件
    files_to_check = {
        'templates/index.html': [
            'format-manager.js',
            'download-manager.js', 
            'error-handler.js',
            'data-bs-toggle="tooltip"',
            'Ctrl+1',
            'Ctrl+2'
        ],
        'static/js/modules/format-manager.js': [
            'class FormatManager',
            'initKeyboardShortcuts',
            'showLoadingOverlay',
            'switchToFormat',
            'showShortcutFeedback'
        ],
        'static/css/style.css': [
            'format-selector',
            'loading-overlay',
            'shortcut-feedback',
            '@media (max-width: 768px)',
            '@keyframes fadeInOut'
        ]
    }
    
    all_passed = True
    
    for file_path, required_content in files_to_check.items():
        if not os.path.exists(file_path):
            print(f"❌ 文件不存在: {file_path}")
            all_passed = False
            continue
            
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        missing_content = []
        for required in required_content:
            if required not in content:
                missing_content.append(required)
        
        if missing_content:
            print(f"❌ {file_path} 缺少内容: {missing_content}")
            all_passed = False
        else:
            print(f"✅ {file_path} 内容完整")
    
    return all_passed

def test_javascript_syntax():
    """测试JavaScript语法完整性"""
    print("\n🔍 测试JavaScript语法...")
    
    js_files = [
        'static/js/app.js',
        'static/js/modules/format-manager.js'
    ]
    
    all_passed = True
    
    for js_file in js_files:
        if not os.path.exists(js_file):
            print(f"❌ JS文件不存在: {js_file}")
            all_passed = False
            continue
            
        with open(js_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 基本语法检查
        issues = []
        
        # 检查括号匹配
        open_braces = content.count('{')
        close_braces = content.count('}')
        if open_braces != close_braces:
            issues.append(f"大括号不匹配: {open_braces} vs {close_braces}")
        
        open_parens = content.count('(')
        close_parens = content.count(')')
        if open_parens != close_parens:
            issues.append(f"小括号不匹配: {open_parens} vs {close_parens}")
        
        # 检查基本函数定义
        if 'function' not in content and 'class' not in content and '=>' not in content:
            issues.append("未找到函数定义")
        
        if issues:
            print(f"❌ {js_file} 语法问题: {issues}")
            all_passed = False
        else:
            print(f"✅ {js_file} 语法正常")
    
    return all_passed

if __name__ == "__main__":
    print("🚀 开始前端模块测试...\n")
    
    tests_passed = 0
    total_tests = 2
    
    if test_frontend_files():
        tests_passed += 1
    
    if test_javascript_syntax():
        tests_passed += 1
    
    print(f"\n📊 前端测试结果: {tests_passed}/{total_tests} 通过")
    
    if tests_passed == total_tests:
        print("🎉 前端模块测试通过！")
    else:
        print("⚠️  前端模块存在问题")