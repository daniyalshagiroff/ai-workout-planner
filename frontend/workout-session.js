async function fetchDayExercises(dayId) {
    console.log('Fetching exercises for dayId:', dayId);
    try {
        const url = `http://localhost:8000/api/day-exercises?training_day_id=${dayId}`;
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
        
        // API returns exercises without sets, so we need to add sets and fetch existing data
        console.log('API returned exercises without sets, adding sets to each exercise');
        const exercisesWithSets = await Promise.all(exercises.map(async (exercise, index) => {
            // Fetch existing sets for this exercise
            try {
                const setsResponse = await fetch(`http://localhost:8000/api/sets?day_exercise_id=${exercise.id}`);
                if (setsResponse.ok) {
                    const existingSets = await setsResponse.json();
                    console.log(`Found ${existingSets.length} existing sets for exercise ${exercise.id}`);
                    
                    // Create sets array with existing data or defaults
                    const sets = [
                        { id: exercise.id, set_order: 1, target_weight: 0, completed: false, rep: null, weight: null },
                        { id: exercise.id, set_order: 2, target_weight: 0, completed: false, rep: null, weight: null }
                    ];
                    
                    // Update with existing data
                    existingSets.forEach(existingSet => {
                        const setIndex = existingSet.set_order - 1;
                        if (setIndex < sets.length) {
                            sets[setIndex] = {
                                ...sets[setIndex],
                                id: existingSet.id,
                                rep: existingSet.rep,
                                weight: existingSet.weight,
                                completed: existingSet.rep !== null && existingSet.weight !== null
                            };
                        }
                    });
                    
                    return {
                        ...exercise,
                        sets: sets
                    };
                }
            } catch (error) {
                console.error(`Error fetching sets for exercise ${exercise.id}:`, error);
            }
            
            // Fallback to default sets
            return {
                ...exercise,
                sets: [
                    { id: exercise.id, set_order: 1, target_weight: 0, completed: false, rep: null, weight: null },
                    { id: exercise.id, set_order: 2, target_weight: 0, completed: false, rep: null, weight: null }
                ]
            };
        }));
        
        return exercisesWithSets;
    } catch (error) {
        console.error('Error fetching day exercises:', error);
        console.error('Error details:', error.message);
        // Return default exercises if API fails
        return getFallbackExercises();
    }
}

async function displayAddedSets(dayExerciseId, set_order) {
    try {
        const response = await fetch(`/api/sets?day_exercise_id=${dayExerciseId}`);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        const sets = await response.json();
        console.log('API returned sets:', sets);
        
        const targetSet = sets.find(set => set.set_order === set_order);
        if (targetSet) {
            const setRow = document.querySelector(`.set-row[data-set-id="${targetSet.id}"]`);
            if (setRow) {
                const weightInput = setRow.querySelector('.weight-input');
                const repsInput = setRow.querySelector('.reps-input');
                const completeBtn = setRow.querySelector('.complete-set-btn');
                
                // Заполняем данные
                weightInput.value = targetSet.weight;
                repsInput.value = targetSet.rep;
                
                // Проверяем, завершен ли сет (есть ли данные)
                if (targetSet.rep !== null && targetSet.weight !== null) {
                    // Применяем стили завершенного сета
                    setRow.classList.add('completed');
                    completeBtn.classList.add('completed');
                    
                    // Заполняем галочку
                    completeBtn.innerHTML = `
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M20 6L9 17L4 12"/>
                        </svg>
                    `;
                    
                    // Отключаем поля ввода
                    weightInput.disabled = true;
                    repsInput.disabled = true;
                    
                    console.log('Set data loaded and marked as completed:', targetSet);
                } else {
                    console.log('Set data loaded (not completed):', targetSet);
                }
            } else {
                console.log('Set row not found in DOM');
            }
        } else {
            console.log('Set not found in API response');
        }
    } catch (error) {
        console.error('Error displaying added sets:', error);
        alert('Failed to display added sets. Please try again.');
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

async function completeSet(setId, button) {
    const setRow = button.closest('.set-row');
    const weightInput = setRow.querySelector('.weight-input');
    const repsInput = setRow.querySelector('.reps-input');
    
    const weight = weightInput.value;
    const reps = repsInput.value;
    
    if (!weight || !reps) {
        alert('Please enter both weight and reps');
        return;
    }

    try {
        const response = await fetch(`http://localhost:8000/api/sets`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                day_exercise_id: parseInt(setId),
                set_order: parseInt(setRow.querySelector('.set-number').textContent.split(' ')[1]),
                rep: parseInt(reps),
                weight: parseFloat(weight),
                target_weight: null
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
    } catch (error) {
        console.error('Error completing set:', error);
        alert('Failed to complete set. Please try again.');
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
    
    console.log(`Set ${setId} completed: ${weight}kg x ${reps} reps!!!`);
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
    
    // Load existing set data for each exercise
    for (const exercise of exercises) {
        for (const set of exercise.sets) {
            await displayAddedSets(exercise.id, set.set_order);
        }
    }
});
