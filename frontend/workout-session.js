// Helper function to get default weight for exercise
function getDefaultWeight(exerciseName) {
    const weights = {
        'barbell squat': 80.0,
        'bench press': 60.0,
        'pulldown': 40.0,
        'biceps curls': 12.5,
        'triceps pushdown': 25.0
    };
    return weights[exerciseName.toLowerCase()] || 50.0;
}

async function fetchDayExercises(dayId) {
    console.log('Fetching exercises for dayId:', dayId);
    try {
        const url = `/api/day-exercises?training_day_id=${dayId}`;
        console.log('Making API request to:', url);
        
        const response = await fetch(url, { 
            cache: 'no-store',
            headers: { 'Accept': 'application/json' }
        });
        
        console.log('API response status:', response.status);
        console.log('API response ok:', response.ok);
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('API error response:', errorText);
            throw new Error(`HTTP ${response.status}: ${response.statusText} - ${errorText}`);
        }
        
        const exercises = await response.json();
        console.log('API returned exercises:', exercises);
        
        // Check if exercises have sets, if not use fallback data
        if (exercises.length === 0) {
            console.warn('API returned no exercises, using fallback data');
            return getFallbackExercises();
        }
        
        // API returns exercises without sets, so we need to add sets
        console.log('API returned exercises without sets, adding sets to each exercise');
        const exercisesWithSets = exercises.map((exercise, index) => ({
            ...exercise,
            sets: [
                { id: index * 2 + 1, set_order: 1, target_weight: getDefaultWeight(exercise.exercise.name) },
                { id: index * 2 + 2, set_order: 2, target_weight: getDefaultWeight(exercise.exercise.name) }
            ]
        }));
        
        return exercisesWithSets;
    } catch (error) {
        console.error('Error fetching day exercises:', error);
        console.error('Error details:', error.message);
        // Return default exercises if API fails
        return getFallbackExercises();
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
