document.addEventListener('DOMContentLoaded', function() { 
    setupNavLinks();
})
function setupNavLinks(){
    const navLinks = document.querySelectorAll('nav a');

    navLinks.forEach(link => {
        link.addEventListener('click', function(event) {
            event.preventDefault(); // 防止頁面跳轉

            if (this.id === 'home-button') {
                // 回到主畫面的按鈕邏輯
                resetToHome();
            } else {
                const content = this.getAttribute('data-content'); // 獲取data-content屬性
                clicknav1(content); // 更新section的內容
            }
        });
    });
}

function clicknav1(contentFile) {
    // 隱藏左邊和中間的區塊
    document.querySelector('.left-side').style.display = 'none';
    document.querySelector('.middle').style.display = 'none';
    document.querySelector('.image-container').style.display = 'none';
    
    // 讓右邊的區塊佔滿整個頁面
    const rightSide = document.getElementById('right-side-content');
    rightSide.className = 'nav1sec';

    // 使用 Fetch API 載入外部文字檔
    fetch(`static/text/${contentFile}.txt`)
        .then(response => response.text())
        .then(data => {
            rightSide.innerHTML = `
                <div class='nav1sec'>
                    <h2>${contentFile}</h2>
                    <div class='nav1box'>
                        <p>${data}</p>
                    </div>
                </div>`;
        })
        .catch(error => {
            console.error('Error loading content:', error);
        });
}

function reinitialize() {
    // 重新綁定事件處理程序或其他初始化操作
    setupNavLinks();
}

function resetToHome() {
    // 顯示左邊和中間的區塊
    document.querySelector('.left-side').style.display = 'flex';
    document.querySelector('.middle').style.display = 'flex';
    document.querySelector('.image-container').style.display = 'block';

    // 重置右側區域的內容和樣式
    const rightSide = document.getElementById('right-side-content');
    rightSide.className = 'right-side'; // 恢復原始class
    rightSide.innerHTML = `
        <div class='right-image'></div>`;
}