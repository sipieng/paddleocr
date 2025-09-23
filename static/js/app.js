let ocrReady = false;
let checkInterval;

// 页面加载完成后开始检查状态
document.addEventListener('DOMContentLoaded', function() {
    console.log('页面加载完成，开始检查系统状态');
    checkSystemStatus();
});

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
    
    // 滚动到结果区域
    resultArea.scrollIntoView({ behavior: 'smooth' });
}

function copyResult() {
    const resultText = document.getElementById('result-text');
    resultText.select();
    document.execCommand('copy');
    alert('结果已复制到剪贴板');
}

function showManualGuide() {
    alert('手动下载指南:\\n\\n1. 访问 PaddleOCR 官方网站\\n2. 下载中文模型文件\\n3. 解压到用户目录的 .paddleocr 文件夹\\n4. 重新初始化服务\\n\\n详细说明请查看项目文档。');
}