let currentRotation = 0;
let isDragging = false;
let startX, startY, scrollLeft, scrollTop;
let currentRotationIndex = 0;
const rotationAngles = [0, 270, 180, 90, 0];

function viewImage(user, image) {
    console.log("查看图片: " + user + "/" + image);
    document.getElementById('fullscreen-view').style.display = 'flex';
    const imgElement = document.getElementById('fullscreen-image');
    imgElement.src = '/image/' + user + '/' + image;
    imgElement.style.transform = `rotate(${rotationAngles[currentRotationIndex]}deg)`;

    // 确保移除所有拖拽相关的事件
    imgElement.onmousedown = null;
    imgElement.onmousemove = null;
    imgElement.onmouseup = null;
    imgElement.ondragstart = function() { return false; }; // 禁用拖拽


    imgElement.onload = function() {
        const container = document.getElementById('fullscreen-view');
        const containerAspectRatio = container.clientWidth / container.clientHeight;
        const imageAspectRatio = imgElement.naturalWidth / imgElement.naturalHeight;

        if (containerAspectRatio > imageAspectRatio) {
            imgElement.style.width = 'auto';
            imgElement.style.height = '100%';
        } else {
            imgElement.style.width = '100%';
            imgElement.style.height = 'auto';
        }
    };

}

function closeFullscreen(event) {
    event.stopPropagation();
    if (event.target.id === 'fullscreen-view' || event.target.closest('.back-btn')) {
        console.log("关闭全屏查看");
        document.getElementById('fullscreen-view').style.display = 'none';
    }
}

function closeFullscreenDirectly() {
    console.log("直接关闭全屏查看");
    document.getElementById('fullscreen-view').style.display = 'none';
}

function toggleInfo(event) {
    event.stopPropagation();
    const infoBar = document.getElementById('info-bar');
    const menuBtn = document.querySelector('.menu-btn');
    if (infoBar.style.display === 'none') {
        infoBar.style.display = 'block';
        menuBtn.style.display = 'none';
    } else {
        infoBar.style.display = 'none';
        menuBtn.style.display = 'block';
    }
}

function downloadSelected() {
    const zip = new JSZip();
    const checkboxes = document.querySelectorAll('.select-checkbox:checked');
    const promises = [];

    checkboxes.forEach(checkbox => {
        const filename = checkbox.getAttribute('data-filename');
        const user = checkbox.getAttribute('data-user');
        const url = '/image/' + user + '/' + filename;
        promises.push(
            fetch(url)
                .then(response => response.blob())
                .then(blob => {
                    zip.file(filename, blob);
                })
        );
    });

    Promise.all(promises).then(() => {
        zip.generateAsync({ type: 'blob' }).then(content => {
            saveAs(content, 'images.zip');
        });
    });
}

function updateNavbar() {
    const selectedCount = document.querySelectorAll('.select-checkbox:checked').length;
    const navbarInfo = document.getElementById('navbar-info');
    const navbarActions = document.getElementById('navbar-actions');
    if (navbarInfo && navbarActions) {
        if (selectedCount > 0) {
            navbarInfo.textContent = `已选择 ${selectedCount} 张图片`;
        } else {
            navbarInfo.textContent = '图片浏览器';
        }
        navbarActions.style.display = 'flex';
    }
}

function clearSelection() {
    document.querySelectorAll('.select-checkbox:checked').forEach(checkbox => {
        checkbox.checked = false;
        toggleImageSize(checkbox);
    });
    updateNavbar();
}

function invertSelection() {
    document.querySelectorAll('.select-checkbox').forEach(checkbox => {
        checkbox.checked = !checkbox.checked;
        toggleImageSize(checkbox);
    });
    updateNavbar();
}

function toggleImageSize(checkbox) {
    const image = checkbox.nextElementSibling;
    image.style.transition = 'transform 0.2s ease-in-out';
    if (checkbox.checked) {
        image.style.transform = 'scale(0.85)';
    } else {
        image.style.transform = 'scale(1)';
    }
}

function showDownloadOptions() {
    document.getElementById('download-options').style.display = 'block';
}

function closeDownloadOptions() {
    document.getElementById('download-options').style.display = 'none';
}

function downloadAsZip() {
    const zip = new JSZip();
    const checkboxes = document.querySelectorAll('.select-checkbox:checked');
    const promises = [];

    checkboxes.forEach(checkbox => {
        const filename = checkbox.getAttribute('data-filename');
        const user = checkbox.getAttribute('data-user');
        const url = '/image/' + user + '/' + filename;
        promises.push(
            fetch(url)
                .then(response => response.blob())
                .then(blob => {
                    zip.file(filename, blob);
                })
        );
    });

    Promise.all(promises).then(() => {
        zip.generateAsync({ type: 'blob' }).then(content => {
            saveAs(content, 'images.zip');
            closeDownloadOptions();
        });
    });
}

function downloadIndividually() {
    const checkboxes = document.querySelectorAll('.select-checkbox:checked');
    checkboxes.forEach(checkbox => {
        const filename = checkbox.getAttribute('data-filename');
        const user = checkbox.getAttribute('data-user');
        const url = '/image/' + user + '/' + filename;
        fetch(url)
            .then(response => response.blob())
            .then(blob => {
                saveAs(blob, filename);
            });
    });
}

function selectAll() {
    document.querySelectorAll('.select-checkbox').forEach(checkbox => {
        checkbox.checked = true;
        toggleImageSize(checkbox);
    });
    updateNavbar();
}

function closeOnClickOutside(event) {
    if (event.target.id === 'fullscreen-view') {
        console.log("点击空白区域关闭全屏查看");
        document.getElementById('fullscreen-view').style.display = 'none';
    }
} 