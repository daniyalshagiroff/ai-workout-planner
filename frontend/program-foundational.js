async function fetchProgramData() {
    try {
        // Fetch from FastAPI endpoint
        const res = await fetch('/api/programs/Full Body/export', { 
            cache: 'no-store',
            headers: {
                'Accept': 'application/json'
            }
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
        return await res.json();
    } catch (e) {
        console.error('Failed to fetch program data:', e);
        // Fallback: minimal mock if API not available
        return {
            program: { name: 'Full Body', days_per_week: 3 },
            week: { week_no: 1 },
            days: [
                { label: 'Day 1', emphasis: 'chest', exercises: ['barbell squat', 'bench press', 'pulldown', 'biceps curls', 'triceps pushdown'] },
                { label: 'Day 2', emphasis: 'back', exercises: ['barbell squat', 'bench press', 'pulldown', 'biceps curls', 'triceps pushdown'] },
                { label: 'Day 3', emphasis: 'legs', exercises: ['barbell squat', 'bench press', 'pulldown', 'biceps curls', 'triceps pushdown'] },
            ]
        };
    }
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


