import json
import re
from typing import Dict, Any, Optional

# 预编译正则表达式以提高性能
WHITESPACE_PATTERN = re.compile(r'[\n\t\r]')
MULTIPLE_SPACES_PATTERN = re.compile(r'\s+')
TRAILING_COMMA_BRACE = re.compile(r',\s*}')
TRAILING_COMMA_BRACKET = re.compile(r',\s*]')
UNQUOTED_KEYS = re.compile(r'(\w+):')

def json_str_parser_fast(json_str: str) -> Optional[Dict[str, Any]]:
    """快速JSON解析器 - 优化性能版本"""
    if not json_str:
        return None
    
    try:
        # 快速路径：先尝试去除首尾空白
        stripped = json_str.strip()
        if stripped:
            return json.loads(stripped)
    except (json.JSONDecodeError, ValueError, TypeError):
        pass
    
    return None

def repair_json_fast(json_str: str) -> str:
    """快速JSON修复 - 优化性能版本"""
    if not json_str:
        return json_str
    
    # 使用预编译的正则表达式
    repaired = json_str.strip()
    
    # 批量修复常见问题
    repaired = TRAILING_COMMA_BRACE.sub('}', repaired)
    repaired = TRAILING_COMMA_BRACKET.sub(']', repaired)
    repaired = UNQUOTED_KEYS.sub(r'"\1":', repaired)
    repaired = repaired.replace("'", '"')
    
    # 确保格式正确
    if repaired and not (repaired.startswith(('{', '[')) and repaired.endswith(('}', ']'))):
        if not repaired.startswith(('{', '[')):
            repaired = '{' + repaired
        if not repaired.endswith(('}', ']')):
            repaired = repaired + '}'
    
    return repaired

def json_str_parser_all_optimized(json_str: str) -> Dict[str, Any]:
    """
    优化版本的JSON字符串解析器 - 专注于性能
    
    Args:
        json_str: 要解析的JSON字符串
        
    Returns:
        解析成功返回字典，失败返回空字典
    """
    # 快速类型检查
    if not isinstance(json_str, str) or not json_str:
        return {}
    
    # 策略1: 直接解析原始字符串
    result = json_str_parser_fast(json_str)
    if result is not None:
        return result
    
    # 策略2: 移除空白字符后解析
    cleaned_str = WHITESPACE_PATTERN.sub('', json_str)
    if cleaned_str != json_str:  # 只有在真的有变化时才尝试
        result = json_str_parser_fast(cleaned_str)
        if result is not None:
            return result
    
    # 策略3: 修复原始字符串
    try:
        repaired_str = repair_json_fast(json_str)
        result = json_str_parser_fast(repaired_str)
        if result is not None:
            return result
    except Exception:
        pass
    
    # 策略4: 修复清理后的字符串
    try:
        repaired_cleaned_str = repair_json_fast(cleaned_str)
        result = json_str_parser_fast(repaired_cleaned_str)
        if result is not None:
            return result
    except Exception:
        pass
    
    # 策略5: 深度清理（压缩空白）
    try:
        deep_cleaned = MULTIPLE_SPACES_PATTERN.sub(' ', json_str).strip()
        if deep_cleaned != json_str:
            result = json_str_parser_fast(deep_cleaned)
            if result is not None:
                return result
            
            # 修复深度清理后的字符串
            repaired_deep = repair_json_fast(deep_cleaned)
            result = json_str_parser_fast(repaired_deep)
            if result is not None:
                return result
    except Exception:
        pass
    
    return {}

# 原始函数的简化重构版本
def json_str_parser_all_refactored(json_str: str) -> Dict[str, Any]:
    """
    重构原始函数 - 保持原有逻辑但优化代码结构
    """
    if not isinstance(json_str, str):
        return {}

    # 定义解析步骤
    steps = [
        # (处理函数, 描述)
        (lambda x: x, "原始字符串"),
        (lambda x: WHITESPACE_PATTERN.sub('', x), "移除换行符和制表符"),
        (lambda x: repair_json_fast(x), "修复原始字符串"),
        (lambda x: repair_json_fast(WHITESPACE_PATTERN.sub('', x)), "修复清理后的字符串")
    ]
    
    for processor, _ in steps:
        try:
            processed_str = processor(json_str)
            result = json_str_parser_fast(processed_str)
            if result is not None:
                return result
        except Exception:
            continue
    
    return {}

# 使用缓存的版本（适用于重复解析相同字符串的场景）
_parse_cache = {}
_cache_size_limit = 1000

def json_str_parser_all_cached(json_str: str, use_cache: bool = True) -> Dict[str, Any]:
    """
    带缓存的JSON解析器 - 适用于重复解析场景
    """
    if not isinstance(json_str, str):
        return {}
    
    # 使用缓存
    if use_cache and json_str in _parse_cache:
        return _parse_cache[json_str].copy()  # 返回副本避免修改缓存
    
    result = json_str_parser_all_optimized(json_str)
    
    # 更新缓存
    if use_cache and len(_parse_cache) < _cache_size_limit:
        _parse_cache[json_str] = result.copy()
    
    return result

def clear_cache():
    """清空解析缓存"""
    global _parse_cache
    _parse_cache.clear()

# 使用示例和性能测试
if __name__ == "__main__":
    import timeit
    
    # 测试用例
    test_cases = [
        '{"name": "test", "age": 25}',  # 正常JSON
        "{'name': 'test', 'age': 25}",  # 单引号
        '{"name": "test", "age": 25,}',  # 多余逗号
        '{\n  "name": "test",\n  "age": 25\n}',  # 包含换行符
        'name: "test", age: 25',  # 缺少引号和大括号
        '{"name": "test"',  # 不完整的JSON
    ]
    
    print("=== 功能测试 ===")
    for i, test_case in enumerate(test_cases, 1):
        print(f"测试用例 {i}: {repr(test_case)}")
        
        # 测试所有版本
        result_optimized = json_str_parser_all_optimized(test_case)
        result_refactored = json_str_parser_all_refactored(test_case)
        result_cached = json_str_parser_all_cached(test_case)
        
        print(f"  优化版本: {result_optimized}")
        print(f"  重构版本: {result_refactored}")
        print(f"  缓存版本: {result_cached}")
        print(f"  结果一致: {result_optimized == result_refactored == result_cached}")
        print()
    
    # 性能测试
    print("=== 性能测试 ===")
    test_json = '{"name": "test", "data": [1, 2, 3], "nested": {"key": "value"}}'
    malformed_json = "{'name': 'test', 'data': [1, 2, 3,], 'nested': {'key': 'value',}}"
    
    # 原始版本模拟
    def original_version(json_str):
        if not isinstance(json_str, str):
            return {}
        
        result = json_str_parser_fast(json_str)
        if result: return result
        
        cleaned_str = WHITESPACE_PATTERN.sub('', json_str)
        result = json_str_parser_fast(cleaned_str)
        if result: return result
        
        repaired_str = repair_json_fast(json_str)
        result = json_str_parser_fast(repaired_str)
        if result: return result
        
        repaired_cleaned_str = repair_json_fast(cleaned_str)
        return json_str_parser_fast(repaired_cleaned_str) or {}
    
    # 性能对比
    test_count = 10000
    
    print(f"测试次数: {test_count}")
    print(f"测试数据: {repr(test_json)}")
    
    time_original = timeit.timeit(lambda: original_version(test_json), number=test_count)
    time_optimized = timeit.timeit(lambda: json_str_parser_all_optimized(test_json), number=test_count)
    time_refactored = timeit.timeit(lambda: json_str_parser_all_refactored(test_json), number=test_count)
    time_cached = timeit.timeit(lambda: json_str_parser_all_cached(test_json), number=test_count)
    
    print(f"原始版本耗时: {time_original:.4f}秒")
    print(f"优化版本耗时: {time_optimized:.4f}秒")
    print(f"重构版本耗时: {time_refactored:.4f}秒")
    print(f"缓存版本耗时: {time_cached:.4f}秒")
    
    print(f"\n相对于原始版本的性能提升:")
    print(f"优化版本: {((time_original - time_optimized) / time_original * 100):.2f}%")
    print(f"重构版本: {((time_original - time_refactored) / time_original * 100):.2f}%")
    print(f"缓存版本: {((time_original - time_cached) / time_original * 100):.2f}%")
    
    # 测试错误格式的JSON性能
    print(f"\n=== 错误格式JSON性能测试 ===")
    print(f"测试数据: {repr(malformed_json)}")
    
    time_original_bad = timeit.timeit(lambda: original_version(malformed_json), number=test_count)
    time_optimized_bad = timeit.timeit(lambda: json_str_parser_all_optimized(malformed_json), number=test_count)
    
    print(f"原始版本耗时: {time_original_bad:.4f}秒")
    print(f"优化版本耗时: {time_optimized_bad:.4f}秒")
    print(f"性能提升: {((time_original_bad - time_optimized_bad) / time_original_bad * 100):.2f}%")
    
    # 缓存效果测试
    print(f"\n=== 缓存效果测试 ===")
    clear_cache()
    time_first = timeit.timeit(lambda: json_str_parser_all_cached(test_json), number=1)
    time_cached_repeat = timeit.timeit(lambda: json_str_parser_all_cached(test_json), number=test_count)
    
    print(f"首次解析耗时: {time_first:.6f}秒")
    print(f"缓存重复解析 {test_count} 次耗时: {time_cached_repeat:.4f}秒")
    print(f"平均每次缓存解析耗时: {time_cached_repeat/test_count:.6f}秒")
    print(f"缓存加速比: {time_first/(time_cached_repeat/test_count):.2f}x")