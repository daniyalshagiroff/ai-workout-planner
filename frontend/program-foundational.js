async function fetchProgramData() {
    const res = await fetch('/api/programs/Full Body/export', { 
        cache: 'no-store',
        headers: {
            'Accept': 'application/json'
        }
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    return await res.json();
}

function capital(s) { return s.charAt(0).toUpperCase() + s.slice(1); }

function render(data) {
    const grid = document.getElementById('daysGrid');
    grid.innerHTML = '';
    data.days.forEach((day, idx) => {
        const card = document.createElement('div');
        card.className = 'day-card';
        card.innerHTML = `
            <div class="day-title">
                <h3>Day ${idx + 1}</h3>
                <span class="emphasis-badge">${(day.emphasis || '').toUpperCase()}</span>
            </div>
            <ul class="exercise-list">
                ${day.exercises.map((ex) => `
                    <li class="exercise-item">
                        <span class="exercise-name">${ex}</span>
                        <span class="exercise-meta">2 sets · RPE ~7–8</span>
                    </li>
                `).join('')}
            </ul>
        `;
        grid.appendChild(card);
    });
}

document.addEventListener('DOMContentLoaded', async () => {
    const data = await fetchProgramData();
    render(data);
});


