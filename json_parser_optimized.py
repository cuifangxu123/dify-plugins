import json
import re
import logging
from typing import Dict, Any, Optional, Callable, List, Union
from functools import wraps
import time

# 设置日志
logger = logging.getLogger(__name__)

def timer_decorator(func: Callable) -> Callable:
    """装饰器：记录函数执行时间"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        logger.debug(f"{func.__name__} 执行时间: {end_time - start_time:.4f}秒")
        return result
    return wrapper

def json_str_parser(json_str: str) -> Optional[Dict[str, Any]]:
    """
    基础的JSON字符串解析器
    
    Args:
        json_str: 要解析的JSON字符串
        
    Returns:
        解析成功返回字典，失败返回None
    """
    try:
        if not json_str or not json_str.strip():
            return None
        return json.loads(json_str.strip())
    except (json.JSONDecodeError, ValueError, TypeError) as e:
        logger.debug(f"JSON解析失败: {e}")
        return None

def repair_json(json_str: str) -> str:
    """
    JSON修复函数（简化版实现）
    
    在实际使用中，你可能需要使用专门的库如 json-repair
    这里提供一个基础的修复实现
    
    Args:
        json_str: 需要修复的JSON字符串
        
    Returns:
        修复后的JSON字符串
    """
    if not json_str:
        return json_str
    
    # 基础修复逻辑
    repaired = json_str.strip()
    
    # 修复常见问题
    # 1. 移除多余的逗号
    repaired = re.sub(r',\s*}', '}', repaired)
    repaired = re.sub(r',\s*]', ']', repaired)
    
    # 2. 添加缺失的引号
    repaired = re.sub(r'(\w+):', r'"\1":', repaired)
    
    # 3. 修复单引号为双引号
    repaired = repaired.replace("'", '"')
    
    # 4. 确保以{}或[]包围
    if not (repaired.startswith(('{', '[')) and repaired.endswith(('}', ']'))):
        if not repaired.startswith(('{', '[')):
            repaired = '{' + repaired
        if not repaired.endswith(('}', ']')):
            repaired = repaired + '}'
    
    return repaired

class JSONParsingStrategy:
    """JSON解析策略类"""
    
    def __init__(self, name: str, processor: Callable[[str], str], description: str):
        self.name = name
        self.processor = processor
        self.description = description
    
    def apply(self, json_str: str) -> str:
        """应用策略处理字符串"""
        try:
            return self.processor(json_str)
        except Exception as e:
            logger.warning(f"策略 '{self.name}' 处理失败: {e}")
            return json_str

class JSONParserOptimized:
    """优化的JSON解析器类"""
    
    def __init__(self, enable_logging: bool = False):
        """
        初始化解析器
        
        Args:
            enable_logging: 是否启用详细日志记录
        """
        self.enable_logging = enable_logging
        if enable_logging:
            logging.basicConfig(level=logging.DEBUG)
        
        # 定义解析策略
        self._strategies = [
            JSONParsingStrategy(
                "原始解析", 
                lambda x: x, 
                "直接解析原始字符串"
            ),
            JSONParsingStrategy(
                "清理空白", 
                lambda x: re.sub(r'[\n\t\r]', '', x), 
                "移除换行符、制表符和回车符"
            ),
            JSONParsingStrategy(
                "修复原始", 
                repair_json, 
                "使用修复函数处理原始字符串"
            ),
            JSONParsingStrategy(
                "清理并修复", 
                lambda x: repair_json(re.sub(r'[\n\t\r]', '', x)), 
                "先清理空白再修复"
            ),
            JSONParsingStrategy(
                "深度清理", 
                lambda x: re.sub(r'\s+', ' ', x).strip(), 
                "压缩所有连续空白为单个空格"
            ),
            JSONParsingStrategy(
                "深度修复", 
                lambda x: repair_json(re.sub(r'\s+', ' ', x).strip()), 
                "深度清理后再修复"
            )
        ]
    
    @timer_decorator
    def parse(self, json_str: Union[str, Any]) -> Dict[str, Any]:
        """
        优化的JSON解析函数
        
        Args:
            json_str: 要解析的JSON字符串
            
        Returns:
            解析结果字典，失败时返回空字典
        """
        # 输入验证
        if not isinstance(json_str, str):
            logger.warning(f"输入类型错误，期望str，得到{type(json_str)}")
            return {}
        
        if not json_str or not json_str.strip():
            logger.warning("输入为空字符串")
            return {}
        
        # 缓存原始字符串以避免重复处理
        original_str = json_str
        
        # 尝试各种策略
        for strategy in self._strategies:
            if self.enable_logging:
                logger.debug(f"尝试策略: {strategy.name} - {strategy.description}")
            
            try:
                # 应用策略处理字符串
                processed_str = strategy.apply(original_str)
                
                # 尝试解析
                result = json_str_parser(processed_str)
                
                if result is not None:
                    if self.enable_logging:
                        logger.info(f"解析成功，使用策略: {strategy.name}")
                    return result
                    
            except Exception as e:
                if self.enable_logging:
                    logger.debug(f"策略 '{strategy.name}' 解析失败: {e}")
                continue
        
        # 所有策略都失败了
        logger.warning("所有解析策略都失败了")
        return {}
    
    def add_custom_strategy(self, name: str, processor: Callable[[str], str], description: str = "") -> None:
        """
        添加自定义解析策略
        
        Args:
            name: 策略名称
            processor: 处理函数
            description: 策略描述
        """
        strategy = JSONParsingStrategy(name, processor, description)
        self._strategies.append(strategy)
        logger.info(f"添加自定义策略: {name}")
    
    def get_strategies(self) -> List[str]:
        """获取所有可用策略的名称列表"""
        return [strategy.name for strategy in self._strategies]

# 创建默认解析器实例
default_parser = JSONParserOptimized()

def json_str_parser_all(json_str: str, enable_logging: bool = False) -> Dict[str, Any]:
    """
    优化版本的JSON字符串解析器
    
    通过一系列的清洗和修复步骤，尽最大努力将一个可能格式不正确的JSON字符串解析为字典。
    
    Args:
        json_str: 要解析的JSON字符串
        enable_logging: 是否启用详细的日志记录
        
    Returns:
        解析成功返回字典，失败返回空字典
        
    Examples:
        >>> json_str_parser_all('{"name": "test"}')
        {'name': 'test'}
        
        >>> json_str_parser_all("{'name': 'test'}")  # 单引号修复
        {'name': 'test'}
        
        >>> json_str_parser_all('{"name": "test",}')  # 多余逗号修复
        {'name': 'test'}
    """
    parser = JSONParserOptimized(enable_logging=enable_logging)
    return parser.parse(json_str)

def json_str_parser_all_advanced(
    json_str: str, 
    custom_strategies: Optional[List[Callable[[str], str]]] = None,
    enable_logging: bool = False
) -> Dict[str, Any]:
    """
    高级版本的JSON解析器，支持自定义策略
    
    Args:
        json_str: 要解析的JSON字符串
        custom_strategies: 自定义策略函数列表
        enable_logging: 是否启用日志记录
        
    Returns:
        解析结果字典
    """
    parser = JSONParserOptimized(enable_logging=enable_logging)
    
    # 添加自定义策略
    if custom_strategies:
        for i, strategy_func in enumerate(custom_strategies):
            parser.add_custom_strategy(
                f"自定义策略{i+1}", 
                strategy_func, 
                f"用户定义的第{i+1}个自定义策略"
            )
    
    return parser.parse(json_str)

# 使用示例和测试
if __name__ == "__main__":
    # 测试用例
    test_cases = [
        '{"name": "test", "age": 25}',  # 正常JSON
        "{'name': 'test', 'age': 25}",  # 单引号
        '{"name": "test", "age": 25,}',  # 多余逗号
        '{\n  "name": "test",\n  "age": 25\n}',  # 包含换行符
        'name: "test", age: 25',  # 缺少引号和大括号
        '{"name": "test"',  # 不完整的JSON
        '',  # 空字符串
        None,  # None值
        123,  # 非字符串类型
    ]
    
    # 启用日志进行测试
    print("=== JSON解析器测试 ===")
    for i, test_case in enumerate(test_cases):
        print(f"\n测试用例 {i+1}: {repr(test_case)}")
        try:
            result = json_str_parser_all(test_case, enable_logging=True)
            print(f"解析结果: {result}")
        except Exception as e:
            print(f"解析异常: {e}")
    
    # 性能测试
    print("\n=== 性能测试 ===")
    test_json = '{"name": "test", "data": [1, 2, 3], "nested": {"key": "value"}}'
    
    import timeit
    
    # 测试原始版本（模拟）
    def original_version(json_str):
        # 这是原始函数的简化模拟
        result = json_str_parser(json_str)
        if result: return result
        
        cleaned_str = re.sub(r'[\n\t]', '', json_str)
        result = json_str_parser(cleaned_str)
        if result: return result
        
        repaired_str = repair_json(json_str)
        result = json_str_parser(repaired_str)
        if result: return result
        
        repaired_cleaned_str = repair_json(cleaned_str)
        return json_str_parser(repaired_cleaned_str) or {}
    
    # 性能对比
    time_original = timeit.timeit(lambda: original_version(test_json), number=1000)
    time_optimized = timeit.timeit(lambda: json_str_parser_all(test_json), number=1000)
    
    print(f"原始版本执行1000次耗时: {time_original:.4f}秒")
    print(f"优化版本执行1000次耗时: {time_optimized:.4f}秒")
    print(f"性能提升: {((time_original - time_optimized) / time_original * 100):.2f}%")