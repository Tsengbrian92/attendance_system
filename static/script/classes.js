// 從網址 ?studentId=... 取得使用者
const params = new URLSearchParams(location.search);
const studentId = params.get('studentId');

let accessToken = localStorage.getItem('access_token');

// 沒帶 studentId 就提示
if (!studentId) {
  const container = document.getElementById('classes-list');
  container.innerHTML = '<p style="color:#900;">缺少 studentId 參數</p>';
} else {
  // 取得我的班級（改：把 studentId 放到 query string）
  fetch(`http://26.8.220.101:5000/api/my_classes?studentId=${encodeURIComponent(studentId)}`, {
      headers: { 'Authorization': 'Bearer ' + accessToken }
  })
  .then(res => res.json())
  .then(classes => {
      const container = document.getElementById('classes-list');
      if (!Array.isArray(classes) || classes.length === 0) {
        container.innerHTML = '<p>尚未加入任何課程</p>';
        return;
      }

      classes.forEach(cls => {
          // 創建班級框框
          const card = document.createElement('div');
          card.className = 'class-card';
          card.style = 'border:1px solid #888;padding:1em;margin:1em 0;border-radius:10px;';

          // 標題和箭頭
          const header = document.createElement('div');
          header.innerHTML = `
              <span style="font-size:1.2em;">${cls.class_name}</span>
              <span class="arrow" style="float:right;cursor:pointer;">▼</span>
          `;
          card.appendChild(header);

          // 下拉內容(初始隱藏)
          const detail = document.createElement('div');
          detail.style.display = 'none';
          detail.textContent = "讀取中...";
          card.appendChild(detail);

          // 點擊箭頭展開/收合
          header.addEventListener('click', () => {
              if (detail.style.display === 'none') {
                  detail.style.display = 'block';
                  // 請求該班級成績（改：帶上 studentId）
                  fetch(`http://26.8.220.101:5000/api/class_grade/${encodeURIComponent(cls.class_code)}?studentId=${encodeURIComponent(studentId)}`, {
                      headers: { 'Authorization': 'Bearer ' + accessToken }
                  })
                  .then(res => res.json())
                  .then(grades => {
                      if (!Array.isArray(grades) || grades.length === 0) {
                          detail.textContent = "本課程尚無成績";
                      } else {
                          detail.innerHTML = `
                              <ul class="score-list">
                                  ${grades.map(g => `<li>${g.exam_name}: ${g.score}</li>`).join('')}
                              </ul>
                          `;
                      }
                  })
                  .catch(err => {
                      detail.innerHTML = `<span style="color:#900;">讀取失敗：${err.message}</span>`;
                  });
              } else {
                  detail.style.display = 'none';
              }
          });

          container.appendChild(card);
      });
  })
  .catch(err => {
      const container = document.getElementById('classes-list');
      container.innerHTML = `<p style="color:#900;">載入失敗：${err.message}</p>`;
  });
}
