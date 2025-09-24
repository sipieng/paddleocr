/**
 * 前端错误处理和显示组件
 */
class ErrorHandler {
    constructor() {
        this.errorContainer = null;
        this.initErrorContainer();
    }

    /**
     * 初始化错误显示容器
     */
    initErrorContainer() {
        // 查找现有的错误容器
        this.errorContainer = document.getElementById('error-container');
        
        // 如果不存在，创建一个
        if (!this.errorContainer) {
            this.errorContainer = document.createElement('div');
            this.errorContainer.id = 'error-container';
            this.errorContainer.className = 'error-container';
            
            // 插入到页面顶部
            const mainContent = document.querySelector('.container') || document.body;
            mainContent.insertBefore(this.errorContainer, mainContent.firstChild);
        }
    }

    /**
     * 显示错误信息
     * @param {string|Error|Object} error - 错误信息
     * @param {string} type - 错误类型 ('error', 'warning', 'info')
     * @param {number} duration - 显示持续时间（毫秒），0表示不自动消失
     */
    showError(error, type = 'error', duration = 5000) {
        const errorInfo = this.parseError(error);
        const alertElement = this.createAlertElement(errorInfo, type);
        
        // 添加到容器
        this.errorContainer.appendChild(alertElement);
        
        // 自动消失
        if (duration > 0) {
            setTimeout(() => {
                this.removeAlert(alertElement);
            }, duration);
        }
        
        // 记录到控制台
        console.error('Error displayed:', errorInfo);
        
        return alertElement;
    }

    /**
     * 显示成功信息
     * @param {string} message - 成功信息
     * @param {number} duration - 显示持续时间（毫秒）
     */
    showSuccess(message, duration = 3000) {
        return this.showError(message, 'success', duration);
    }

    /**
     * 显示警告信息
     * @param {string} message - 警告信息
     * @param {number} duration - 显示持续时间（毫秒）
     */
    showWarning(message, duration = 4000) {
        return this.showError(message, 'warning', duration);
    }

    /**
     * 显示信息提示
     * @param {string} message - 信息内容
     * @param {number} duration - 显示持续时间（毫秒）
     */
    showInfo(message, duration = 3000) {
        return this.showError(message, 'info', duration);
    }

    /**
     * 解析错误对象
     * @param {string|Error|Object} error - 错误信息
     * @returns {Object} 解析后的错误信息
     */
    parseError(error) {
        if (typeof error === 'string') {
            return {
                message: error,
                code: null,
                details: null,
                type: 'string'
            };
        }

        if (error instanceof Error) {
            return {
                message: error.message,
                code: error.code || null,
                details: error.details || null,
                type: error.constructor.name
            };
        }

        if (typeof error === 'object' && error !== null) {
            return {
                message: error.message || 'Unknown error',
                code: error.code || error.error_code || null,
                details: error.details || null,
                type: error.type || 'object'
            };
        }

        return {
            message: String(error),
            code: null,
            details: null,
            type: 'unknown'
        };
    }

    /**
     * 创建警告元素
     * @param {Object} errorInfo - 错误信息
     * @param {string} type - 警告类型
     * @returns {HTMLElement} 警告元素
     */
    createAlertElement(errorInfo, type) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${this.getBootstrapAlertType(type)} alert-dismissible fade show`;
        alertDiv.setAttribute('role', 'alert');

        // 构建消息内容
        let messageHtml = `<strong>${this.getTypeLabel(type)}:</strong> ${this.escapeHtml(errorInfo.message)}`;
        
        // 添加错误代码
        if (errorInfo.code) {
            messageHtml += ` <small class="text-muted">(${errorInfo.code})</small>`;
        }

        // 添加详细信息（如果有且不是生产环境）
        if (errorInfo.details && this.shouldShowDetails()) {
            messageHtml += this.formatDetails(errorInfo.details);
        }

        alertDiv.innerHTML = `
            ${messageHtml}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;

        // 添加关闭事件监听器
        const closeButton = alertDiv.querySelector('.btn-close');
        closeButton.addEventListener('click', () => {
            this.removeAlert(alertDiv);
        });

        return alertDiv;
    }

    /**
     * 格式化详细信息
     * @param {Object} details - 详细信息
     * @returns {string} 格式化后的HTML
     */
    formatDetails(details) {
        if (!details || typeof details !== 'object') {
            return '';
        }

        let detailsHtml = '<div class="mt-2"><small class="text-muted">Details:</small><ul class="small text-muted mb-0">';
        
        for (const [key, value] of Object.entries(details)) {
            if (value !== null && value !== undefined) {
                detailsHtml += `<li><strong>${this.escapeHtml(key)}:</strong> ${this.escapeHtml(String(value))}</li>`;
            }
        }
        
        detailsHtml += '</ul></div>';
        return detailsHtml;
    }

    /**
     * 获取Bootstrap警告类型
     * @param {string} type - 错误类型
     * @returns {string} Bootstrap类型
     */
    getBootstrapAlertType(type) {
        const typeMap = {
            'error': 'danger',
            'warning': 'warning',
            'info': 'info',
            'success': 'success'
        };
        return typeMap[type] || 'danger';
    }

    /**
     * 获取类型标签
     * @param {string} type - 错误类型
     * @returns {string} 类型标签
     */
    getTypeLabel(type) {
        const labelMap = {
            'error': '错误',
            'warning': '警告',
            'info': '信息',
            'success': '成功'
        };
        return labelMap[type] || '错误';
    }

    /**
     * 转义HTML字符
     * @param {string} text - 要转义的文本
     * @returns {string} 转义后的文本
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * 判断是否应该显示详细信息
     * @returns {boolean} 是否显示详细信息
     */
    shouldShowDetails() {
        // 在开发环境或调试模式下显示详细信息
        return window.location.hostname === 'localhost' || 
               window.location.hostname === '127.0.0.1' ||
               localStorage.getItem('debug') === 'true';
    }

    /**
     * 移除警告元素
     * @param {HTMLElement} alertElement - 要移除的警告元素
     */
    removeAlert(alertElement) {
        if (alertElement && alertElement.parentNode) {
            // 添加淡出动画
            alertElement.classList.remove('show');
            
            // 等待动画完成后移除元素
            setTimeout(() => {
                if (alertElement.parentNode) {
                    alertElement.parentNode.removeChild(alertElement);
                }
            }, 150);
        }
    }

    /**
     * 清除所有错误信息
     */
    clearAllErrors() {
        const alerts = this.errorContainer.querySelectorAll('.alert');
        alerts.forEach(alert => {
            this.removeAlert(alert);
        });
    }

    /**
     * 处理API错误响应
     * @param {Response|Object} response - API响应或错误对象
     * @param {string} defaultMessage - 默认错误消息
     */
    async handleApiError(response, defaultMessage = '操作失败') {
        try {
            let errorData;
            
            if (response instanceof Response) {
                if (!response.ok) {
                    try {
                        errorData = await response.json();
                    } catch (e) {
                        errorData = {
                            message: `HTTP ${response.status}: ${response.statusText}`,
                            code: `HTTP_${response.status}`
                        };
                    }
                } else {
                    return; // 响应正常，不需要处理错误
                }
            } else {
                errorData = response;
            }

            // 提取错误信息
            const error = errorData.error || errorData;
            const message = error.message || defaultMessage;
            
            this.showError(error, 'error');
            
        } catch (e) {
            console.error('Error handling API error:', e);
            this.showError(defaultMessage, 'error');
        }
    }

    /**
     * 处理格式转换错误的回退机制
     * @param {Object} result - 转换结果
     * @param {string} targetFormat - 目标格式
     */
    handleFormatConversionFallback(result, targetFormat) {
        if (result.error && result.error.fallback_applied) {
            const message = `格式转换失败，已回退到文本格式: ${result.error.message}`;
            this.showWarning(message, 6000);
            
            // 更新UI状态以反映回退
            this.updateFormatSelectorAfterFallback();
        }
    }

    /**
     * 更新格式选择器状态（回退后）
     */
    updateFormatSelectorAfterFallback() {
        const textRadio = document.getElementById('format-text');
        if (textRadio) {
            textRadio.checked = true;
            
            // 触发change事件以更新UI
            const event = new Event('change', { bubbles: true });
            textRadio.dispatchEvent(event);
        }
    }

    /**
     * 显示网络错误
     * @param {Error} error - 网络错误
     */
    showNetworkError(error) {
        let message = '网络连接失败，请检查网络连接后重试';
        
        if (error.name === 'TypeError' && error.message.includes('fetch')) {
            message = '无法连接到服务器，请检查网络连接';
        } else if (error.name === 'AbortError') {
            message = '请求超时，请重试';
        }
        
        this.showError({
            message: message,
            code: 'NETWORK_ERROR',
            details: {
                error_name: error.name,
                error_message: error.message
            }
        }, 'error', 8000);
    }

    /**
     * 显示文件操作错误
     * @param {string} operation - 操作类型
     * @param {Error} error - 错误对象
     */
    showFileError(operation, error) {
        const operationMap = {
            'upload': '文件上传',
            'download': '文件下载',
            'read': '文件读取',
            'write': '文件写入'
        };
        
        const operationName = operationMap[operation] || operation;
        const message = `${operationName}失败: ${error.message}`;
        
        this.showError({
            message: message,
            code: 'FILE_OPERATION_ERROR',
            details: {
                operation: operation,
                error_type: error.constructor.name
            }
        }, 'error');
    }
}

// 创建全局错误处理器实例
window.errorHandler = new ErrorHandler();

// 导出类（如果使用模块系统）
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ErrorHandler;
}