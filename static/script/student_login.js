let accessToken = null;

// 登入邏輯

document.getElementById('login-button').addEventListener('click', () => {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
 
    if (!username || !password) {
        alert("請輸入帳號和密碼！");
        return;
    }

    fetch('http://26.218.4.126:5000/api/s_login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('登入失敗，請檢查帳號或密碼');
        }
        return response.json();
    })
    .then(data => {
        accessToken = data.access_token;
        localStorage.setItem('access_token', data.access_token);
        alert('登入成功！');
        window.location.href = `home.html?studentId=${username}`;
    })

    .catch(error => alert(error.message));
});

document.getElementById('register-button').addEventListener('click', () => {
    window.location.href = 'register.html';
});

 