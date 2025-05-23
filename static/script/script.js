let accessToken = null;

// 登入邏輯

document.getElementById('login-button').addEventListener('click', () => {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
 
    if (!username || !password) {
        alert("請輸入帳號和密碼！");
        return;
    }

    fetch('http://127.0.0.1:5000/api/login', {
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

// 加載學生列表
function loadStudents() {
    fetch('http://127.0.0.1:5000/api/students', {
        headers: { Authorization: `Bearer ${accessToken}` }
    })
    .then(response => response.json())
    .then(data => {
        const studentsDiv = document.getElementById('students');
        studentsDiv.innerHTML = ''; // 清空內容
        data.forEach(student => {
            const studentDiv = document.createElement('div');
            studentDiv.innerHTML = `
                <label>
                    <input type="checkbox" id="${student.sno}" />
                    ${student.name} (${student.class})
                </label>
            `;
            studentsDiv.appendChild(studentDiv);
        });
    })
    .catch(error => console.error('Error loading students:', error));
}

// 保存點名結果
document.getElementById('saveAttendance').addEventListener('click', () => {
    const attendance = [];
    const checkboxes = document.querySelectorAll('input[type="checkbox"]');
    checkboxes.forEach(checkbox => {
        attendance.push({
            sno: checkbox.id,
            date: new Date().toISOString().split('T')[0],
            status: checkbox.checked ? 'present' : 'absent'
        });
    });

    fetch('http://127.0.0.1:5000/api/attendance', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${accessToken}`
        },
        body: JSON.stringify(attendance)
    })
    .then(response => response.json())
    .then(data => alert(data.message))
    .catch(error => console.error('Error saving attendance:', error));
});
