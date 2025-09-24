"""自定义异常类定义"""


class FormatConversionError(Exception):
    """格式转换错误基类"""
    
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or 'FORMAT_CONVERSION_ERROR'
        self.details = details or {}
    
    def to_dict(self) -> dict:
        """转换为字典格式，便于API响应"""
        return {
            'message': self.message,
            'code': self.error_code,
            'details': self.details,
            'type': self.__class__.__name__
        }


class UnsupportedFormatError(FormatConversionError):
    """不支持的格式错误"""
    
    def __init__(self, format_name: str, supported_formats: list = None):
        self.format_name = format_name
        self.supported_formats = supported_formats or []
        
        message = f"Unsupported format: {format_name}"
        if self.supported_formats:
            message += f". Supported formats: {', '.join(self.supported_formats)}"
        
        super().__init__(
            message=message,
            error_code='UNSUPPORTED_FORMAT',
            details={
                'requested_format': format_name,
                'supported_formats': self.supported_formats
            }
        )


class TextAnalysisError(FormatConversionError):
    """文本分析错误"""
    
    def __init__(self, message: str, analysis_stage: str = None, original_error: Exception = None):
        self.analysis_stage = analysis_stage
        self.original_error = original_error
        
        details = {}
        if analysis_stage:
            details['analysis_stage'] = analysis_stage
        if original_error:
            details['original_error'] = str(original_error)
            details['original_error_type'] = type(original_error).__name__
        
        super().__init__(
            message=message,
            error_code='TEXT_ANALYSIS_ERROR',
            details=details
        )


class ValidationError(FormatConversionError):
    """输入验证错误"""
    
    def __init__(self, message: str, field_name: str = None, field_value=None):
        self.field_name = field_name
        self.field_value = field_value
        
        details = {}
        if field_name:
            details['field_name'] = field_name
        if field_value is not None:
            details['field_value'] = str(field_value)
        
        super().__init__(
            message=message,
            error_code='VALIDATION_ERROR',
            details=details
        )


class FileOperationError(FormatConversionError):
    """文件操作错误"""
    
    def __init__(self, message: str, operation: str = None, filepath: str = None, original_error: Exception = None):
        self.operation = operation
        self.filepath = filepath
        self.original_error = original_error
        
        details = {}
        if operation:
            details['operation'] = operation
        if filepath:
            details['filepath'] = filepath
        if original_error:
            details['original_error'] = str(original_error)
            details['original_error_type'] = type(original_error).__name__
        
        super().__init__(
            message=message,
            error_code='FILE_OPERATION_ERROR',
            details=details
        )


class APIError(Exception):
    """API相关错误"""
    
    def __init__(self, message: str, status_code: int = 500, error_code: str = None, details: dict = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or 'API_ERROR'
        self.details = details or {}
    
    def to_dict(self) -> dict:
        """转换为字典格式，便于API响应"""
        return {
            'message': self.message,
            'code': self.error_code,
            'details': self.details,
            'type': self.__class__.__name__
        }


class RequestValidationError(APIError):
    """请求验证错误"""
    
    def __init__(self, message: str, validation_errors: list = None):
        self.validation_errors = validation_errors or []
        
        super().__init__(
            message=message,
            status_code=400,
            error_code='REQUEST_VALIDATION_ERROR',
            details={'validation_errors': self.validation_errors}
        )


class ResourceNotFoundError(APIError):
    """资源未找到错误"""
    
    def __init__(self, resource_type: str, resource_id: str = None):
        self.resource_type = resource_type
        self.resource_id = resource_id
        
        message = f"{resource_type} not found"
        if resource_id:
            message += f": {resource_id}"
        
        super().__init__(
            message=message,
            status_code=404,
            error_code='RESOURCE_NOT_FOUND',
            details={
                'resource_type': resource_type,
                'resource_id': resource_id
            }
        )


class ServiceUnavailableError(APIError):
    """服务不可用错误"""
    
    def __init__(self, service_name: str, reason: str = None):
        self.service_name = service_name
        self.reason = reason
        
        message = f"{service_name} service is unavailable"
        if reason:
            message += f": {reason}"
        
        super().__init__(
            message=message,
            status_code=503,
            error_code='SERVICE_UNAVAILABLE',
            details={
                'service_name': service_name,
                'reason': reason
            }
        )


class RateLimitError(APIError):
    """请求频率限制错误"""
    
    def __init__(self, limit: int, window: str, retry_after: int = None):
        self.limit = limit
        self.window = window
        self.retry_after = retry_after
        
        message = f"Rate limit exceeded: {limit} requests per {window}"
        if retry_after:
            message += f". Retry after {retry_after} seconds"
        
        super().__init__(
            message=message,
            status_code=429,
            error_code='RATE_LIMIT_EXCEEDED',
            details={
                'limit': limit,
                'window': window,
                'retry_after': retry_after
            }
        )