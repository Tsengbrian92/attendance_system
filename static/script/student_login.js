let accessToken = null;

// 登入邏輯

document.getElementById('login-button').addEventListener('click', () => {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
 
    if (!username || !password) {
        alert("請輸入帳號和密碼！");
        return;
    }

    fetch('http://26.8.220.101:5000/api/t_login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('點名失敗，請檢查帳號或密碼');
        }
        return response.json();
    })
    .then(data => {
        accessToken = data.access_token;
        alert('點名成功！');
        document.getElementById('login-page').style.display = 'none';
        document.getElementById('attendance-page').style.display = 'block';
        loadStudents();
    })
    .catch(error => alert(error.message));
});