async function verifyToken() {
    const accessToken = localStorage.getItem('teacher_access_token'); // 從 localStorage 獲取 Token
    if (!accessToken) {
        handleUnauthenticated('未檢測到登入資訊，請先登入！');
        return false;
    }
    
    try {
        // 向後端驗證 Token 是否有效
        const response = await fetch('http://127.0.0.1:5000/api/teacher/verify', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${accessToken}`
            }
        
        });
        
        if (response.ok) {
            const data = await response.json();
            return true; // 驗證成功
        } else {
            handleUnauthenticated('登入已過期或無效，請重新登入！');
            return false; // 驗證失敗
        }
    } catch (error) {
        console.error('驗證 Token 時出現錯誤：', error);
        handleUnauthenticated('無法驗證登入狀態，請稍後重試！');
        return false; // 驗證失敗
    }
}

// 未授權處理邏輯
function handleUnauthenticated(message) {
    alert(message);
    localStorage.removeItem('access_token'); // 清除本地 Token
    window.location.href = 'login.html'; // 跳轉到登入頁面
}

window.onload = () => {
    verifyToken()
};