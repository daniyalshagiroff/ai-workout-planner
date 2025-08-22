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
    const daysGrid = document.getElementById('daysGrid');
    daysGrid.innerHTML = '';
    
    data.days.forEach(day => {
        const dayCard = document.createElement('div');
        dayCard.className = 'day-card';
        
        dayCard.innerHTML = `
            <h3 class="day-title">${day.label}</h3>
            <div class="day-emphasis">${day.emphasis}</div>
            <ul class="exercises-list">
                ${day.exercises.map(exercise => `<li class="exercise-item">${exercise}</li>`).join('')}
            </ul>
        `;
        
        daysGrid.appendChild(dayCard);
    });
}


function startProgram() {
    window.location.href = '/static/workout-plan.html';
}


document.addEventListener('DOMContentLoaded', async () => {
    const data = await fetchProgramData();
    render(data);
});


