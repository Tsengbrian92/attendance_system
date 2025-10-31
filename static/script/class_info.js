// 從後端獲取班級列表
async function fetchClassList() {
    const urlParams = new URLSearchParams(window.location.search);
    const teacherId = urlParams.get("teacherId");
    if (!teacherId) {
        alert("找不到教師帳號資訊，請重新登入");
        return;
    }
    
    try {
        const response = await fetch(`http://26.218.4.126:5000/api/get-classes?teacherId=${teacherId}`); // 替換為後端 API 的 URL
        if (!response.ok) {
            throw new Error("無法獲取班級資料，請稍後再試！");
        }
        const classes = await response.json();
        renderClassList(classes);
    } catch (error) {
        console.error(error);
        alert(error.message);
    }
}

// 動態渲染班級列表
function renderClassList(classes) {
    const classListContainer = document.getElementById("class-list");
    classListContainer.innerHTML = ""; // 清空列表

    classes.forEach((cls) => {
        const classCard = document.createElement("div");
        classCard.classList.add("class-card");

        classCard.innerHTML = `
            <h3>${cls.name}</h3>
            <p>教師: ${cls.teacher}</p>
            <p>學生人數: ${cls.students}</p>
            <div class="card-actions">
                <button class="add-student" onclick="navigateToAddStudent('${cls.id}')">查看詳情</button>
            </div>
        `;

        classListContainer.appendChild(classCard);
    });
}


// 跳轉到查看詳情
function navigateToAddStudent(classId) {
    const username = getStudentIdFromUrl();
    window.location.href = `solo_class_info.html?classId=${classId}&teacherId=${username}`; // 替換為後端對應頁面的 URL
}

document.getElementById('back_home').addEventListener('click', async () => {
    const username = getStudentIdFromUrl();
    window.location.href = `home.html?teacherId=${username}`;
});

document.getElementById('add-class-button').addEventListener('click', async () => {
    const username = getStudentIdFromUrl();
    window.location.href = `createclass.html?teacherId=${username}`;
});

// 初始化頁面
fetchClassList();
