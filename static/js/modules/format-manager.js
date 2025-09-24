/**
 * FormatManager - 管理文本格式转换功能
 * 负责处理纯文本和Markdown格式之间的转换
 */
class FormatManager {
    constructor() {
        this.currentFormat = 'text';
        this.originalText = '';
        this.convertedText = {};
        this.isConverting = false;
        this.initEventListeners();
    }

    /**
     * 初始化事件监听器
     */
    initEventListeners() {
        // 格式切换按钮事件
        document.addEventListener('change', (e) => {
            if (e.target.name === 'format') {
                this.handleFormatSwitch(e.target.value);
            }
        });
        
        // 键盘快捷键支持
        this.initKeyboardShortcuts();
    }

    /**
     * 初始化键盘快捷键
     */
    initKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // 检查是否在结果区域内
            const resultArea = document.getElementById('result-area');
            if (!resultArea || resultArea.style.display === 'none') return;
            
            // Ctrl/Cmd + 数字键切换格式
            if ((e.ctrlKey || e.metaKey) && !e.shiftKey && !e.altKey) {
                switch(e.key) {
                    case '1':
                        e.preventDefault();
                        this.switchToFormat('text');
                        this.showShortcutFeedback('切换到纯文本格式');
                        break;
                    case '2':
                        e.preventDefault();
                        this.switchToFormat('markdown');
                        this.showShortcutFeedback('切换到Markdown格式');
                        break;
                    case 'c':
                        // Ctrl+C 复制结果（如果焦点在结果区域）
                        if (document.activeElement && 
                            document.activeElement.id === 'result-text') {
                            // 让浏览器处理默认复制行为
                            setTimeout(() => {
                                this.showShortcutFeedback('已复制到剪贴板');
                            }, 100);
                        }
                        break;
                    case 'd':
                        // Ctrl+D 下载当前格式文件
                        e.preventDefault();
                        this.downloadCurrentFormat();
                        this.showShortcutFeedback(`下载${this.currentFormat === 'text' ? 'TXT' : 'MD'}文件`);
                        break;
                }
            }
            
            // Alt + 数字键切换Markdown视图（仅在Markdown格式时）
            if (e.altKey && !e.ctrlKey && !e.metaKey && this.currentFormat === 'markdown') {
                switch(e.key) {
                    case '1':
                        e.preventDefault();
                        this.switchMarkdownView('raw');
                        this.showShortcutFeedback('切换到原始代码视图');
                        break;
                    case '2':
                        e.preventDefault();
                        this.switchMarkdownView('preview');
                        this.showShortcutFeedback('切换到预览视图');
                        break;
                    case '3':
                        e.preventDefault();
                        this.switchMarkdownView('split');
                        this.showShortcutFeedback('切换到并排视图');
                        break;
                }
            }
        });
    }

    /**
     * 切换到指定格式
     * @param {string} format - 目标格式
     */
    switchToFormat(format) {
        const formatRadio = document.querySelector(`input[name="format"][value="${format}"]`);
        if (formatRadio && !formatRadio.disabled) {
            formatRadio.checked = true;
            formatRadio.dispatchEvent(new Event('change'));
        }
    }

    /**
     * 切换Markdown视图
     * @param {string} view - 视图类型
     */
    switchMarkdownView(view) {
        const viewRadio = document.querySelector(`input[name="markdown-view"][value="${view}"]`);
        if (viewRadio && !viewRadio.disabled) {
            viewRadio.checked = true;
            viewRadio.dispatchEvent(new Event('change'));
        }
    }

    /**
     * 下载当前格式文件
     */
    downloadCurrentFormat() {
        const downloadBtn = document.querySelector(`.download-btn[data-format="${this.currentFormat}"]`);
        if (downloadBtn && !downloadBtn.disabled) {
            downloadBtn.click();
        }
    }

    /**
     * 显示快捷键反馈
     * @param {string} message - 反馈消息
     */
    showShortcutFeedback(message) {
        // 创建临时提示
        const feedback = document.createElement('div');
        feedback.className = 'shortcut-feedback';
        feedback.textContent = message;
        feedback.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: rgba(13, 110, 253, 0.9);
            color: white;
            padding: 8px 16px;
            border-radius: 4px;
            font-size: 14px;
            z-index: 1050;
            animation: fadeInOut 2s ease-in-out;
        `;
        
        document.body.appendChild(feedback);
        
        // 2秒后移除
        setTimeout(() => {
            if (feedback.parentNode) {
                feedback.parentNode.removeChild(feedback);
            }
        }, 2000);
    }

    /**
     * 处理格式切换
     * @param {string} targetFormat - 目标格式 ('text' 或 'markdown')
     */
    async handleFormatSwitch(targetFormat) {
        if (this.currentFormat === targetFormat) return;

        const resultTextarea = document.getElementById('result-text');
        if (!resultTextarea || !resultTextarea.value.trim()) {
            this.currentFormat = targetFormat;
            return;
        }

        try {
            this.showLoadingState(true);
            
            if (targetFormat === 'text') {
                // 切换到纯文本格式
                this.displayText(this.originalText || resultTextarea.value);
            } else {
                // 切换到Markdown格式
                const convertedResult = await this.convertFormat(
                    this.originalText || resultTextarea.value, 
                    targetFormat
                );
                if (convertedResult.success) {
                    this.displayText(convertedResult.data.content);
                    this.convertedText[targetFormat] = convertedResult.data.content;
                } else {
                    throw new Error(convertedResult.error?.message || '格式转换失败');
                }
            }
            
            this.currentFormat = targetFormat;
            this.updateFormatControls(targetFormat);
            
        } catch (error) {
            console.error('Format switch error:', error);
            
            // 使用全局错误处理器
            if (window.errorHandler) {
                window.errorHandler.showError(error, 'error');
                window.errorHandler.handleFormatConversionFallback({
                    error: { fallback_applied: true, message: error.message }
                }, targetFormat);
            } else {
                this.showError(`格式转换失败: ${error.message}`);
            }
            
            // 回退到之前的格式
            this.revertFormatSelection();
        } finally {
            this.showLoadingState(false);
        }
    }

    /**
     * 调用API进行格式转换
     * @param {string} text - 要转换的文本
     * @param {string} targetFormat - 目标格式
     * @returns {Promise<Object>} 转换结果
     */
    async convertFormat(text, targetFormat) {
        if (this.isConverting) {
            throw new Error('正在转换中，请稍候...');
        }

        this.isConverting = true;
        
        try {
            const response = await fetch('/api/convert-format', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    text: text,
                    target_format: targetFormat
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();
            return result;
            
        } catch (error) {
            console.error('API call error:', error);
            
            // 使用全局错误处理器处理网络错误
            if (window.errorHandler && error.name === 'TypeError') {
                window.errorHandler.showNetworkError(error);
            }
            
            throw error;
        } finally {
            this.isConverting = false;
        }
    }

    /**
     * 设置原始文本（OCR识别结果）
     * @param {string} text - 原始文本
     */
    setOriginalText(text) {
        this.originalText = text;
        this.convertedText = {};
        this.currentFormat = 'text';
        this.displayText(text);
        this.updateFormatControls('text');
    }

    /**
     * 显示文本内容
     * @param {string} text - 要显示的文本
     */
    displayText(text) {
        const resultTextarea = document.getElementById('result-text');
        if (resultTextarea) {
            resultTextarea.value = text;
        }
    }

    /**
     * 更新格式控制按钮状态
     * @param {string} format - 当前格式
     */
    updateFormatControls(format) {
        const formatRadios = document.querySelectorAll('input[name="format"]');
        formatRadios.forEach(radio => {
            radio.checked = radio.value === format;
        });

        // 更新预览区域显示状态
        this.updatePreviewDisplay(format);
    }

    /**
     * 更新预览区域显示
     * @param {string} format - 当前格式
     */
    updatePreviewDisplay(format) {
        const textContent = document.querySelector('.text-content');
        const markdownPreview = document.querySelector('.markdown-preview');
        
        if (format === 'markdown') {
            // 显示Markdown预览选项
            this.showMarkdownControls(true);
        } else {
            // 隐藏Markdown预览选项
            this.showMarkdownControls(false);
            if (textContent) textContent.style.display = 'block';
            if (markdownPreview) markdownPreview.style.display = 'none';
        }
    }

    /**
     * 显示/隐藏Markdown控制按钮
     * @param {boolean} show - 是否显示
     */
    showMarkdownControls(show) {
        const markdownControls = document.querySelector('.markdown-view-controls');
        if (markdownControls) {
            markdownControls.style.display = show ? 'block' : 'none';
        }
    }

    /**
     * 显示加载状态
     * @param {boolean} loading - 是否显示加载状态
     */
    showLoadingState(loading) {
        const formatSelector = document.querySelector('.format-selector');
        const resultArea = document.getElementById('result-area');
        
        if (loading) {
            // 添加加载状态到格式选择器
            if (formatSelector) {
                formatSelector.classList.add('loading');
            }
            
            // 显示全局加载覆盖层
            this.showLoadingOverlay(true, '正在转换格式...');
            
            // 禁用相关按钮
            this.toggleButtonsState(false);
            
        } else {
            // 移除加载状态
            if (formatSelector) {
                formatSelector.classList.remove('loading');
            }
            
            // 隐藏加载覆盖层
            this.showLoadingOverlay(false);
            
            // 启用相关按钮
            this.toggleButtonsState(true);
        }
    }

    /**
     * 显示/隐藏加载覆盖层
     * @param {boolean} show - 是否显示
     * @param {string} message - 加载消息
     */
    showLoadingOverlay(show, message = '处理中...') {
        let overlay = document.getElementById('format-loading-overlay');
        
        if (show) {
            if (!overlay) {
                overlay = document.createElement('div');
                overlay.id = 'format-loading-overlay';
                overlay.className = 'loading-overlay';
                overlay.innerHTML = `
                    <div class="text-center">
                        <div class="loading-spinner mb-2"></div>
                        <div class="loading-message small text-muted">${message}</div>
                        <div class="loading-progress mt-2">
                            <div class="progress" style="width: 200px; height: 4px;">
                                <div class="progress-bar progress-bar-striped progress-bar-animated" 
                                     role="progressbar" style="width: 0%"></div>
                            </div>
                        </div>
                    </div>
                `;
                
                const resultDisplay = document.querySelector('.result-display');
                if (resultDisplay) {
                    resultDisplay.style.position = 'relative';
                    resultDisplay.appendChild(overlay);
                }
            }
            
            // 启动进度条动画
            this.animateProgress();
            
        } else {
            if (overlay) {
                overlay.remove();
            }
        }
    }

    /**
     * 进度条动画
     */
    animateProgress() {
        const progressBar = document.querySelector('#format-loading-overlay .progress-bar');
        if (!progressBar) return;
        
        let progress = 0;
        const interval = setInterval(() => {
            progress += Math.random() * 30;
            if (progress > 90) progress = 90;
            
            progressBar.style.width = `${progress}%`;
            
            if (!document.getElementById('format-loading-overlay')) {
                clearInterval(interval);
            }
        }, 200);
        
        // 存储interval ID以便清理
        this.progressInterval = interval;
    }

    /**
     * 切换按钮状态
     * @param {boolean} enabled - 是否启用
     */
    toggleButtonsState(enabled) {
        // 格式选择按钮
        const formatButtons = document.querySelectorAll('input[name="format"]');
        formatButtons.forEach(btn => btn.disabled = !enabled);
        
        // 下载按钮
        const downloadButtons = document.querySelectorAll('.download-btn');
        downloadButtons.forEach(btn => btn.disabled = !enabled);
        
        // 复制按钮
        const copyButton = document.querySelector('button[onclick="copyResult()"]');
        if (copyButton) copyButton.disabled = !enabled;
        
        // Markdown视图控制按钮
        const viewButtons = document.querySelectorAll('input[name="markdown-view"]');
        viewButtons.forEach(btn => btn.disabled = !enabled);
    }

    /**
     * 显示错误信息
     * @param {string} message - 错误信息
     */
    showError(message) {
        // 创建错误提示
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-warning alert-dismissible fade show mt-2';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        // 插入到格式选择器下方
        const formatSelector = document.querySelector('.format-selector');
        if (formatSelector && formatSelector.parentNode) {
            formatSelector.parentNode.insertBefore(alertDiv, formatSelector.nextSibling);
            
            // 3秒后自动移除
            setTimeout(() => {
                if (alertDiv.parentNode) {
                    alertDiv.parentNode.removeChild(alertDiv);
                }
            }, 3000);
        }
    }

    /**
     * 回退格式选择
     */
    revertFormatSelection() {
        const formatRadios = document.querySelectorAll('input[name="format"]');
        formatRadios.forEach(radio => {
            radio.checked = radio.value === this.currentFormat;
        });
    }

    /**
     * 获取当前显示的文本内容
     * @returns {string} 当前文本内容
     */
    getCurrentText() {
        const resultTextarea = document.getElementById('result-text');
        return resultTextarea ? resultTextarea.value : '';
    }

    /**
     * 获取当前格式
     * @returns {string} 当前格式
     */
    getCurrentFormat() {
        return this.currentFormat;
    }
}

// 导出类（如果使用模块系统）
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FormatManager;
}