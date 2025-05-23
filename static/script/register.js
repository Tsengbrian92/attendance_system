// 讀卡按鈕事件
document.getElementById('read-card-button').addEventListener('click', async () => {
    const statusDisplay = document.getElementById('card-status');
    statusDisplay.textContent = "等待刷卡中...";
    statusDisplay.style.color = "black";

    try {
        const response = await fetch('http://127.0.0.1:5000/get_card_num');
        const data = await response.json();
        if (data.status === "success") {
            document.getElementById('card-num').value = data.card_num;
            statusDisplay.textContent = "讀卡成功，卡號：" + data.card_num;
            statusDisplay.style.color = "green";
        } else {
            statusDisplay.textContent = "讀卡失敗：" + data.message;
            statusDisplay.style.color = "red";
        }
    } catch (err) {
        statusDisplay.textContent = "伺服器錯誤，無法取得卡號";
        statusDisplay.style.color = "red";
        console.error(err);
    }
});

// 創建帳號事件
document.getElementById('create-account-button').addEventListener('click', () => {
    const newUsername = document.getElementById('new-username').value;
    const newPassword = document.getElementById('new-password').value;
    const checkPassword = document.getElementById('check-password').value;
    const name = document.getElementById('name').value;
    const email = document.getElementById('email').value;
    const phone = document.getElementById('phone').value;
    const cardNum = document.getElementById('card-num').value;

    if (!newUsername || !newPassword || !name || !email || !phone || !checkPassword || !cardNum) {
        alert("請輸入所有必填資訊，包含卡號！");
        return;
    }

    if (newPassword !== checkPassword) {
        alert("密碼第一次輸入和第二次不一樣");
        return;
    }

    const emailRegex = /^[a-zA-Z0-9._%+-]+@gmail\.com$/;
    if (!emailRegex.test(email)) {
        alert("請輸入正確的 Gmail 地址！");
        return;
    }

    fetch('http://127.0.0.1:5000/api/register', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            username: newUsername,
            password: newPassword,
            name: name,
            email: email,
            phone: phone,
            card_num: cardNum
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.message === '帳號創建成功') {
            alert("帳號創建成功！");
            window.location.href = 'home.html';
        } else {
            alert(data.message || "帳號創建失敗！");
        }
    })
    .catch(error => {
        alert("發生錯誤：" + error);
        console.error('創建帳號錯誤：', error);
    });
});