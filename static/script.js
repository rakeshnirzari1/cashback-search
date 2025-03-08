document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('merchantInput');
    const suggestions = document.getElementById('suggestions');
    const table = document.getElementById('resultsTable');
    const tbody = document.getElementById('resultsBody');

    // Autosuggest
    input.addEventListener('input', async () => {
        const query = input.value.trim();
        if (query.length < 2) {
            suggestions.innerHTML = '';
            table.style.display = 'none';
            return;
        }
        const response = await fetch(`/suggest?q=${encodeURIComponent(query)}`);
        const data = await response.json();
        suggestions.innerHTML = data.map(item => `<div>${item}</div>`).join('');
        suggestions.style.display = 'block';
    });

    // Select suggestion and fetch cashback immediately
    suggestions.addEventListener('click', async (e) => {
        if (e.target.tagName === 'DIV') {
            const merchant = e.target.textContent;
            input.value = merchant;
            suggestions.style.display = 'none';

            // Show loading state
            tbody.innerHTML = '<tr><td colspan="3">Loading...</td></tr>';
            table.style.display = 'table';

            // Fetch cashback data
            const response = await fetch('/search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: `merchant=${encodeURIComponent(merchant)}`
            });
            const data = await response.json();

            if (data.error) {
                tbody.innerHTML = `<tr><td colspan="3">${data.error}</td></tr>`;
            } else {
                tbody.innerHTML = data.map(row => `
                    <tr>
                        <td>${row.Site}</td>
                        <td>${row.Cashback}</td>
                        <td><a href="${row.URL}" target="_blank">Go</a></td>
                    </tr>
                `).join('');
            }
        }
    });

    // Hide suggestions when clicking outside
    document.addEventListener('click', (e) => {
        if (!suggestions.contains(e.target) && e.target !== input) {
            suggestions.style.display = 'none';
        }
    });
});
