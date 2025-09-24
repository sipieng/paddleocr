/**
 * DownloadManager - 管理文件下载功能
 * 负责处理不同格式文件的下载
 */
class DownloadManager {
    constructor() {
        this.downloadHistory = [];
        this.initEventListeners();
    }

    /**
     * 初始化事件监听器
     */
    initEventListeners() {
        // 下载按钮事件
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('download-btn')) {
                const format = e.target.dataset.format || 'text';
                this.handleDownload(format);
            }
        });
    }

    /**
     * 处理文件下载
     * @param {string} format - 下载格式 ('text' 或 'markdown')
     */
    async handleDownload(format) {
        try {
            // 获取当前文本内容
            const content = this.getCurrentContent();
            if (!content.trim()) {
                this.showError('没有可下载的内容');
                return;
            }

            // 显示下载开始提示
            this.showDownloadStarted(format);

            // 生成文件名
            const filename = this.generateFilename(format);
            
            // 创建并触发下载
            await this.downloadFile(content, format, filename);
            
            // 记录下载历史
            this.addToHistory(filename, format, content.length);
            
            // 显示成功提示
            this.showSuccess(`文件 ${filename} 下载成功`);
            
        } catch (error) {
            console.error('Download error:', error);
            
            // 使用全局错误处理器
            if (window.errorHandler) {
                window.errorHandler.showFileError('download', error);
            } else {
                this.showError(`下载失败: ${error.message}`);
            }
        }
    }

    /**
     * 获取当前文本内容
     * @returns {string} 当前文本内容
     */
    getCurrentContent() {
        const resultTextarea = document.getElementById('result-text');
        return resultTextarea ? resultTextarea.value : '';
    }

    /**
     * 下载文件
     * @param {string} content - 文件内容
     * @param {string} format - 文件格式
     * @param {string} filename - 文件名
     */
    async downloadFile(content, format, filename) {
        try {
            // 方法1: 使用API端点下载（如果后端支持）
            const response = await fetch('/api/download-result', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    content: content,
                    format: format,
                    filename: filename
                })
            });

            if (response.ok) {
                // 从响应中获取文件
                const blob = await response.blob();
                this.triggerDownload(blob, filename);
                return;
            }
        } catch (error) {
            console.warn('API download failed, using client-side download:', error);
        }

        // 方法2: 客户端直接下载（备用方案）
        this.clientSideDownload(content, format, filename);
    }

    /**
     * 客户端直接下载
     * @param {string} content - 文件内容
     * @param {string} format - 文件格式
     * @param {string} filename - 文件名
     */
    clientSideDownload(content, format, filename) {
        const mimeType = this.getMimeType(format);
        const blob = new Blob([content], { type: mimeType });
        this.triggerDownload(blob, filename);
    }

    /**
     * 触发文件下载
     * @param {Blob} blob - 文件数据
     * @param {string} filename - 文件名
     */
    triggerDownload(blob, filename) {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.style.display = 'none';
        
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        
        // 清理URL对象
        setTimeout(() => URL.revokeObjectURL(url), 100);
    }

    /**
     * 生成文件名
     * @param {string} format - 文件格式
     * @returns {string} 生成的文件名
     */
    generateFilename(format) {
        const now = new Date();
        const timestamp = now.toISOString()
            .replace(/[:.]/g, '-')
            .replace('T', '_')
            .substring(0, 19);
        
        // 生成更友好的文件名
        const formatPrefix = {
            'text': 'OCR文本',
            'markdown': 'OCR文档'
        };
        
        const prefix = formatPrefix[format] || 'OCR结果';
        const extension = this.getFileExtension(format);
        
        return `${prefix}_${timestamp}.${extension}`;
    }

    /**
     * 获取文件扩展名
     * @param {string} format - 文件格式
     * @returns {string} 文件扩展名
     */
    getFileExtension(format) {
        const extensions = {
            'text': 'txt',
            'markdown': 'md',
            'html': 'html',
            'pdf': 'pdf'
        };
        return extensions[format] || 'txt';
    }

    /**
     * 获取MIME类型
     * @param {string} format - 文件格式
     * @returns {string} MIME类型
     */
    getMimeType(format) {
        const mimeTypes = {
            'text': 'text/plain;charset=utf-8',
            'markdown': 'text/markdown;charset=utf-8',
            'html': 'text/html;charset=utf-8',
            'pdf': 'application/pdf'
        };
        return mimeTypes[format] || 'text/plain;charset=utf-8';
    }

    /**
     * 添加到下载历史
     * @param {string} filename - 文件名
     * @param {string} format - 文件格式
     * @param {number} size - 文件大小（字符数）
     */
    addToHistory(filename, format, size) {
        const historyItem = {
            filename,
            format,
            size,
            timestamp: new Date().toISOString(),
            id: Date.now()
        };
        
        this.downloadHistory.unshift(historyItem);
        
        // 限制历史记录数量
        if (this.downloadHistory.length > 10) {
            this.downloadHistory = this.downloadHistory.slice(0, 10);
        }
        
        // 更新历史显示（如果有的话）
        this.updateHistoryDisplay();
    }

    /**
     * 更新历史显示
     */
    updateHistoryDisplay() {
        const historyContainer = document.querySelector('.download-history');
        if (!historyContainer) return;

        if (this.downloadHistory.length === 0) {
            historyContainer.innerHTML = '<p class="text-muted">暂无下载记录</p>';
            return;
        }

        const historyHTML = this.downloadHistory.map(item => `
            <div class="download-history-item">
                <div class="filename">${item.filename}</div>
                <div class="details">
                    <span class="format badge bg-secondary">${item.format}</span>
                    <span class="size">${item.size} 字符</span>
                    <span class="time">${new Date(item.timestamp).toLocaleString()}</span>
                </div>
            </div>
        `).join('');

        historyContainer.innerHTML = historyHTML;
    }

    /**
     * 获取下载历史
     * @returns {Array} 下载历史记录
     */
    getDownloadHistory() {
        return [...this.downloadHistory];
    }

    /**
     * 清空下载历史
     */
    clearHistory() {
        this.downloadHistory = [];
        this.updateHistoryDisplay();
    }

    /**
     * 显示下载开始提示
     * @param {string} format - 下载格式
     */
    showDownloadStarted(format) {
        const formatNames = {
            'text': '纯文本',
            'markdown': 'Markdown'
        };
        const formatName = formatNames[format] || format;
        this.showMessage(`正在准备 ${formatName} 文件下载...`, 'info');
    }

    /**
     * 显示成功信息
     * @param {string} message - 成功信息
     */
    showSuccess(message) {
        this.showMessage(message, 'success');
    }

    /**
     * 显示错误信息
     * @param {string} message - 错误信息
     */
    showError(message) {
        this.showMessage(message, 'danger');
    }

    /**
     * 显示消息
     * @param {string} message - 消息内容
     * @param {string} type - 消息类型 ('success', 'danger', 'warning', 'info')
     */
    showMessage(message, type = 'info') {
        // 创建消息提示
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show mt-2`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        // 插入到下载按钮区域附近
        const downloadControls = document.querySelector('.download-controls') || 
                                document.querySelector('.format-controls') ||
                                document.querySelector('.result-display');
        
        if (downloadControls) {
            downloadControls.appendChild(alertDiv);
            
            // 3秒后自动移除
            setTimeout(() => {
                if (alertDiv.parentNode) {
                    alertDiv.parentNode.removeChild(alertDiv);
                }
            }, 3000);
        }
    }

    /**
     * 批量下载多种格式
     * @param {Array<string>} formats - 要下载的格式列表
     */
    async batchDownload(formats) {
        const content = this.getCurrentContent();
        if (!content.trim()) {
            this.showError('没有可下载的内容');
            return;
        }

        try {
            for (const format of formats) {
                const filename = this.generateFilename(format);
                await this.downloadFile(content, format, filename);
                this.addToHistory(filename, format, content.length);
                
                // 添加小延迟避免浏览器阻止多个下载
                await new Promise(resolve => setTimeout(resolve, 100));
            }
            
            this.showSuccess(`成功下载 ${formats.length} 个文件`);
        } catch (error) {
            console.error('Batch download error:', error);
            this.showError(`批量下载失败: ${error.message}`);
        }
    }

    /**
     * 测试下载功能
     * @param {string} format - 测试格式
     */
    testDownload(format = 'text') {
        const testContent = `测试文档

这是一个测试文档，用于验证下载功能。

## 功能特点
- 支持纯文本格式
- 支持Markdown格式
- 自动生成文件名
- 完整的错误处理

### 测试时间
${new Date().toLocaleString()}

感谢使用 PaddleOCR 系统！`;

        // 临时设置测试内容
        const resultText = document.getElementById('result-text');
        const originalContent = resultText ? resultText.value : '';
        
        if (resultText) {
            resultText.value = testContent;
        }
        
        // 执行下载
        this.handleDownload(format).then(() => {
            // 恢复原始内容
            if (resultText) {
                resultText.value = originalContent;
            }
        });
    }
}

// 导出类（如果使用模块系统）
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DownloadManager;
}