// 宠物丢失网站前端交互脚本

// 图片上传预览功能
function setupImagePreview() {
    const fileInputs = document.querySelectorAll('input[type="file"][multiple]');
    
    fileInputs.forEach(input => {
        // 移除已有的事件监听器，避免重复绑定
        input.removeEventListener('change', handleImagePreview);
        input.addEventListener('change', handleImagePreview);
    });
}

// 图片预览处理函数
function handleImagePreview(e) {
    const files = e.target.files;
    const previewContainer = document.getElementById('image-preview');
    
    if (!previewContainer) return;
    
    // 清空之前的预览
    previewContainer.innerHTML = '';
    
    // 限制最多9张图片
    const maxFiles = Math.min(files.length, 9);
    
    for (let i = 0; i < maxFiles; i++) {
        const file = files[i];
        
        if (file.type.startsWith('image/')) {
            const reader = new FileReader();
            
            reader.onload = function(e) {
                const imageDiv = document.createElement('div');
                imageDiv.className = 'image-item';
                imageDiv.innerHTML = `
                    <img src="${e.target.result}" alt="预览图片">
                    <button type="button" class="remove-image" onclick="removeImage(this)">&times;</button>
                `;
                previewContainer.appendChild(imageDiv);
            };
            
            reader.readAsDataURL(file);
        }
    }
    
    // 如果选择了超过9张图片，显示警告
    if (files.length > 9) {
        showAlert('最多只能上传9张图片，已自动选择前9张', 'warning');
    }
}

// 移除图片预览
function removeImage(button) {
    const imageItem = button.parentElement;
    imageItem.remove();
}

// 显示提示消息
function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.textContent = message;
    
    const container = document.querySelector('.container');
    container.insertBefore(alertDiv, container.firstChild);
    
    // 3秒后自动消失
    setTimeout(() => {
        alertDiv.remove();
    }, 3000);
}

// 表单验证
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return true;
    
    const requiredFields = form.querySelectorAll('[required]');
    let isValid = true;
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            field.style.borderColor = '#e74c3c';
            isValid = false;
        } else {
            field.style.borderColor = '#ddd';
        }
    });
    
    if (!isValid) {
        showAlert('请填写所有必填字段', 'danger');
    }
    
    return isValid;
}

// 图片懒加载
function setupLazyLoading() {
    const images = document.querySelectorAll('img[data-src]');
    
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.removeAttribute('data-src');
                observer.unobserve(img);
            }
        });
    });
    
    images.forEach(img => imageObserver.observe(img));
}

// 搜索功能
function setupSearch() {
    const searchInput = document.getElementById('search-input');
    if (!searchInput) return;
    
    searchInput.addEventListener('input', function(e) {
        const searchTerm = e.target.value.toLowerCase();
        const posts = document.querySelectorAll('.post-card');
        
        posts.forEach(post => {
            const title = post.querySelector('.post-title').textContent.toLowerCase();
            const description = post.querySelector('.post-description').textContent.toLowerCase();
            
            if (title.includes(searchTerm) || description.includes(searchTerm)) {
                post.style.display = 'block';
            } else {
                post.style.display = 'none';
            }
        });
    });
}

// 评论功能
function setupComments() {
    const commentForms = document.querySelectorAll('.comment-form');
    
    commentForms.forEach(form => {
        // 移除已有的事件监听器，避免重复绑定
        form.removeEventListener('submit', handleCommentSubmit);
        form.addEventListener('submit', handleCommentSubmit);
    });
}

// 评论提交处理函数
function handleCommentSubmit(e) {
    e.preventDefault();
    
    const form = e.target;
    const submitButton = form.querySelector('button[type="submit"]');
    
    // 防止重复提交
    if (submitButton.disabled) return;
    submitButton.disabled = true;
    submitButton.textContent = '提交中...';
    
    const formData = new FormData(form);
    const postId = form.dataset.postId;
    
    fetch(`/add_comment/${postId}`, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            location.reload(); // 简单的重新加载页面
        } else {
            showAlert(data.message || '评论发布失败', 'danger');
            // 恢复按钮状态
            submitButton.disabled = false;
            submitButton.textContent = '发表评论';
        }
    })
    .catch(error => {
        showAlert('网络错误，请稍后重试', 'danger');
        // 恢复按钮状态
        submitButton.disabled = false;
        submitButton.textContent = '发表评论';
    });
}

// 图片点击放大
function setupImageModal() {
    const images = document.querySelectorAll('.post-images img, .comment img');
    
    images.forEach(img => {
        // 移除已有的事件监听器，避免重复绑定
        img.removeEventListener('click', handleImageClick);
        img.addEventListener('click', handleImageClick);
    });
}

// 图片点击处理函数
function handleImageClick(e) {
    const modal = document.createElement('div');
    modal.className = 'image-modal';
    modal.innerHTML = `
        <div class="modal-backdrop" onclick="closeModal(this)">
            <div class="modal-content">
                <img src="${e.target.src}" alt="放大图片">
                <button class="close-btn" onclick="closeModal(this)">&times;</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    document.body.style.overflow = 'hidden';
}

// 关闭模态框
function closeModal(element) {
    const modal = element.closest('.image-modal');
    if (modal) {
        modal.remove();
        document.body.style.overflow = 'auto';
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    setupImagePreview();
    setupLazyLoading();
    setupSearch();
    setupComments();
    setupImageModal();
    
    // 自动隐藏flash消息
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 300);
        }, 5000);
    });
});

// 添加图片模态框样式
const modalStyles = `
.image-modal {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    z-index: 1000;
}

.modal-backdrop {
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.8);
    display: flex;
    justify-content: center;
    align-items: center;
    cursor: pointer;
}

.modal-content {
    position: relative;
    max-width: 90%;
    max-height: 90%;
    cursor: default;
}

.modal-content img {
    width: 100%;
    height: 100%;
    object-fit: contain;
    border-radius: 8px;
}

.close-btn {
    position: absolute;
    top: -40px;
    right: 0;
    background: rgba(255, 255, 255, 0.8);
    border: none;
    width: 30px;
    height: 30px;
    border-radius: 50%;
    cursor: pointer;
    font-size: 18px;
    font-weight: bold;
}
`;

// 动态添加样式
const styleSheet = document.createElement('style');
styleSheet.textContent = modalStyles;
document.head.appendChild(styleSheet);