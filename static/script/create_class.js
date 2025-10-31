document.addEventListener("DOMContentLoaded", () => {
  const timeInputsContainer = document.getElementById("time-inputs-container");
  const daysCheckboxes = document.querySelectorAll(".class-day");

  // 👉 班級代碼：只允許小寫英數，並即時過濾
  const classCodeInput = document.getElementById("class_code");
  classCodeInput.addEventListener("input", (e) => {
    const cleaned = e.target.value.toLowerCase().replace(/[^a-z0-9]/g, "");
    if (cleaned !== e.target.value) e.target.value = cleaned;
    // 移除自訂錯誤訊息（若先前 invalid）
    e.target.setCustomValidity("");
  });

  // 自訂 invalid 訊息（搭配 HTML 的 pattern）
  classCodeInput.addEventListener("invalid", function () {
    this.setCustomValidity("班級代碼僅能使用英文小寫與數字，且至少 1 碼。");
  });
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

        fetch("http://26.218.4.126:5000/api/create-class", {
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
            window.location.href = 'home.html';
        })
        .catch(error => {
            console.error("Error:", error);
            alert("建立班級失敗，請稍後再試！");
        });
    });
});
