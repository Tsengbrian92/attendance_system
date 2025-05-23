let accessToken = null; // 儲存 JWT Token

// 登入邏輯
async function teacherLogin() {
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value.trim();

    if (!username || !password) {
        alert("請輸入帳號和密碼！");
        return;
    }

    const loginButton = document.getElementById('login-button');
    loginButton.innerText = '登入中...';
    loginButton.disabled = true;

    try {
        const response = await fetch('http://127.0.0.1:5000/api/t_login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || '請檢查帳號或密碼');
        }

        const data = await response.json();
        if (!data.access_token) {
            throw new Error('後端未返回有效的 Token');
        }

        accessToken = data.access_token; // 儲存 Token 到變數
        localStorage.setItem('teacher_access_token', accessToken); // 儲存 Token 到 localStorage

        alert('成功登錄！');
        window.location.href = 'home.html'; // 跳轉到首頁

    } catch (error) {
        console.error('登入失敗:', error);
        alert(error.message);
    } finally {
        loginButton.innerText = '登入';
        loginButton.disabled = false;
    }
}

// 綁定登入按鈕的點擊事件
document.getElementById('login-button').addEventListener('click', teacherLogin);

// 支持按下 Enter 鍵登入
document.getElementById('password').addEventListener('keypress', (event) => {
    if (event.key === 'Enter') {
        teacherLogin();
    }
});