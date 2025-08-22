async function fetchDayExercises(dayId) {
    try {
        const response = await fetch(`/api/day-exercises?training_day_id=${dayId}`, { 
            cache: 'no-store',
            headers: { 'Accept': 'application/json' }
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        
        const exercises = await response.json();
        
        // Check if exercises have sets, if not use fallback data
        if (exercises.length === 0 || !exercises[0].sets) {
            console.warn('API returned exercises without sets, using fallback data');
            return [
                {
                    id: 1,
                    exercise: { name: 'Barbell Squat', equipment: 'barbell', target_muscle: 'quads' },
                    ex_order: 1,
                    sets: [
                        { id: 1, set_order: 1, target_weight: 80.0 },
                        { id: 2, set_order: 2, target_weight: 80.0 }
                    ]
                },
                {
                    id: 2,
                    exercise: { name: 'Bench Press', equipment: 'barbell', target_muscle: 'chest' },
                    ex_order: 2,
                    sets: [
                        { id: 3, set_order: 1, target_weight: 60.0 },
                        { id: 4, set_order: 2, target_weight: 60.0 }
                    ]
                },
                {
                    id: 3,
                    exercise: { name: 'Pulldown', equipment: 'cable', target_muscle: 'lats' },
                    ex_order: 3,
                    sets: [
                        { id: 5, set_order: 1, target_weight: 40.0 },
                        { id: 6, set_order: 2, target_weight: 40.0 }
                    ]
                }
            ];
        }
        
        return exercises;
    } catch (error) {
        console.error('Error fetching day exercises:', error);
        // Return default exercises if API fails
        return [
            {
                id: 1,
                exercise: { name: 'Barbell Squat', equipment: 'barbell', target_muscle: 'quads' },
                ex_order: 1,
                sets: [
                    { id: 1, set_order: 1, target_weight: 80.0 },
                    { id: 2, set_order: 2, target_weight: 80.0 }
                ]
            },
            {
                id: 2,
                exercise: { name: 'Bench Press', equipment: 'barbell', target_muscle: 'chest' },
                ex_order: 2,
                sets: [
                    { id: 3, set_order: 1, target_weight: 60.0 },
                    { id: 4, set_order: 2, target_weight: 60.0 }
                ]
            },
            {
                id: 3,
                exercise: { name: 'Pulldown', equipment: 'cable', target_muscle: 'lats' },
                ex_order: 3,
                sets: [
                    { id: 5, set_order: 1, target_weight: 40.0 },
                    { id: 6, set_order: 2, target_weight: 40.0 }
                ]
            }
        ];
    }
}

function renderExercises(exercises) {
    const exercisesList = document.getElementById('exercisesList');
    exercisesList.innerHTML = '';
    
    exercises.forEach((dayExercise, index) => {
        const exerciseCard = document.createElement('div');
        exerciseCard.className = 'exercise-card';
        exerciseCard.innerHTML = `
            <div class="exercise-header" onclick="toggleExercise(${index})">
                <div class="exercise-info">
                    <h3 class="exercise-name">${dayExercise.exercise.name}</h3>
                    <div class="exercise-meta">
                        <span class="equipment">${dayExercise.exercise.equipment}</span>
                        <span class="target-muscle">${dayExercise.exercise.target_muscle}</span>
                    </div>
                </div>
                <div class="exercise-toggle">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" class="toggle-icon">
                        <path d="M6 9L12 15L18 9" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                </div>
            </div>
            <div class="exercise-sets" id="sets-${index}" style="display: none;">
                ${dayExercise.sets.map(set => `
                    <div class="set-row" data-set-id="${set.id}">
                        <div class="set-info">
                            <span class="set-number">Set ${set.set_order}</span>
                            <span class="target-weight">Target: ${set.target_weight}kg</span>
                        </div>
                        <div class="set-inputs">
                            <input type="number" class="weight-input" placeholder="Weight (kg)" min="0" step="0.5">
                            <input type="number" class="reps-input" placeholder="Reps" min="1" max="50">
                        </div>
                        <button class="complete-set-btn" onclick="completeSet(${set.id}, this)">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                                <path d="M20 6L9 17L4 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                            </svg>
                        </button>
                    </div>
                `).join('')}
            </div>
        `;
        
        exercisesList.appendChild(exerciseCard);
    });
}

function toggleExercise(index) {
    const setsContainer = document.getElementById(`sets-${index}`);
    const toggleIcon = event.currentTarget.querySelector('.toggle-icon');
    
    if (setsContainer.style.display === 'none') {
        setsContainer.style.display = 'block';
        toggleIcon.style.transform = 'rotate(180deg)';
    } else {
        setsContainer.style.display = 'none';
        toggleIcon.style.transform = 'rotate(0deg)';
    }
}

function completeSet(setId, button) {
    const setRow = button.closest('.set-row');
    const weightInput = setRow.querySelector('.weight-input');
    const repsInput = setRow.querySelector('.reps-input');
    
    const weight = weightInput.value;
    const reps = repsInput.value;
    
    if (!weight || !reps) {
        alert('Please enter both weight and reps');
        return;
    }
    
    // Mark set as completed
    setRow.classList.add('completed');
    button.classList.add('completed');
    button.innerHTML = `
        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
            <path d="M20 6L9 17L4 12"/>
        </svg>
    `;
    
    // Disable inputs
    weightInput.disabled = true;
    repsInput.disabled = true;
    
    console.log(`Set ${setId} completed: ${weight}kg x ${reps} reps`);
}

function getUrlParams() {
    const urlParams = new URLSearchParams(window.location.search);
    return {
        week: urlParams.get('week'),
        day: urlParams.get('day'),
        dayId: urlParams.get('dayId')
    };
}

document.addEventListener('DOMContentLoaded', async () => {
    const params = getUrlParams();
    
    // Update page title
    const sessionTitle = document.getElementById('sessionTitle');
    sessionTitle.textContent = `WEEK ${params.week} - DAY ${params.day}`;
    
    // Fetch exercises for the day
    const exercises = await fetchDayExercises(params.dayId || 1);
    renderExercises(exercises);
});
