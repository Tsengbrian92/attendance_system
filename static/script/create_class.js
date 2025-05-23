document.addEventListener("DOMContentLoaded", () => {
    const timeInputsContainer = document.getElementById("time-inputs-container");
    const daysCheckboxes = document.querySelectorAll(".class-day");

    daysCheckboxes.forEach(checkbox => {
        checkbox.addEventListener("change", () => {
            const day = checkbox.value;
            const existingInput = document.getElementById(`time-input-${day}`);

            if (checkbox.checked) {
                // 如果選中，生成時間輸入框
                if (!existingInput) {
                    const timeInputGroup = document.createElement("div");
                    timeInputGroup.className = "form-group";
                    timeInputGroup.id = `time-input-${day}`;
                    timeInputGroup.innerHTML = `
                        <label for="start-time-${day}">請選擇 ${day} 的上課開始時間</label>
                        <input type="time" id="start-time-${day}" name="start-time-${day}" required>

                        <label for="end-time-${day}">請選擇 ${day} 的上課結束時間</label>
                        <input type="time" id="end-time-${day}" name="end-time-${day}" required>
                    `;
                    timeInputsContainer.appendChild(timeInputGroup);
                }
            } else {
                // 如果取消選中，移除對應的時間輸入框
                if (existingInput) {
                    existingInput.remove();
                }
            }
        });
    });

    document.getElementById("create-class-form").addEventListener("submit", function(event) {
        event.preventDefault();

        const selectedDays = Array.from(document.querySelectorAll(".class-day:checked")).map(checkbox => {
            const day = checkbox.value;
            const startTime = document.getElementById(`start-time-${day}`).value;
            const endTime = document.getElementById(`end-time-${day}`).value;

            return { day, start_time: startTime, end_time: endTime };
        });

        const classData = {
            class_code: document.getElementById("class_code").value,
            class_name: document.getElementById("class_name").value,
            teacher_name: document.getElementById("teacher_name").value,
            max_students: document.getElementById("students_count").value,
            class_count: document.getElementById("class_count").value,
            start_date: document.getElementById("start_date").value,
            schedule: selectedDays, // 將選中的星期與時間一起傳送
        };

        fetch("http://127.0.0.1:5000/api/create-class", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(classData),
        })
        .then(response => response.json())
        .then(data => {
            alert(data.message);
            document.getElementById("create-class-form").reset();
            timeInputsContainer.innerHTML = ""; // 清空動態生成的時間輸入框
        })
        .catch(error => {
            console.error("Error:", error);
            alert("建立班級失敗，請稍後再試！");
        });
    });
});
