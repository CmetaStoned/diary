console.log('Скрипт работает');

function fetchEntries() {
  fetch('/api/entries')
    .then(response => {
      if (!response.ok) {
        throw new Error("Ошибка авторизации или сервера");
      }
      return response.json();
    })
    .then(data => {
      const container = document.getElementById('entries-container');
      container.innerHTML = '';

      if (!Array.isArray(data)) {
        console.error("API вернул не список:", data);
        return;
      }

      data.forEach(item => {
        if (!item.dateandtime || !item.entry) {
          console.error("Неполные данные:", item);
          return;
        }

        const entryDiv = document.createElement('div');
        entryDiv.className = 'entry';

        let [datePart, timePart] = item.dateandtime.split(" ");
        let dateArr = datePart.split(".");
        let timeArr = timePart.split(":");
        let nums = [...dateArr, ...timeArr];

        const pre1 = document.createElement('div');
        pre1.className = 'pre';
        pre1.innerHTML = `
          <p>${nums[0]}.${nums[1]}</p>
          <p>${nums[2]}</p>
          <p>${nums[3]}:${nums[4]}</p>
        `;

        const pre2 = document.createElement('div');
        pre2.className = 'pre';
        pre2.innerHTML = `<p>${item.id}</p>`;

        const info = document.createElement('div');
        info.className = 'info';
        info.innerHTML = `<h3>${item.entry}</h3>`;

        entryDiv.appendChild(pre1);
        entryDiv.appendChild(pre2);
        entryDiv.appendChild(info);

        container.appendChild(entryDiv);
      });
    })
    .catch(error => console.error('Ошибка при загрузке записей:', error));
}

window.addEventListener('DOMContentLoaded', () => {
  fetchEntries();
  setInterval(fetchEntries, 1000);
});
