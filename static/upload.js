let selectedFiles = new Map(); // 存储选中的文件

// 使用服务器传递的设置
const MAX_UPLOAD_SIZE = SERVER_SETTINGS.maxUploadSize;

document.addEventListener('DOMContentLoaded', () => {
    const uploadArea = document.getElementById('upload-area');
    const fileInput = document.getElementById('file-input');
    const fileList = document.getElementById('file-list');
    const uploadBtn = document.getElementById('upload-btn');
    const userSelect = document.getElementById('user-select');

    // 拖放处理
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        handleFiles(e.dataTransfer.files);
    });

    // 点击上传区域触发文件选择
    uploadArea.addEventListener('click', () => {
        fileInput.click();
    });

    // 文件选择处理
    fileInput.addEventListener('change', (e) => {
        handleFiles(e.target.files);
    });

    // 用户选择处理
    userSelect.addEventListener('change', () => {
        uploadBtn.disabled = userSelect.value === '' || selectedFiles.size === 0;
    });

    // 上传按钮处理
    uploadBtn.addEventListener('click', uploadFiles);

    function handleFiles(files) {
        Array.from(files).forEach(file => {
            // 检查文件类型
            if (!file.type.startsWith('image/')) {
                alert('请只上传图片文件');
                return;
            }

            // 检查文件大小
            if (file.size > MAX_UPLOAD_SIZE) {
                alert(`文件大小不能超过${formatFileSize(MAX_UPLOAD_SIZE)}`);
                return;
            }

            const fileId = Date.now() + '-' + file.name;
            selectedFiles.set(fileId, file);

            // 创建预览元素
            const fileItem = document.createElement('div');
            fileItem.className = 'file-item';
            fileItem.innerHTML = `
                <img class="preview" src="${URL.createObjectURL(file)}" alt="${file.name}">
                <div class="info">
                    <div>${file.name}</div>
                    <div>${formatFileSize(file.size)}</div>
                    <div class="progress-bar"><div class="progress"></div></div>
                </div>
                <span class="remove" data-id="${fileId}">×</span>
            `;

            fileList.appendChild(fileItem);
        });

        uploadBtn.disabled = userSelect.value === '' || selectedFiles.size === 0;
    }

    // 删除文件处理
    fileList.addEventListener('click', (e) => {
        if (e.target.classList.contains('remove')) {
            const fileId = e.target.dataset.id;
            selectedFiles.delete(fileId);
            e.target.closest('.file-item').remove();
            uploadBtn.disabled = userSelect.value === '' || selectedFiles.size === 0;
        }
    });

    async function uploadFiles() {
        const username = userSelect.value;
        if (!username) {
            alert('请选择用户');
            return;
        }

        uploadBtn.disabled = true;
        let successCount = 0;
        let failCount = 0;

        for (const [fileId, file] of selectedFiles) {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('username', username);

            const fileItem = document.querySelector(`[data-id="${fileId}"]`).closest('.file-item');
            const progressBar = fileItem.querySelector('.progress');

            try {
                const response = await fetch('/upload_image', {
                    method: 'POST',
                    body: formData
                });

                const result = await response.json();

                if (result.success) {
                    progressBar.style.width = '100%';
                    progressBar.style.backgroundColor = '#4CAF50';
                    successCount++;
                } else {
                    progressBar.style.backgroundColor = '#f44336';
                    failCount++;
                }
            } catch (error) {
                console.error('Upload error:', error);
                progressBar.style.backgroundColor = '#f44336';
                failCount++;
            }
        }

        alert(`上传完成\n成功：${successCount}个\n失败：${failCount}个`);
        
        if (successCount > 0) {
            // 清空文件列表
            selectedFiles.clear();
            fileList.innerHTML = '';
            uploadBtn.disabled = true;
        }
    }
});

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
} 