document.addEventListener('DOMContentLoaded', () => {
    const merchantInput = document.getElementById('merchantInput');
    const suggestionsDiv = document.getElementById('suggestions');
    const resultsTable = document.getElementById('resultsTable');
    const resultsBody = document.getElementById('resultsBody');

    merchantInput.addEventListener('input', async () => {
        const query = merchantInput.value.trim();
        if (query.length < 2) {
            suggestionsDiv.innerHTML = '';
            return;
        }

        const response = await fetch(`/suggest?q=${encodeURIComponent(query)}`);
        const suggestions = await response.json();
        suggestionsDiv.innerHTML = suggestions.map(s => `<div>${s}</div>`).join('');
    });

    suggestionsDiv.addEventListener('click', async (e) => {
        const merchant = e.target.textContent;
        merchantInput.value = merchant;
        suggestionsDiv.innerHTML = '';

        resultsBody.innerHTML = '<tr><td colspan="3">Loading...</td></tr>';
        resultsTable.style.display = 'table';

        const formData = new FormData();
        formData.append('merchant', merchant);

        const response = await fetch('/search', {
            method: 'POST',
            body: formData
        });
        const results = await response.json();

        if (results.error) {
            resultsBody.innerHTML = `<tr><td colspan="3">${results.error}</td></tr>`;
            return;
        }

        resultsBody.innerHTML = ''; // Clear loading
        results.forEach(result => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${result.Site}</td>
                <td>${result.Cashback}</td>
                <td><a href="${result.URL}" target="_blank">Go</a></td>
            `;
            resultsBody.appendChild(row);
        });
    });
});
