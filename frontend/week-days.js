async function fetchTrainingDays(weekNo) {
    try {
        // Get the program ID for "Full Body" program
        const programsRes = await fetch('/api/programs', { 
            cache: 'no-store',
            headers: { 'Accept': 'application/json' }
        });
        if (!programsRes.ok) throw new Error(`HTTP ${programsRes.status}: ${programsRes.statusText}`);
        
        const programs = await programsRes.json();
        const fullBodyProgram = programs.find(p => p.name === 'Full Body');
        if (!fullBodyProgram) throw new Error('Full Body program not found');
        
        // Get cycles for the program
        const cyclesRes = await fetch(`/api/cycles?program_id=${fullBodyProgram.id}`, { 
            cache: 'no-store',
            headers: { 'Accept': 'application/json' }
        });
        if (!cyclesRes.ok) throw new Error(`HTTP ${cyclesRes.status}: ${cyclesRes.statusText}`);
        
        const cycles = await cyclesRes.json();
        if (cycles.length === 0) throw new Error('No cycles found for program');
        
        // Get the latest cycle (assuming it's the first one for now)
        const latestCycle = cycles[0];
        
        // Get weeks for the cycle
        const weeksRes = await fetch(`/api/weeks?cycle_id=${latestCycle.id}`, { 
            cache: 'no-store',
            headers: { 'Accept': 'application/json' }
        });
        if (!weeksRes.ok) throw new Error(`HTTP ${weeksRes.status}: ${weeksRes.statusText}`);
        
        const weeks = await weeksRes.json();
        const targetWeek = weeks.find(w => w.week_no === weekNo);
        if (!targetWeek) throw new Error(`Week ${weekNo} not found`);
        
        // Get training days for the week
        const daysRes = await fetch(`/api/training-days?week_id=${targetWeek.id}`, { 
            cache: 'no-store',
            headers: { 'Accept': 'application/json' }
        });
        if (!daysRes.ok) throw new Error(`HTTP ${daysRes.status}: ${daysRes.statusText}`);
        
        return await daysRes.json();
    } catch (error) {
        console.error('Error fetching training days:', error);
        // Return default days if API fails
        return [
            { id: 1, name: 'Full Body', emphasis: 'chest', day_order: 1 },
            { id: 2, name: 'Full Body', emphasis: 'back', day_order: 2 },
            { id: 3, name: 'Full Body', emphasis: 'legs', day_order: 3 }
        ];
    }
}

function renderDays(days) {
    const daysGrid = document.getElementById('daysGrid');
    daysGrid.innerHTML = '';
    
    days.forEach(day => {
        const dayCard = document.createElement('div');
        dayCard.className = 'day-card';
        dayCard.onclick = () => selectDay(day.id, day.name);
        
        dayCard.innerHTML = `
            <div class="day-content">
                <div class="day-title">
                    <h3>${day.name || `Day ${day.day_order}`}</h3>
                    <span class="emphasis-badge">${(day.emphasis || '').toUpperCase()}</span>
                </div>
                <div class="day-arrow">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                        <path d="M9 18L15 12L9 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                </div>
            </div>
        `;
        
        daysGrid.appendChild(dayCard);
    });
}

function selectDay(dayId, dayName) {
    const card = event.currentTarget;
    card.style.transform = 'scale(0.98)';
    setTimeout(() => {
        card.style.transform = '';
        // Navigate to workout session page
        const urlParams = new URLSearchParams(window.location.search);
        const week = urlParams.get('week');
        const day = dayId;
        window.location.href = `/static/workout-session.html?week=${week}&day=${day}&dayId=${dayId}`;
    }, 150);
}

function getWeekFromUrl() {
    const urlParams = new URLSearchParams(window.location.search);
    return parseInt(urlParams.get('week')) || 1;
}

document.addEventListener('DOMContentLoaded', async () => {
    const weekNo = getWeekFromUrl();
    
    // Update page title
    const weekTitle = document.getElementById('weekTitle');
    weekTitle.textContent = `WEEK ${weekNo}`;
    
    const days = await fetchTrainingDays(weekNo);
    renderDays(days);
});
