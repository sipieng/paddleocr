"""文本结构分析器模块"""
from typing import List, Dict
from dataclasses import dataclass


@dataclass
class Heading:
    """标题数据模型"""
    text: str
    level: int  # 1-6
    line_number: int
    confidence: float


@dataclass
class ListItem:
    """列表项数据模型"""
    text: str
    type: str  # 'ordered' or 'unordered'
    level: int  # 嵌套层级
    line_number: int


@dataclass
class Table:
    """表格数据模型"""
    headers: List[str]
    rows: List[List[str]]
    line_start: int
    line_end: int


@dataclass
class TextStructure:
    """文本结构数据模型"""
    headings: List[Heading]
    paragraphs: List[str]
    lists: List[ListItem]
    tables: List[Table]
    raw_lines: List[str]


class TextAnalyzer:
    """文本结构分析器"""
    
    def __init__(self):
        """初始化分析器"""
        self.min_heading_length = 2
        self.max_heading_length = 100
        self.heading_indicators = ['第', '章', '节', '部分', '概述', '总结', '介绍', '说明']
        
        # 性能优化：预编译正则表达式
        import re
        self._compiled_patterns = {
            'unordered_list': [
                re.compile(r'^[-•*]\s+(.+)'),
                re.compile(r'^[·]\s+(.+)'),
                re.compile(r'^[○]\s+(.+)'),
            ],
            'ordered_list': [
                re.compile(r'^(\d+)[\.\)]\s+(.+)'),
                re.compile(r'^([一二三四五六七八九十]+)[\.\)]\s+(.+)'),
                re.compile(r'^([ABCDEFGHIJKLMNOPQRSTUVWXYZ])[\.\)]\s+(.+)'),
                re.compile(r'^([abcdefghijklmnopqrstuvwxyz])[\.\)]\s+(.+)'),
            ],
            'heading_patterns': {
                'chapter': re.compile(r'^第[一二三四五六七八九十]+章'),
                'section': re.compile(r'^第[一二三四五六七八九十]+节'),
                'numbered_section': re.compile(r'^\d+\.\d+'),
                'numbered_main': re.compile(r'^\d+\.'),
                'list_marker': re.compile(r'^[•\-\*]\s'),
                'numeric_start': re.compile(r'^\d+[\.\s]'),
                'chinese_number': re.compile(r'^[一二三四五六七八九十]+[\.\s]'),
                'chapter_section': re.compile(r'第[一二三四五六七八九十]+[章节]'),
                'title_markers': re.compile(r'[第章节部分]|^\d+[\.\s]|^[一二三四五六七八九十]+[\.\s]'),
                'whitespace_normalize': re.compile(r'\s+'),
                'escape_numeric_list': re.compile(r'^(\d+)\.'),
                'escape_list_markers': re.compile(r'^([-+*])\s'),
                'escape_links': re.compile(r'\[([^\]]*)\]\(([^)]*)\)'),
            }
        }
        
        # 性能优化：缓存机制
        self._analysis_cache = {}
        self._cache_max_size = 100
        
        # 性能监控
        self._performance_stats = {
            'total_analyses': 0,
            'cache_hits': 0,
            'average_analysis_time': 0.0,
            'large_text_count': 0
        }
    
    def analyze_structure(self, text_lines: List[str]) -> TextStructure:
        """分析文本结构，识别标题、段落、列表等"""
        import time
        import hashlib
        
        start_time = time.time()
        self._performance_stats['total_analyses'] += 1
        
        if not text_lines:
            return TextStructure(
                headings=[],
                paragraphs=[],
                lists=[],
                tables=[],
                raw_lines=[]
            )
        
        # 性能优化：检查缓存
        text_hash = hashlib.md5('\n'.join(text_lines).encode()).hexdigest()
        if text_hash in self._analysis_cache:
            self._performance_stats['cache_hits'] += 1
            return self._analysis_cache[text_hash]
        
        # 性能监控：检测大文本
        total_chars = sum(len(line) for line in text_lines)
        if total_chars > 10000:  # 10KB threshold
            self._performance_stats['large_text_count'] += 1
        
        # 预处理文本行（优化版本）
        processed_lines = self._preprocess_lines_optimized(text_lines)
        
        # 检测各种结构元素（并行处理小批量）
        headings = self._convert_heading_dicts_to_objects(
            self.detect_headings_optimized(processed_lines)
        )
        lists = self._convert_list_dicts_to_objects(
            self.detect_lists_optimized(processed_lines)
        )
        
        # 提取段落（非标题、非列表的行）
        paragraphs = self._extract_paragraphs_optimized(processed_lines, headings, lists)
        
        result = TextStructure(
            headings=headings,
            paragraphs=paragraphs,
            lists=lists,
            tables=[],  # 表格检测将在后续版本实现
            raw_lines=text_lines
        )
        
        # 更新缓存
        self._update_cache(text_hash, result)
        
        # 更新性能统计
        analysis_time = time.time() - start_time
        self._update_performance_stats(analysis_time)
        
        return result
    
    def _preprocess_lines(self, lines: List[str]) -> List[str]:
        """预处理文本行"""
        processed = []
        for line in lines:
            # 去除首尾空白字符
            cleaned = line.strip()
            # 保留非空行
            if cleaned:
                processed.append(cleaned)
        return processed
    
    def _convert_heading_dicts_to_objects(self, heading_dicts: List[Dict]) -> List[Heading]:
        """将标题字典转换为Heading对象"""
        headings = []
        for h_dict in heading_dicts:
            heading = Heading(
                text=h_dict.get('text', ''),
                level=h_dict.get('level', 1),
                line_number=h_dict.get('line_number', 0),
                confidence=h_dict.get('confidence', 0.0)
            )
            headings.append(heading)
        return headings
    
    def _convert_list_dicts_to_objects(self, list_dicts: List[Dict]) -> List[ListItem]:
        """将列表字典转换为ListItem对象"""
        list_items = []
        for l_dict in list_dicts:
            list_item = ListItem(
                text=l_dict.get('text', ''),
                type=l_dict.get('type', 'unordered'),
                level=l_dict.get('level', 0),
                line_number=l_dict.get('line_number', 0)
            )
            list_items.append(list_item)
        return list_items
    
    def _extract_paragraphs(self, lines: List[str], headings: List[Heading], lists: List[ListItem]) -> List[str]:
        """提取段落文本（排除标题和列表项）"""
        # 获取已被识别为标题或列表的行号
        used_line_numbers = set()
        for heading in headings:
            used_line_numbers.add(heading.line_number)
        for list_item in lists:
            used_line_numbers.add(list_item.line_number)
        
        paragraphs = []
        current_paragraph = []
        
        for i, line in enumerate(lines):
            if i not in used_line_numbers:
                # 如果是普通文本行，添加到当前段落
                current_paragraph.append(line)
            else:
                # 如果遇到标题或列表，结束当前段落
                if current_paragraph:
                    paragraphs.append(' '.join(current_paragraph))
                    current_paragraph = []
        
        # 处理最后一个段落
        if current_paragraph:
            paragraphs.append(' '.join(current_paragraph))
        
        return paragraphs
    
    def detect_headings(self, lines: List[str]) -> List[Dict]:
        """检测标题行"""
        headings = []
        total_lines = len(lines)
        
        for i, line in enumerate(lines):
            if self._is_heading_candidate(line):
                # 计算标题层级和置信度
                level, confidence = self._determine_heading_level(line, i, lines)
                
                if confidence > 0.3:  # 置信度阈值
                    headings.append({
                        'text': line,
                        'level': level,
                        'line_number': i,
                        'confidence': confidence
                    })
        
        return headings
    
    def detect_lists(self, lines: List[str]) -> List[Dict]:
        """检测列表项"""
        list_items = []
        
        for i, line in enumerate(lines):
            list_info = self._analyze_list_item(line, i)
            if list_info:
                list_items.append(list_info)
        
        # 后处理：调整嵌套层级
        list_items = self._adjust_list_nesting(list_items)
        
        return list_items
    
    def _analyze_list_item(self, line: str, line_number: int) -> Dict:
        """分析单行是否为列表项"""
        import re
        
        if not line or not line.strip():
            return None
        
        original_line = line  # 保留原始行（包含缩进）
        line = line.strip()   # 去除首尾空格用于模式匹配
        
        # 检测无序列表
        unordered_patterns = [
            r'^[-•*]\s+(.+)',  # - item, • item, * item
            r'^[·]\s+(.+)',    # · item
            r'^[○]\s+(.+)',    # ○ item
        ]
        
        for pattern in unordered_patterns:
            match = re.match(pattern, line)
            if match:
                content = match.group(1).strip()
                level = self._calculate_list_indentation(original_line)
                return {
                    'text': content,
                    'type': 'unordered',
                    'level': level,
                    'line_number': line_number,
                    'marker': line[0],
                    'full_text': line
                }
        
        # 检测有序列表
        ordered_patterns = [
            r'^(\d+)[\.\)]\s+(.+)',           # 1. item, 1) item
            r'^([一二三四五六七八九十]+)[\.\)]\s+(.+)',  # 一. item
            r'^([ABCDEFGHIJKLMNOPQRSTUVWXYZ])[\.\)]\s+(.+)',  # A. item
            r'^([abcdefghijklmnopqrstuvwxyz])[\.\)]\s+(.+)',  # a. item
        ]
        
        for pattern in ordered_patterns:
            match = re.match(pattern, line)
            if match:
                marker = match.group(1)
                content = match.group(2).strip()
                level = self._calculate_list_indentation(original_line)
                return {
                    'text': content,
                    'type': 'ordered',
                    'level': level,
                    'line_number': line_number,
                    'marker': marker,
                    'full_text': line
                }
        
        return None
    
    def _calculate_list_indentation(self, line: str) -> int:
        """计算列表项的缩进层级"""
        # 计算前导空格数量
        leading_spaces = len(line) - len(line.lstrip())
        
        # 每4个空格或1个tab算一个层级
        if '\t' in line[:leading_spaces]:
            level = line[:leading_spaces].count('\t')
        else:
            # 每2个空格算一个层级（更适合中文文档）
            level = leading_spaces // 2
        
        return max(0, level)
    
    def _adjust_list_nesting(self, list_items: List[Dict]) -> List[Dict]:
        """调整列表嵌套层级"""
        if not list_items:
            return list_items
        
        # 标准化层级（确保从0开始）
        min_level = min(item['level'] for item in list_items)
        for item in list_items:
            item['level'] = item['level'] - min_level
        
        # 检测连续的列表项并调整层级
        for i in range(1, len(list_items)):
            current = list_items[i]
            previous = list_items[i-1]
            
            # 如果当前项的行号与前一项不连续，可能是新的列表组
            if current['line_number'] - previous['line_number'] > 2:
                # 重置层级计算
                continue
            
            # 基于内容长度和位置微调层级
            if len(current['text']) < len(previous['text']) * 0.5:
                # 较短的项可能是子项
                current['level'] = max(current['level'], previous['level'] + 1)
        
        return list_items
    
    def _is_heading_candidate(self, line: str) -> bool:
        """判断是否为标题候选行"""
        if not line or len(line.strip()) == 0:
            return False
        
        line = line.strip()
        
        # 长度检查
        if len(line) < self.min_heading_length or len(line) > self.max_heading_length:
            return False
        
        # 排除明显的列表项
        if line.startswith(('-', '•', '*')) or line.startswith('- '):
            return False
        
        # 排除过长的句子（通常是段落）
        if len(line) > 60 and line.endswith('。'):
            return False
        
        # 基本特征检查
        features = self._get_heading_features(line)
        
        # 综合判断
        score = 0
        
        # 强标题标识符（高权重）
        if features['starts_with_chinese_number'] or features['has_chapter_markers']:
            score += 0.6
        
        # 数字编号标题
        if features['starts_with_number'] and not features['is_list_item']:
            score += 0.4
        
        # 关键词特征
        if features['contains_keywords']:
            score += 0.3
        
        # 长度特征（较短的行更可能是标题）
        if len(line) <= 20:
            score += 0.3
        elif len(line) <= 40:
            score += 0.1
        
        # 结尾特征（标题通常不以句号结尾）
        if not features['ends_with_punctuation']:
            score += 0.2
        
        # 惩罚项：如果看起来像普通句子
        if len(line) > 40 and features['ends_with_punctuation']:
            score -= 0.3
        
        # 惩罚项：以冒号结尾的长句子通常不是标题
        if len(line) > 30 and (line.endswith('：') or line.endswith(':')):
            score -= 0.2
        
        return score >= 0.5
    
    def _get_heading_features(self, line: str) -> Dict:
        """获取标题特征"""
        import re
        
        # 中文数字映射
        chinese_numbers = ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十']
        
        features = {
            'contains_keywords': any(keyword in line for keyword in self.heading_indicators),
            'starts_with_number': bool(re.match(r'^\d+[\.\s]', line)),
            'starts_with_chinese_number': any(line.startswith(f'第{num}') for num in chinese_numbers),
            'has_chapter_markers': bool(re.search(r'第[一二三四五六七八九十]+[章节]', line)),
            'has_title_markers': bool(re.search(r'[第章节部分]|^\d+[\.\s]|^[一二三四五六七八九十]+[\.\s]', line)),
            'ends_with_punctuation': line.endswith(('。', '！', '？')),
            'has_colon': '：' in line or ':' in line,
            'is_all_caps': line.isupper() if line.isascii() else False,
            'word_count': len(line.split()),
            'is_list_item': line.startswith(('-', '•', '*', '- ')) or bool(re.match(r'^[•\-\*]\s', line))
        }
        
        return features
    
    def _determine_heading_level(self, line: str, line_number: int, all_lines: List[str]) -> tuple:
        """确定标题层级和置信度"""
        import re
        
        level = 1
        confidence = 0.5
        
        # 基于内容特征判断层级
        if re.match(r'^第[一二三四五六七八九十]+章', line):
            level = 1
            confidence = 0.9
        elif re.match(r'^第[一二三四五六七八九十]+节', line):
            level = 2
            confidence = 0.8
        elif re.match(r'^\d+\.\d+', line):  # 如 "1.1"
            level = 2
            confidence = 0.8
        elif re.match(r'^\d+\.', line):  # 如 "1."
            level = 1
            confidence = 0.8
        elif any(keyword in line for keyword in ['概述', '总结', '介绍']):
            level = 2
            confidence = 0.7
        elif any(keyword in line for keyword in ['部分', '章节']):
            level = 1
            confidence = 0.7
        
        # 基于位置调整置信度
        position_ratio = line_number / len(all_lines) if all_lines else 0
        if position_ratio < 0.1:  # 文档开头
            confidence += 0.1
        elif position_ratio > 0.9:  # 文档结尾
            confidence += 0.05
        
        # 基于长度调整置信度
        if len(line) <= 20:
            confidence += 0.1
        elif len(line) > 50:
            confidence -= 0.1
        
        # 确保置信度在合理范围内
        confidence = max(0.0, min(1.0, confidence))
        
        return level, confidence
    
    def _normalize_text(self, text: str) -> str:
        """标准化文本，去除多余空格和特殊字符"""
        import re
        # 去除多余空格
        text = re.sub(r'\s+', ' ', text.strip())
        return text
    
    def _is_empty_or_whitespace(self, line: str) -> bool:
        """检查行是否为空或只包含空白字符"""
        return not line or line.isspace()
    
    def _calculate_line_features(self, line: str, line_number: int, total_lines: int) -> Dict:
        """计算文本行的特征"""
        return {
            'length': len(line),
            'word_count': len(line.split()),
            'position_ratio': line_number / total_lines if total_lines > 0 else 0,
            'has_punctuation': any(char in line for char in '。！？：；'),
            'is_short': len(line) < 20,
            'is_numeric_start': line[0].isdigit() if line else False,
            'contains_keywords': any(keyword in line for keyword in self.heading_indicators)
        }
    
    # 性能优化方法
    def _preprocess_lines_optimized(self, lines: List[str]) -> List[str]:
        """优化版本的预处理文本行"""
        # 使用列表推导式提高性能
        return [line.strip() for line in lines if line.strip()]
    
    def detect_headings_optimized(self, lines: List[str]) -> List[Dict]:
        """优化版本的标题检测"""
        headings = []
        total_lines = len(lines)
        
        # 批量处理，减少函数调用开销
        for i, line in enumerate(lines):
            if self._is_heading_candidate_optimized(line):
                level, confidence = self._determine_heading_level_optimized(line, i, total_lines)
                
                if confidence > 0.3:
                    headings.append({
                        'text': line,
                        'level': level,
                        'line_number': i,
                        'confidence': confidence
                    })
        
        return headings
    
    def detect_lists_optimized(self, lines: List[str]) -> List[Dict]:
        """优化版本的列表检测"""
        list_items = []
        
        for i, line in enumerate(lines):
            list_info = self._analyze_list_item_optimized(line, i)
            if list_info:
                list_items.append(list_info)
        
        return self._adjust_list_nesting(list_items)
    
    def _is_heading_candidate_optimized(self, line: str) -> bool:
        """优化版本的标题候选判断"""
        if not line or len(line.strip()) == 0:
            return False
        
        line = line.strip()
        line_len = len(line)
        
        # 快速长度检查
        if line_len < self.min_heading_length or line_len > self.max_heading_length:
            return False
        
        # 使用预编译的正则表达式
        if self._compiled_patterns['heading_patterns']['list_marker'].match(line):
            return False
        
        # 快速特征检查
        score = 0
        
        # 使用预编译模式进行快速匹配
        patterns = self._compiled_patterns['heading_patterns']
        
        if patterns['chapter'].match(line) or patterns['section'].match(line):
            score += 0.6
        elif patterns['numbered_section'].match(line) or patterns['numbered_main'].match(line):
            score += 0.4
        
        # 关键词检查（优化为集合查找）
        if any(keyword in line for keyword in self.heading_indicators):
            score += 0.3
        
        # 长度特征
        if line_len <= 20:
            score += 0.3
        elif line_len <= 40:
            score += 0.1
        
        # 结尾特征
        if not line.endswith(('。', '！', '？')):
            score += 0.2
        
        return score >= 0.5
    
    def _determine_heading_level_optimized(self, line: str, line_number: int, total_lines: int) -> tuple:
        """优化版本的标题层级判断"""
        level = 1
        confidence = 0.5
        
        patterns = self._compiled_patterns['heading_patterns']
        
        # 使用预编译正则表达式进行快速匹配
        if patterns['chapter'].match(line):
            level, confidence = 1, 0.9
        elif patterns['section'].match(line):
            level, confidence = 2, 0.8
        elif patterns['numbered_section'].match(line):
            level, confidence = 2, 0.8
        elif patterns['numbered_main'].match(line):
            level, confidence = 1, 0.8
        elif any(keyword in line for keyword in ['概述', '总结', '介绍']):
            level, confidence = 2, 0.7
        elif any(keyword in line for keyword in ['部分', '章节']):
            level, confidence = 1, 0.7
        
        # 位置调整
        position_ratio = line_number / total_lines if total_lines else 0
        if position_ratio < 0.1:
            confidence += 0.1
        elif position_ratio > 0.9:
            confidence += 0.05
        
        # 长度调整
        line_len = len(line)
        if line_len <= 20:
            confidence += 0.1
        elif line_len > 50:
            confidence -= 0.1
        
        return level, max(0.0, min(1.0, confidence))
    
    def _analyze_list_item_optimized(self, line: str, line_number: int) -> Dict:
        """优化版本的列表项分析"""
        if not line or not line.strip():
            return None
        
        original_line = line
        line = line.strip()
        
        # 使用预编译的正则表达式
        for pattern in self._compiled_patterns['unordered_list']:
            match = pattern.match(line)
            if match:
                content = match.group(1).strip()
                level = self._calculate_list_indentation(original_line)
                return {
                    'text': content,
                    'type': 'unordered',
                    'level': level,
                    'line_number': line_number,
                    'marker': line[0],
                    'full_text': line
                }
        
        for pattern in self._compiled_patterns['ordered_list']:
            match = pattern.match(line)
            if match:
                marker = match.group(1)
                content = match.group(2).strip()
                level = self._calculate_list_indentation(original_line)
                return {
                    'text': content,
                    'type': 'ordered',
                    'level': level,
                    'line_number': line_number,
                    'marker': marker,
                    'full_text': line
                }
        
        return None
    
    def _extract_paragraphs_optimized(self, lines: List[str], headings: List, lists: List) -> List[str]:
        """优化版本的段落提取"""
        # 使用集合提高查找性能
        used_line_numbers = {heading.line_number for heading in headings}
        used_line_numbers.update(list_item.line_number for list_item in lists)
        
        paragraphs = []
        current_paragraph = []
        
        for i, line in enumerate(lines):
            if i not in used_line_numbers:
                current_paragraph.append(line)
            else:
                if current_paragraph:
                    paragraphs.append(' '.join(current_paragraph))
                    current_paragraph = []
        
        if current_paragraph:
            paragraphs.append(' '.join(current_paragraph))
        
        return paragraphs
    
    def _update_cache(self, text_hash: str, result: TextStructure):
        """更新分析结果缓存"""
        if len(self._analysis_cache) >= self._cache_max_size:
            # 简单的LRU：删除最旧的条目
            oldest_key = next(iter(self._analysis_cache))
            del self._analysis_cache[oldest_key]
        
        self._analysis_cache[text_hash] = result
    
    def _update_performance_stats(self, analysis_time: float):
        """更新性能统计"""
        total = self._performance_stats['total_analyses']
        current_avg = self._performance_stats['average_analysis_time']
        
        # 计算新的平均时间
        new_avg = ((current_avg * (total - 1)) + analysis_time) / total
        self._performance_stats['average_analysis_time'] = new_avg
    
    def get_performance_stats(self) -> Dict:
        """获取性能统计信息"""
        stats = self._performance_stats.copy()
        if stats['total_analyses'] > 0:
            stats['cache_hit_rate'] = stats['cache_hits'] / stats['total_analyses']
        else:
            stats['cache_hit_rate'] = 0.0
        return stats
    
    def clear_cache(self):
        """清空缓存"""
        self._analysis_cache.clear()
        
    def reset_performance_stats(self):
        """重置性能统计"""
        self._performance_stats = {
            'total_analyses': 0,
            'cache_hits': 0,
            'average_analysis_time': 0.0,
            'large_text_count': 0
        }