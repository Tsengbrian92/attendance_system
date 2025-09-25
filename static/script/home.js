function getStudentIdFromUrl() {
    const params = new URLSearchParams(window.location.search);
    return params.get('studentId');
}

document.getElementById('grade_button').addEventListener('click', async () => {
    const username = getStudentIdFromUrl();
    window.location.href = `grade.html?studentId=${username}`;
});

document.getElementById('change_password_button').addEventListener('click', async () => {
    const username = getStudentIdFromUrl();
    window.location.href = `change_password.html?studentId=${username}`;
});

document.getElementById('attendance_button').addEventListener('click', async () => {
    const username = getStudentIdFromUrl();
    window.location.href = `attendance.html?studentId=${username}`;
});
document.getElementById('class_info_button').addEventListener('click', async () => {
    const username = getStudentIdFromUrl();
    window.location.href = `class_info.html?studentId=${username}`;
});