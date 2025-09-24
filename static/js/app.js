let ocrReady = false;
let checkInterval;
let formatManager;
let downloadManager;

// 页面加载完成后开始检查状态
document.addEventListener('DOMContentLoaded', function() {
    console.log('页面加载完成，开始检查系统状态');
    initializeManagers();
    initializeTooltips();
    checkSystemStatus();
});

// 初始化Bootstrap工具提示
function initializeTooltips() {
    // 初始化所有工具提示
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // 为动态添加的元素初始化工具提示
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            mutation.addedNodes.forEach(function(node) {
                if (node.nodeType === 1) { // Element node
                    const tooltips = node.querySelectorAll('[data-bs-toggle="tooltip"]');
                    tooltips.forEach(function(tooltip) {
                        new bootstrap.Tooltip(tooltip);
                    });
                }
            });
        });
    });
    
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
}

// 初始化格式管理器和下载管理器
function initializeManagers() {
    // 动态加载模块
    loadFormatManagers().then(() => {
        console.log('格式管理器初始化完成');
    }).catch(error => {
        console.error('格式管理器初始化失败:', error);
    });
}

// 加载格式管理器模块
async function loadFormatManagers() {
    try {
        // 由于不是ES6模块环境，直接创建实例
        if (typeof FormatManager !== 'undefined') {
            formatManager = new FormatManager();
        }
        if (typeof DownloadManager !== 'undefined') {
            downloadManager = new DownloadManager();
        }
        
        // 如果类未定义，动态加载脚本
        if (!formatManager || !downloadManager) {
            await loadModuleScripts();
        }
    } catch (error) {
        console.error('加载格式管理器失败:', error);
    }
}

// 动态加载模块脚本
function loadModuleScripts() {
    return new Promise((resolve, reject) => {
        let scriptsLoaded = 0;
        const totalScripts = 2;
        
        function onScriptLoad() {
            scriptsLoaded++;
            if (scriptsLoaded === totalScripts) {
                // 创建管理器实例
                formatManager = new FormatManager();
                downloadManager = new DownloadManager();
                resolve();
            }
        }
        
        // 加载FormatManager
        const formatScript = document.createElement('script');
        formatScript.src = '/static/js/modules/format-manager.js';
        formatScript.onload = onScriptLoad;
        formatScript.onerror = () => reject(new Error('Failed to load format-manager.js'));
        document.head.appendChild(formatScript);
        
        // 加载DownloadManager
        const downloadScript = document.createElement('script');
        downloadScript.src = '/static/js/modules/download-manager.js';
        downloadScript.onload = onScriptLoad;
        downloadScript.onerror = () => reject(new Error('Failed to load download-manager.js'));
        document.head.appendChild(downloadScript);
    });
}

async function checkSystemStatus() {
    try {
        console.log('检查系统状态...');
        const response = await fetch('/api/status');
        const data = await response.json();
        
        console.log('系统状态:', data);
        
        if (data.success) {
            updateSystemStatus(data.data);
            
            // 如果模型已下载且OCR未初始化，自动启动
            if (data.data.can_init_immediately && !data.data.ocr_ready && !data.data.ocr_initializing) {
                console.log('模型已就绪，自动启动OCR服务');
                setTimeout(() => {
                    initOCR();
                }, 1000); // 延迟1秒自动启动
            }
        } else {
            showError('获取系统状态失败: ' + (data.error?.message || '未知错误'));
        }
    } catch (error) {
        console.error('检查系统状态失败:', error);
        showError('无法连接到服务器: ' + error.message);
    }
}

function updateSystemStatus(status) {
    const ocrStatus = document.getElementById('ocr-status');
    const uploadContent = document.getElementById('upload-content');
    
    // 更新模型信息显示
    updateModelsInfo(status.models_info || []);
    
    if (status.ocr_ready) {
        // OCR已就绪
        ocrReady = true;
        ocrStatus.className = 'badge bg-success';
        ocrStatus.textContent = '已就绪';
        
        uploadContent.innerHTML = `
            <i class="fas fa-cloud-upload-alt fa-3x text-muted mb-3"></i>
            <h5>拖拽图片到此处或点击下方按钮</h5>
            <p class="text-muted">支持 JPG, PNG, BMP, TIFF 格式<br>最大文件大小: 10MB</p>
            <button type="button" class="btn btn-primary" id="select-file-btn">
                <i class="fas fa-folder-open me-1"></i>选择文件
            </button>
        `;
        
        // 绑定拖拽事件
        bindUploadEvents();
        
    } else if (status.ocr_initializing) {
        // OCR正在初始化
        ocrStatus.className = 'badge bg-warning';
        ocrStatus.textContent = '启动中';
        
        if (status.can_init_immediately) {
            uploadContent.innerHTML = `
                <div class="spinner-border text-success mb-3" role="status"></div>
                <h5>正在启动OCR服务</h5>
                <p class="text-muted">正在加载已下载的模型文件...<br>这通常只需要几秒钟时间</p>
                <div class="progress mb-3" style="height: 6px;">
                    <div class="progress-bar progress-bar-striped progress-bar-animated bg-success" 
                         role="progressbar" style="width: 100%"></div>
                </div>
            `;
        } else {
            uploadContent.innerHTML = `
                <div class="spinner-border text-primary mb-3" role="status"></div>
                <h5>正在初始化OCR服务</h5>
                <p class="text-muted">正在下载模型文件，请耐心等待...<br>这可能需要几分钟时间</p>
                <div class="progress mb-3" style="height: 6px;">
                    <div class="progress-bar progress-bar-striped progress-bar-animated" 
                         role="progressbar" style="width: 100%"></div>
                </div>
            `;
        }
        
        // 继续检查状态
        setTimeout(checkSystemStatus, 2000); // 缩短检查间隔
        
    } else if (status.ocr_error) {
        // OCR初始化失败
        ocrStatus.className = 'badge bg-danger';
        ocrStatus.textContent = '初始化失败';
        
        uploadContent.innerHTML = `
            <i class="fas fa-exclamation-triangle fa-3x text-danger mb-3"></i>
            <h5>OCR服务初始化失败</h5>
            <p class="text-muted">${status.ocr_error}</p>
            <button type="button" class="btn btn-primary" onclick="initOCR()">
                <i class="fas fa-redo me-1"></i>重试初始化
            </button>
        `;
        
    } else if (!status.paddle_available) {
        // PaddleOCR未安装
        ocrStatus.className = 'badge bg-danger';
        ocrStatus.textContent = 'PaddleOCR未安装';
        
        uploadContent.innerHTML = `
            <i class="fas fa-exclamation-circle fa-3x text-warning mb-3"></i>
            <h5>PaddleOCR未安装</h5>
            <p class="text-muted">请安装必要的依赖包</p>
            <div class="alert alert-info text-start">
                <h6>安装命令:</h6>
                <code>pip install paddlepaddle paddleocr</code>
            </div>
            <button type="button" class="btn btn-primary" onclick="location.reload()">
                <i class="fas fa-redo me-1"></i>重新检测
            </button>
        `;
        
    } else {
        // 需要初始化
        ocrStatus.className = 'badge bg-secondary';
        ocrStatus.textContent = '未初始化';
        
        if (status.can_init_immediately) {
            // 模型已下载，显示自动启动提示
            uploadContent.innerHTML = `
                <i class="fas fa-rocket fa-3x text-success mb-3"></i>
                <h5>OCR服务准备就绪</h5>
                <p class="text-muted">检测到已下载的模型文件<br>正在自动启动服务...</p>
                <div class="progress mb-3">
                    <div class="progress-bar progress-bar-striped progress-bar-animated bg-success" 
                         role="progressbar" style="width: 100%"></div>
                </div>
                <div class="mt-3">
                    <small class="text-success">
                        <i class="fas fa-check me-1"></i>
                        模型文件已就绪，无需重新下载
                    </small>
                </div>
            `;
        } else if (status.models_downloaded) {
            // 模型已下载但可能不完整
            uploadContent.innerHTML = `
                <i class="fas fa-exclamation-triangle fa-3x text-warning mb-3"></i>
                <h5>模型文件可能不完整</h5>
                <p class="text-muted">检测到部分模型文件，但可能不完整<br>建议重新下载以确保正常工作</p>
                <div class="d-grid gap-2">
                    <button type="button" class="btn btn-warning btn-lg" onclick="initOCR()">
                        <i class="fas fa-redo me-2"></i>重新初始化
                    </button>
                    <button type="button" class="btn btn-outline-secondary" onclick="showManualGuide()">
                        <i class="fas fa-info-circle me-2"></i>手动下载说明
                    </button>
                </div>
            `;
        } else {
            // 需要首次下载
            uploadContent.innerHTML = `
                <i class="fas fa-download fa-3x text-primary mb-3"></i>
                <h5>OCR服务需要初始化</h5>
                <p class="text-muted">首次使用需要下载模型文件（约18MB）<br>初始化过程可能需要2-5分钟</p>
                <div class="d-grid gap-2">
                    <button type="button" class="btn btn-primary btn-lg" onclick="initOCR()">
                        <i class="fas fa-download me-2"></i>下载并初始化
                    </button>
                    <button type="button" class="btn btn-outline-secondary" onclick="showManualGuide()">
                        <i class="fas fa-info-circle me-2"></i>手动下载说明
                    </button>
                </div>
            `;
        }
    }
}

async function initOCR() {
    try {
        console.log('开始初始化OCR服务...');
        
        // 先获取当前状态
        const statusResponse = await fetch('/api/status');
        const statusData = await statusResponse.json();
        const canInitImmediately = statusData.success && statusData.data.can_init_immediately;
        
        const uploadContent = document.getElementById('upload-content');
        
        // 根据是否需要下载显示不同的提示
        if (canInitImmediately) {
            uploadContent.innerHTML = `
                <div class="spinner-border text-success mb-3" role="status"></div>
                <h5>正在启动OCR服务</h5>
                <p class="text-muted">正在加载已下载的模型文件...<br>这通常只需要几秒钟时间</p>
            `;
        } else {
            uploadContent.innerHTML = `
                <div class="spinner-border text-primary mb-3" role="status"></div>
                <h5>正在初始化OCR服务</h5>
                <p class="text-muted">正在下载和配置模型文件...<br>请耐心等待，这可能需要几分钟时间</p>
            `;
        }
        
        const response = await fetch('/api/init-ocr', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ auto_download: true })
        });
        
        const data = await response.json();
        console.log('初始化响应:', data);
        
        if (data.success) {
            // 开始轮询状态
            setTimeout(checkSystemStatus, 3000);
        } else {
            throw new Error(data.error?.message || '初始化失败');
        }
        
    } catch (error) {
        console.error('初始化失败:', error);
        showError('初始化失败: ' + error.message);
    }
}

function showError(message) {
    const statusIndicator = document.querySelector('.status-indicator');
    const statusText = document.getElementById('status-text');
    
    statusIndicator.className = 'status-indicator status-offline';
    statusText.textContent = '系统异常';
    
    const uploadContent = document.getElementById('upload-content');
    uploadContent.innerHTML = `
        <i class="fas fa-exclamation-triangle fa-3x text-danger mb-3"></i>
        <h5>系统错误</h5>
        <p class="text-muted">${message}</p>
        <button type="button" class="btn btn-primary" onclick="location.reload()">
            <i class="fas fa-redo me-1"></i>刷新页面
        </button>
    `;
}

function bindUploadEvents() {
    const uploadArea = document.getElementById('upload-area');
    const fileInput = document.getElementById('file-input');
    
    // 清除之前的事件监听器
    uploadArea.onclick = null;
    fileInput.onchange = null;
    
    // 绑定按钮点击事件
    setTimeout(() => {
        const selectButton = document.getElementById('select-file-btn');
        if (selectButton) {
            selectButton.onclick = function(e) {
                e.preventDefault();
                e.stopPropagation();
                if (!ocrReady) {
                    alert('OCR服务未就绪，请先初始化');
                    return;
                }
                fileInput.click();
            };
        }
    }, 100);
    
    // 文件选择事件
    fileInput.onchange = function(e) {
        const files = e.target.files;
        if (files.length > 0) {
            processFile(files[0]);
        }
        // 清空input以允许重复选择同一文件
        e.target.value = '';
    };
    
    // 拖拽事件
    uploadArea.ondragover = function(e) {
        e.preventDefault();
        e.currentTarget.style.borderColor = '#0d6efd';
        e.currentTarget.style.backgroundColor = '#e7f1ff';
    };
    
    uploadArea.ondragleave = function(e) {
        e.preventDefault();
        e.currentTarget.style.borderColor = '#dee2e6';
        e.currentTarget.style.backgroundColor = '#f8f9fa';
    };
    
    uploadArea.ondrop = function(e) {
        e.preventDefault();
        e.currentTarget.style.borderColor = '#dee2e6';
        e.currentTarget.style.backgroundColor = '#f8f9fa';
        
        if (!ocrReady) {
            alert('OCR服务未就绪，请先初始化');
            return;
        }
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            processFile(files[0]);
        }
    };
}

async function processFile(file) {
    if (!ocrReady) {
        alert('OCR服务未就绪');
        return;
    }
    
    try {
        const uploadContent = document.getElementById('upload-content');
        uploadContent.innerHTML = `
            <div class="spinner-border text-primary mb-3" role="status"></div>
            <h5>正在处理图像...</h5>
            <p class="text-muted">文件: ${file.name}</p>
        `;
        
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch('/api/ocr', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            showResult(data.data.text_content);
        } else {
            throw new Error(data.error?.message || '处理失败');
        }
        
    } catch (error) {
        console.error('处理文件失败:', error);
        alert('处理失败: ' + error.message);
    } finally {
        // 恢复上传界面
        setTimeout(() => {
            checkSystemStatus();
        }, 1000);
    }
}

function showResult(text) {
    const resultArea = document.getElementById('result-area');
    const resultText = document.getElementById('result-text');
    
    resultText.value = text;
    resultArea.style.display = 'block';
    
    // 使用格式管理器设置原始文本
    if (formatManager) {
        formatManager.setOriginalText(text);
    }
    
    // 初始化Markdown视图控制事件
    initializeMarkdownViewControls();
    
    // 滚动到结果区域
    resultArea.scrollIntoView({ behavior: 'smooth' });
}

function copyResult() {
    let textToCopy = '';
    let formatType = 'text';
    
    // 确定当前显示的格式和内容
    if (formatManager && formatManager.getCurrentFormat) {
        formatType = formatManager.getCurrentFormat();
    }
    
    // 根据当前格式和视图状态确定要复制的内容
    if (formatType === 'markdown') {
        // 对于Markdown格式，始终复制原始markdown代码，而非渲染后的HTML
        const currentView = getCurrentMarkdownView();
        
        if (currentView === 'preview' && isPreviewOnlyVisible()) {
            // 如果只显示预览，从result-text获取原始markdown
            const resultText = document.getElementById('result-text');
            textToCopy = resultText ? resultText.value : '';
        } else {
            // 从markdown-raw或result-text获取原始代码
            const markdownRaw = document.getElementById('markdown-raw');
            const resultText = document.getElementById('result-text');
            textToCopy = (markdownRaw && markdownRaw.value) || (resultText && resultText.value) || '';
        }
    } else {
        // 对于纯文本格式，直接复制result-text的内容
        const resultText = document.getElementById('result-text');
        textToCopy = resultText ? resultText.value : '';
    }
    
    if (textToCopy.trim()) {
        // 使用现代的Clipboard API，如果不支持则回退到execCommand
        if (navigator.clipboard && window.isSecureContext) {
            navigator.clipboard.writeText(textToCopy).then(() => {
                showCopySuccess(formatType);
            }).catch(error => {
                console.warn('Clipboard API failed, falling back to execCommand:', error);
                fallbackCopy(textToCopy, formatType);
            });
        } else {
            fallbackCopy(textToCopy, formatType);
        }
    } else {
        showCopyError('没有可复制的内容');
    }
}

// 回退复制方法（使用execCommand）
function fallbackCopy(text, formatType) {
    try {
        // 创建临时textarea元素
        const tempTextarea = document.createElement('textarea');
        tempTextarea.value = text;
        tempTextarea.style.position = 'fixed';
        tempTextarea.style.left = '-999999px';
        tempTextarea.style.top = '-999999px';
        document.body.appendChild(tempTextarea);
        
        tempTextarea.focus();
        tempTextarea.select();
        
        const successful = document.execCommand('copy');
        document.body.removeChild(tempTextarea);
        
        if (successful) {
            showCopySuccess(formatType);
        } else {
            throw new Error('execCommand failed');
        }
    } catch (error) {
        console.error('Copy failed:', error);
        showCopyError('复制失败，请手动选择文本复制');
    }
}

// 获取当前Markdown视图模式
function getCurrentMarkdownView() {
    const viewControls = document.querySelectorAll('input[name="markdown-view"]');
    for (const control of viewControls) {
        if (control.checked) {
            return control.value;
        }
    }
    return 'raw'; // 默认返回raw
}

// 检查是否只显示预览（preview模式且原始代码列隐藏）
function isPreviewOnlyVisible() {
    const markdownRawCol = document.querySelector('.markdown-raw-col');
    return markdownRawCol && markdownRawCol.style.display === 'none';
}

// 显示复制成功提示
function showCopySuccess(formatType = 'text') {
    // 根据格式类型显示不同的提示信息
    const formatMessages = {
        'text': '纯文本已复制到剪贴板',
        'markdown': 'Markdown代码已复制到剪贴板'
    };
    
    const formatIcons = {
        'text': 'fas fa-file-alt',
        'markdown': 'fab fa-markdown'
    };
    
    const message = formatMessages[formatType] || '内容已复制到剪贴板';
    const icon = formatIcons[formatType] || 'fas fa-check';
    
    // 创建临时提示元素
    const toast = document.createElement('div');
    toast.className = 'alert alert-success alert-dismissible fade show position-fixed';
    toast.style.cssText = 'top: 20px; right: 20px; z-index: 1050; min-width: 250px;';
    toast.innerHTML = `
        <i class="${icon} me-2"></i>${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    document.body.appendChild(toast);
    
    // 3秒后自动移除
    setTimeout(() => {
        if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
        }
    }, 3000);
}

// 显示复制错误提示
function showCopyError(message) {
    const toast = document.createElement('div');
    toast.className = 'alert alert-warning alert-dismissible fade show position-fixed';
    toast.style.cssText = 'top: 20px; right: 20px; z-index: 1050; min-width: 250px;';
    toast.innerHTML = `
        <i class="fas fa-exclamation-triangle me-2"></i>${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    document.body.appendChild(toast);
    
    // 5秒后自动移除（错误信息显示时间稍长）
    setTimeout(() => {
        if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
        }
    }, 5000);
}

// 初始化Markdown视图控制
function initializeMarkdownViewControls() {
    // 绑定Markdown视图切换事件
    document.addEventListener('change', function(e) {
        if (e.target.name === 'markdown-view') {
            handleMarkdownViewSwitch(e.target.value);
        }
    });
}

// 处理Markdown视图切换
function handleMarkdownViewSwitch(viewType) {
    const textContent = document.querySelector('.text-content');
    const markdownPreview = document.querySelector('.markdown-preview');
    const markdownRawCol = document.querySelector('.markdown-raw-col');
    const markdownRenderedCol = document.querySelector('.markdown-rendered-col');
    
    if (!textContent || !markdownPreview) return;
    
    switch (viewType) {
        case 'raw':
            // 显示原始代码
            textContent.style.display = 'block';
            markdownPreview.style.display = 'none';
            break;
            
        case 'preview':
            // 显示预览
            textContent.style.display = 'none';
            markdownPreview.style.display = 'block';
            
            // 隐藏原始代码列，只显示预览
            if (markdownRawCol) markdownRawCol.style.display = 'none';
            if (markdownRenderedCol) {
                markdownRenderedCol.className = 'col-12';
                markdownRenderedCol.style.display = 'block';
            }
            
            renderMarkdownPreview();
            break;
            
        case 'split':
            // 并排显示
            textContent.style.display = 'none';
            markdownPreview.style.display = 'block';
            
            // 显示两列
            if (markdownRawCol) {
                markdownRawCol.className = 'col-md-6';
                markdownRawCol.style.display = 'block';
            }
            if (markdownRenderedCol) {
                markdownRenderedCol.className = 'col-md-6';
                markdownRenderedCol.style.display = 'block';
            }
            
            renderMarkdownPreview();
            break;
    }
}

// 渲染Markdown预览
function renderMarkdownPreview() {
    const resultText = document.getElementById('result-text');
    const markdownRaw = document.getElementById('markdown-raw');
    const markdownRendered = document.getElementById('markdown-rendered');
    
    if (!resultText || !markdownRendered) return;
    
    const markdownContent = resultText.value;
    
    // 更新原始代码显示
    if (markdownRaw) {
        markdownRaw.value = markdownContent;
    }
    
    // 简单的Markdown渲染（基础功能）
    const htmlContent = renderBasicMarkdown(markdownContent);
    markdownRendered.innerHTML = htmlContent;
}

// Markdown渲染器（优先使用marked库，否则使用基础渲染器）
function renderBasicMarkdown(markdown) {
    if (!markdown) return '';
    
    // 如果有marked库，使用它进行渲染
    if (typeof marked !== 'undefined') {
        try {
            return marked.parse(markdown);
        } catch (error) {
            console.warn('Marked.js rendering failed, falling back to basic renderer:', error);
        }
    }
    
    // 基础Markdown渲染器（备用方案）
    let html = markdown;
    
    // 转义HTML特殊字符
    html = html.replace(/&/g, '&amp;')
               .replace(/</g, '&lt;')
               .replace(/>/g, '&gt;');
    
    // 标题
    html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
    html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');
    html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>');
    
    // 粗体和斜体
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
    
    // 代码
    html = html.replace(/`(.*?)`/g, '<code>$1</code>');
    
    // 链接
    html = html.replace(/\[([^\]]+)\]\(([^\)]+)\)/g, '<a href="$2" target="_blank">$1</a>');
    
    // 无序列表
    html = html.replace(/^\- (.*$)/gim, '<li>$1</li>');
    html = html.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
    
    // 有序列表
    html = html.replace(/^\d+\. (.*$)/gim, '<li>$1</li>');
    
    // 段落
    html = html.replace(/\n\n/g, '</p><p>');
    html = '<p>' + html + '</p>';
    
    // 清理空段落
    html = html.replace(/<p><\/p>/g, '');
    html = html.replace(/<p>(<[uo]l>)/g, '$1');
    html = html.replace(/(<\/[uo]l>)<\/p>/g, '$1');
    
    // 换行
    html = html.replace(/\n/g, '<br>');
    
    return html;
}

function updateModelsInfo(modelsInfo) {
    const modelsInfoElement = document.getElementById('models-info');
    
    if (!modelsInfo || modelsInfo.length === 0) {
        modelsInfoElement.innerHTML = '<span class="badge bg-secondary">暂无模型</span>';
        return;
    }
    
    let html = '';
    let totalSize = 0;
    
    modelsInfo.forEach(model => {
        totalSize += model.size_mb || 0;
        const sizeText = model.size_mb > 0 ? `${model.size_mb}MB` : '未知';
        const currentBadge = model.is_current ? '<span class="badge bg-success ms-1" style="font-size: 0.6em;">当前</span>' : '';
        
        html += `
            <div class="mb-2">
                <div class="d-flex justify-content-between align-items-center">
                    <small class="text-muted">${model.name}${currentBadge}</small>
                    <span class="badge bg-primary">${model.version}</span>
                </div>
                <div class="d-flex justify-content-between align-items-center">
                    <small class="text-secondary">${model.type}</small>
                    <small class="text-info">${sizeText}</small>
                </div>
            </div>
        `;
    });
    
    // 添加总大小信息
    if (totalSize > 0) {
        html += `
            <div class="mt-2 pt-2 border-top">
                <div class="d-flex justify-content-between align-items-center">
                    <small class="fw-bold">总大小:</small>
                    <span class="badge bg-success">${totalSize.toFixed(2)}MB</span>
                </div>
            </div>
        `;
    }
    
    modelsInfoElement.innerHTML = html;
}

function showManualGuide() {
    alert('手动下载指南:\\n\\n1. 访问 PaddleOCR 官方网站\\n2. 下载中文模型文件\\n3. 解压到用户目录的 .paddleocr 文件夹\\n4. 重新初始化服务\\n\\n详细说明请查看项目文档。');
}
//
// 测试格式转换功能
function testFormatConversion() {
    if (!formatManager) {
        console.error('FormatManager not initialized');
        return;
    }
    
    const testText = `标题示例
这是一个段落。

另一个段落：
- 列表项1
- 列表项2
- 列表项3

1. 有序列表项1
2. 有序列表项2`;
    
    console.log('Testing format conversion with text:', testText);
    
    // 测试转换为Markdown
    formatManager.convertFormat(testText, 'markdown')
        .then(result => {
            console.log('Conversion result:', result);
            if (result.success) {
                console.log('Converted markdown:', result.data.content);
            } else {
                console.error('Conversion failed:', result.error);
            }
        })
        .catch(error => {
            console.error('Conversion error:', error);
        });
}

// 在开发环境中暴露测试函数
if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    window.testFormatConversion = testFormatConversion;
    window.formatManager = () => formatManager;
    window.downloadManager = () => downloadManager;
}
// 平衡括号 (添加开括号以修复语法检查