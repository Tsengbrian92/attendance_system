
document.getElementById('change-password-btn').addEventListener('click', async () => {
    console.log('button clicked');
    const params = new URLSearchParams(location.search);
    const studentId = params.get('studentId');
    const oldPwd = document.getElementById('old-password').value;
    const newPwd = document.getElementById('new-password').value;
    const checkPwd = document.getElementById('check-password').value;
    const msg = document.getElementById('change-msg');

    if (!oldPwd || !newPwd || !checkPwd) {
        msg.textContent = '請輸入所有欄位';
        msg.style.color = 'red';
        return;
    }
    if (newPwd !== checkPwd) {
        msg.textContent = '兩次新密碼不一致';
        msg.style.color = 'red';
        return;
    }

    const token = localStorage.getItem('access_token');
    const res = await fetch('http://26.218.4.126:5000/api/change_password', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + token
        },
        body: JSON.stringify({
            old_password: oldPwd,
            new_password: newPwd
        })
    });
    const data = await res.json();
    if (res.ok) {
        msg.textContent = data.message;
        msg.style.color = 'green';
        setTimeout(() => {
            window.location.href = 'home.html';  // 換成你要跳轉的網址
        }, 1000);
        // 你也可以跳回登入頁
    } else {
        msg.textContent = data.message;
        msg.style.color = 'red';
    }
});
