function clickleft(contentFile) {
    // 隱藏中間區塊
    document.querySelector('.middle').style.display = 'none';
    
    // 將右邊區塊佔滿中間和右邊
    const rightSide = document.querySelector('.right-side');
    rightSide.style.width = '100%';

    // 使用 Fetch API 載入外部文字檔
    fetch(`static/text/${contentFile}.txt`)
        .then(response => response.text())
        .then(data => {
            rightSide.innerHTML = `<h2>${contentFile}</h2><p>${data}</p>`;
        })
        .catch(error => {
            console.error('Error loading content:', error);
        });
}