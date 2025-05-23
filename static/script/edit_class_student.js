let classStudentsData = [];
let nonClassStudentsData = [];
let addedStudents = []; // 儲存待加入的學生
let removedStudents = []; // 儲存待刪除的學生

async function fetchStudents() {
    const classCode = new URLSearchParams(window.location.search).get('classId');

    try {
        // 獲取班級學生
        const classResponse = await fetch(`http://127.0.0.1:5000/api/get-class-students?class_code=${classCode}`);
        const classStudents = await classResponse.json();
        classStudentsData = classStudents;
        renderclassStudents('class-students-list', classStudents);

        // 獲取不在班級的學生
        const nonClassResponse = await fetch(`http://127.0.0.1:5000/api/get-non-class-students?class_code=${classCode}`);
        const nonClassStudents = await nonClassResponse.json();
        nonClassStudentsData = nonClassStudents;
        renderStudents('non-class-students-list', nonClassStudents);
    } catch (error) {
        alert('無法加載學生數據');
    }
}

function renderStudents(listId, students) {
    const listElement = document.getElementById(listId);
    listElement.innerHTML = '';

    if (students.length === 0) {
        listElement.innerHTML = '<li>目前無學生</li>';
        return;
    }

    students.forEach(student => {
        const li = document.createElement('li');
        li.textContent = `${student.student_id} - ${student.name}`;
        li.dataset.studentId = student.student_id;

        const addButton = document.createElement('button');
        addButton.textContent = '加入';
        addButton.onclick = () => addToClass(student.student_id, student.name, student.email, student.phone);
        addButton.id = 'addButton';
        li.appendChild(addButton);

        listElement.appendChild(li);
    });
}

function renderclassStudents(listId, students) {
    const listElement = document.getElementById(listId);
    listElement.innerHTML = '';

    if (students.length === 0) {
        listElement.innerHTML = '<li>目前無學生</li>';
        return;
    }

    students.forEach(student => {
        const li = document.createElement('li');
        li.textContent = `${student.student_id} - ${student.student_name}`;
        li.dataset.studentId = student.student_id;

        const removeButton = document.createElement('button');
        removeButton.textContent = '移除';
        removeButton.onclick = () => removeFromClass(student.student_id, student.student_name, student.student_email, student.student_phone);
        removeButton.id = 'removeButton';
        li.appendChild(removeButton);

        listElement.appendChild(li);
    });
}

async function addToClass(studentId, studentName, studentEmail, studentPhone) {
    const existingStudent = addedStudents.find(student => student.username === studentId);
    const classCode = new URLSearchParams(window.location.search).get('classId');

    if (existingStudent) {
        alert("該學生已經在待加入列表中！");
        return;
    }

    try {
        const response = await fetch(`http://127.0.0.1:5000/api/get-max-students?classId=${classCode}`);
        if (!response.ok) throw new Error("無法獲取班級最大學生數");

        const data = await response.json();
        const maxStudents = data.max_students;

        if (classStudentsData.length >= maxStudents) {
            alert(`班級最多可收學生數：${maxStudents}，已經達到上限`);
            return;
        }
    } catch (error) {
        console.error("發生錯誤：", error);
        alert(error.message);
        return;
    }

    // 新增學生到待加入陣列
    addedStudents.push({ username: studentId, name: studentName, email: studentEmail, phone: studentPhone });

    // **插入到班級學生清單最前面**
    classStudentsData.unshift({
        student_id: studentId,
        student_name: studentName,
        student_email: studentEmail,
        student_phone: studentPhone
    });

    // **從非班級學生清單移除**
    removeStudentFromList(studentId, nonClassStudentsData);

    console.log("待儲存學生資料：", addedStudents);
    renderclassStudents('class-students-list', classStudentsData);
    renderStudents('non-class-students-list', nonClassStudentsData);
}

async function removeFromClass(studentId, studentName, studentEmail, studentPhone) {
    const existingStudent = removedStudents.find(student => student.username === studentId);
    if (existingStudent) {
        alert("該學生已經在待刪除列表中！");
        return;
    }

    // **檢查學生是否在班級學生資料**
    const student = classStudentsData.find(s => s.student_id === studentId);
    if (!student) return;

    // **加入待刪除陣列**
    removedStudents.push(student);

    // **插入到非班級學生清單最前面**
    nonClassStudentsData.unshift({
        student_id: studentId,
        student_name: studentName,
        student_email: studentEmail,
        student_phone: studentPhone
    });

    // **從班級學生名單中移除**
    removeStudentFromList(studentId, classStudentsData);

    console.log("待刪除學生資料：", removedStudents);
    renderclassStudents('class-students-list', classStudentsData);
    renderStudents('non-class-students-list', nonClassStudentsData);
}

async function saveChanges() {
    const classCode = new URLSearchParams(window.location.search).get('classId');

    if (addedStudents.length === 0 && removedStudents.length === 0) {
        alert("目前無待儲存的變更！");
        return;
    }

    try {
        const response = await fetch(`http://127.0.0.1:5000/api/update-class-students`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ classCode, addedStudents, removedStudents })
        });

        if (response.ok) {
            alert("儲存成功！");
            addedStudents = [];
            removedStudents = [];
            window.location.href = `solo_class_info.html?classId=${classCode}`;
        } else {
            const errorData = await response.json();
            alert(`儲存失敗: ${errorData.message}`);
        }
    } catch (error) {
        console.error("儲存時發生錯誤：", error);
        alert("儲存失敗，請稍後再試！");
    }
}

function cancelEdit() {
    const classCode = new URLSearchParams(window.location.search).get('classId');
    if (confirm('確定取消編輯嗎？')) {
        window.location.href = `solo_class_info.html?classId=${classCode}`;
    }
}

function removeStudentFromList(studentId, dataList) {
    const index = dataList.findIndex(student => student.student_id === studentId);
    if (index !== -1) {
        dataList.splice(index, 1);
        console.log(`已刪除學生 ID: ${studentId}`);
    }
}

window.onload = fetchStudents;
