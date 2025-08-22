async function fetchWeeks() {
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
        
        return await weeksRes.json();
    } catch (error) {
        console.error('Error fetching weeks:', error);
        // Return default weeks if API fails
        return [
            { week_no: 1 },
            { week_no: 2 },
            { week_no: 3 },
            { week_no: 4 }
        ];
    }
}

function renderWeeks(weeks) {
    const weeksGrid = document.getElementById('weeksGrid');
    weeksGrid.innerHTML = '';
    
    weeks.forEach(week => {
        const weekCard = document.createElement('div');
        weekCard.className = 'week-card';
        weekCard.onclick = () => selectWeek(week.week_no);
        
        weekCard.innerHTML = `
            <div class="week-content">
                <h3 class="week-title">WEEK ${week.week_no}</h3>
                <div class="week-arrow">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                        <path d="M9 18L15 12L9 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                </div>
            </div>
        `;
        
        weeksGrid.appendChild(weekCard);
    });
}

function selectWeek(weekNo) {
    const card = event.currentTarget;
    card.style.transform = 'scale(0.98)';
    setTimeout(() => {
        card.style.transform = '';
        window.location.href = `/static/week-days.html?week=${weekNo}`;
    }, 150);
}

function goBack() {
    // Check if we came from program-foundational or index
    const referrer = document.referrer;
    if (referrer.includes('program-foundational')) {
        window.location.href = '/static/program-foundational.html';
    } else {
        window.location.href = '/static/index.html';
    }
}

document.addEventListener('DOMContentLoaded', async () => {
    const weeks = await fetchWeeks();
    renderWeeks(weeks);
});
