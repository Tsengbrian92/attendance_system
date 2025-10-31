// 創建帳號事件
document.getElementById('create-account-button').addEventListener('click', () => {
    const newUsername = document.getElementById('new-username').value;
    const newPassword = document.getElementById('new-password').value;
    const checkPassword = document.getElementById('check-password').value;
    const name = document.getElementById('name').value;
    const email = document.getElementById('email').value;
    const phone = document.getElementById('phone').value;

    if (!newUsername || !newPassword || !name || !email || !phone || !checkPassword ) {
        alert("請輸入所有必填資訊");
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

    fetch('http://26.218.4.126:5000/api/teacher/register', {
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