// 獲取 URL 中的 classId 參數
function getClassIdFromUrl() {
    const params = new URLSearchParams(window.location.search);
    return params.get('classId');
}

// 獲取班級資訊並顯示在頁面中
async function fetchClassInfo() {
    const classId = getClassIdFromUrl();

    if (!classId) {
        alert("無法獲取班級代碼");
        return;
    }

    try {
        const response = await fetch(`http://127.0.0.1:5000/api/get-class-info?classId=${classId}`);
        if (!response.ok) {
            throw new Error("無法獲取班級資訊");
            
        }

        const data = await response.json();

        const startDate = new Date(data.start_date).toISOString().split('T')[0];
        const endDate = new Date(data.end_date).toISOString().split('T')[0];
                
        // 更新頁面內容
        document.getElementById('class-name').innerText = data.class_name;
        document.getElementById('teacher-name').innerText = data.teacher_name;
        document.getElementById('start-date').innerText = startDate;
        document.getElementById('end-date').innerText = endDate;
        document.getElementById('students-count').innerText = data.students_count;
        document.getElementById('max-students').innerText = data.max_students;
    } catch (error) {
        alert(error.message);
    }
}
// 獲取 URL 中的 classId 參數


// 獲取學生清單並顯示在頁面中
async function fetchStudents() {
    const classId = getClassIdFromUrl();

    if (!classId) {
        alert("無法獲取班級代碼");
        return;
    }

    try {
        const response = await fetch(`http://127.0.0.1:5000/api/get-students?classId=${classId}`);
        if (!response.ok) {
            throw new Error("無法獲取學生清單");
        }

        const data = await response.json();

        const studentList = document.getElementById('student-list');

        // 清空清單
        studentList.innerHTML = '';

        if (data.students.length === 0) {
            const noStudentMsg = document.createElement('p');
            noStudentMsg.innerText = "目前無學生";
            studentList.appendChild(noStudentMsg);
        } else {
            data.students.forEach((student) => {
                const studentItem = document.createElement('li');
                studentItem.innerText = `學號: ${student.student_id} 姓名: ${student.student_name}`;
                studentList.appendChild(studentItem);
            });
        }
    } catch (error) {
        alert(error.message);
    }
}

// 網頁載入後執行
window.onload = () => {
    fetchClassInfo();
    fetchStudents();
};





function editStudents() {
    const classId = new URLSearchParams(window.location.search).get('classId');
    window.location.href = `edit_class_student.html?classId=${classId}`;
}


function deleteClass() {
    if (confirm('確定刪除這個班級嗎？')) {
        alert('班級已刪除');
        // 可呼叫後端 API 刪除班級
    }
}

function goBack() {
    window.location.href = 'class_info.html';
}
