/*
  Minimal, local workout plan generator. No external API required.
  You can swap out generatePlanWithLocalHeuristics with your API call later.
*/

(function () {
    const form = document.getElementById('planner-form');
    const resultEl = document.getElementById('result');
    const copyBtn = document.getElementById('copyBtn');
    const downloadBtn = document.getElementById('downloadBtn');
    const printBtn = document.getElementById('printBtn');
    const resetBtn = document.getElementById('resetBtn');

    // --- Exercise library (compact but reasonably diverse) ---
    const LIB = {
        full_body: [
            { name: 'Bodyweight Squat', tags: ['bodyweight'], area: 'legs', level: 'beginner' },
            { name: 'Goblet Squat', tags: ['dumbbells', 'kettlebell'], area: 'legs', level: 'beginner' },
            { name: 'Barbell Back Squat', tags: ['barbell'], area: 'legs', level: 'intermediate' },
            { name: 'Romanian Deadlift', tags: ['barbell', 'dumbbells'], area: 'legs', level: 'intermediate' },
            { name: 'Hip Thrust', tags: ['barbell', 'dumbbells', 'bodyweight'], area: 'glutes', level: 'beginner' },
            { name: 'Glute Bridge', tags: ['bodyweight', 'bands'], area: 'glutes', level: 'beginner' },
            { name: 'Push‑up', tags: ['bodyweight'], area: 'push', level: 'beginner' },
            { name: 'Incline Push‑up', tags: ['bodyweight'], area: 'push', level: 'beginner' },
            { name: 'Dumbbell Bench Press', tags: ['dumbbells'], area: 'push', level: 'beginner' },
            { name: 'Barbell Bench Press', tags: ['barbell'], area: 'push', level: 'intermediate' },
            { name: 'Overhead Press', tags: ['barbell', 'dumbbells'], area: 'push', level: 'intermediate' },
            { name: 'Seated Shoulder Press', tags: ['machines'], area: 'push', level: 'beginner' },
            { name: 'Pull‑up', tags: ['bodyweight'], area: 'pull', level: 'intermediate' },
            { name: 'Assisted Pull‑up', tags: ['machines', 'bands'], area: 'pull', level: 'beginner' },
            { name: 'Lat Pulldown', tags: ['machines'], area: 'pull', level: 'beginner' },
            { name: 'Dumbbell Row', tags: ['dumbbells'], area: 'pull', level: 'beginner' },
            { name: 'Barbell Row', tags: ['barbell'], area: 'pull', level: 'intermediate' },
            { name: 'Face Pull', tags: ['bands', 'machines'], area: 'pull', level: 'beginner' },
            { name: 'Plank', tags: ['bodyweight'], area: 'core', level: 'beginner' },
            { name: 'Hollow Hold', tags: ['bodyweight'], area: 'core', level: 'intermediate' },
            { name: 'Dead Bug', tags: ['bodyweight'], area: 'core', level: 'beginner' },
            { name: 'Cable Crunch', tags: ['machines'], area: 'core', level: 'beginner' },
        ],
        upper: [
            { name: 'Push‑up', tags: ['bodyweight'], area: 'push', level: 'beginner' },
            { name: 'Dumbbell Bench Press', tags: ['dumbbells'], area: 'push', level: 'beginner' },
            { name: 'Incline Dumbbell Press', tags: ['dumbbells'], area: 'push', level: 'intermediate' },
            { name: 'Barbell Bench Press', tags: ['barbell'], area: 'push', level: 'intermediate' },
            { name: 'Overhead Press', tags: ['barbell', 'dumbbells'], area: 'push', level: 'intermediate' },
            { name: 'Lat Pulldown', tags: ['machines'], area: 'pull', level: 'beginner' },
            { name: 'Pull‑up', tags: ['bodyweight'], area: 'pull', level: 'intermediate' },
            { name: 'Assisted Pull‑up', tags: ['machines', 'bands'], area: 'pull', level: 'beginner' },
            { name: 'Dumbbell Row', tags: ['dumbbells'], area: 'pull', level: 'beginner' },
            { name: 'Barbell Row', tags: ['barbell'], area: 'pull', level: 'intermediate' },
            { name: 'Lateral Raise', tags: ['dumbbells', 'bands'], area: 'shoulders', level: 'beginner' },
            { name: 'Face Pull', tags: ['bands', 'machines'], area: 'rear_delts', level: 'beginner' },
            { name: 'Biceps Curl', tags: ['dumbbells', 'barbell', 'bands'], area: 'arms', level: 'beginner' },
            { name: 'Triceps Pushdown', tags: ['machines', 'bands'], area: 'arms', level: 'beginner' },
        ],
        lower: [
            { name: 'Bodyweight Squat', tags: ['bodyweight'], area: 'quads', level: 'beginner' },
            { name: 'Goblet Squat', tags: ['dumbbells', 'kettlebell'], area: 'quads', level: 'beginner' },
            { name: 'Barbell Back Squat', tags: ['barbell'], area: 'quads', level: 'intermediate' },
            { name: 'Romanian Deadlift', tags: ['barbell', 'dumbbells'], area: 'hamstrings', level: 'intermediate' },
            { name: 'Hip Thrust', tags: ['barbell', 'dumbbells', 'bodyweight'], area: 'glutes', level: 'beginner' },
            { name: 'Lunge', tags: ['bodyweight', 'dumbbells'], area: 'glutes', level: 'beginner' },
            { name: 'Calf Raise', tags: ['machines', 'bodyweight', 'dumbbells'], area: 'calves', level: 'beginner' },
            { name: 'Leg Press', tags: ['machines'], area: 'quads', level: 'beginner' },
            { name: 'Leg Curl', tags: ['machines'], area: 'hamstrings', level: 'beginner' },
        ],
        push: [
            { name: 'Push‑up', tags: ['bodyweight'], area: 'chest', level: 'beginner' },
            { name: 'Dumbbell Bench Press', tags: ['dumbbells'], area: 'chest', level: 'beginner' },
            { name: 'Incline Dumbbell Press', tags: ['dumbbells'], area: 'chest', level: 'intermediate' },
            { name: 'Overhead Press', tags: ['barbell', 'dumbbells'], area: 'shoulders', level: 'intermediate' },
            { name: 'Lateral Raise', tags: ['dumbbells', 'bands'], area: 'shoulders', level: 'beginner' },
            { name: 'Triceps Pushdown', tags: ['machines', 'bands'], area: 'triceps', level: 'beginner' },
        ],
        pull: [
            { name: 'Pull‑up', tags: ['bodyweight'], area: 'back', level: 'intermediate' },
            { name: 'Assisted Pull‑up', tags: ['machines', 'bands'], area: 'back', level: 'beginner' },
            { name: 'Lat Pulldown', tags: ['machines'], area: 'back', level: 'beginner' },
            { name: 'Dumbbell Row', tags: ['dumbbells'], area: 'back', level: 'beginner' },
            { name: 'Barbell Row', tags: ['barbell'], area: 'back', level: 'intermediate' },
            { name: 'Face Pull', tags: ['bands', 'machines'], area: 'rear_delts', level: 'beginner' },
            { name: 'Biceps Curl', tags: ['dumbbells', 'barbell', 'bands'], area: 'biceps', level: 'beginner' },
        ],
        legs: [
            { name: 'Bodyweight Squat', tags: ['bodyweight'], area: 'quads', level: 'beginner' },
            { name: 'Goblet Squat', tags: ['dumbbells', 'kettlebell'], area: 'quads', level: 'beginner' },
            { name: 'Barbell Back Squat', tags: ['barbell'], area: 'quads', level: 'intermediate' },
            { name: 'Romanian Deadlift', tags: ['barbell', 'dumbbells'], area: 'hamstrings', level: 'intermediate' },
            { name: 'Lunge', tags: ['bodyweight', 'dumbbells'], area: 'glutes', level: 'beginner' },
            { name: 'Hip Thrust', tags: ['barbell', 'dumbbells', 'bodyweight'], area: 'glutes', level: 'beginner' },
            { name: 'Calf Raise', tags: ['machines', 'bodyweight', 'dumbbells'], area: 'calves', level: 'beginner' },
        ],
        core: [
            { name: 'Plank', tags: ['bodyweight'], area: 'core', level: 'beginner' },
            { name: 'Hollow Hold', tags: ['bodyweight'], area: 'core', level: 'intermediate' },
            { name: 'Dead Bug', tags: ['bodyweight'], area: 'core', level: 'beginner' },
            { name: 'Cable Crunch', tags: ['machines'], area: 'core', level: 'beginner' },
        ]
    };

    function getFormData() {
        const data = new FormData(form);
        const equipment = Array.from(document.querySelectorAll('input[name="equipment"]:checked')).map(i => i.value);
        const custom = (data.get('customEquipment') || '').toString()
            .split(',')
            .map(s => s.trim().toLowerCase())
            .filter(Boolean);
        return {
            goal: data.get('goal'),
            level: data.get('level'),
            location: data.get('location'),
            days: Number(data.get('days')),
            minutes: Number(data.get('minutes')),
            split: data.get('split'),
            equipment: [...new Set([...equipment, ...custom])],
            warmup: document.getElementById('warmup').checked,
            cooldown: document.getElementById('cooldown').checked,
            notes: (data.get('notes') || '').toString().trim(),
        };
    }

    function pickSplit(days, splitPref) {
        if (splitPref && splitPref !== 'auto') return splitPref;
        if (days <= 3) return 'full_body';
        if (days === 4) return 'upper_lower';
        return 'ppl';
    }

    function repsAndSetsForGoal(goal, level) {
        // Defaults tuned for time efficiency
        const baseSets = level === 'advanced' ? 4 : level === 'intermediate' ? 3 : 2;
        switch (goal) {
            case 'strength': return { reps: '4–6', sets: baseSets + 1, rest: '2–3 min' };
            case 'endurance': return { reps: '12–20', sets: baseSets, rest: '45–60 sec' };
            case 'fat_loss': return { reps: '10–15', sets: baseSets, rest: '60–90 sec' };
            case 'muscle':
            default: return { reps: '8–12', sets: baseSets, rest: '60–90 sec' };
        }
    }

    function estimateExerciseCount(minutes) {
        if (minutes <= 30) return 5;
        if (minutes <= 45) return 7;
        if (minutes <= 60) return 9;
        return 10;
    }

    function filterByEquipment(exercises, equipment) {
        if (!equipment || equipment.length === 0) return exercises;
        return exercises.filter(ex => ex.tags.some(tag => equipment.includes(tag)));
    }

    function filterByLevel(exercises, level) {
        const order = ['beginner', 'intermediate', 'advanced'];
        const idx = order.indexOf(level);
        return exercises.filter(ex => order.indexOf(ex.level) <= idx);
    }

    function uniqueByName(exercises) {
        const seen = new Set();
        const out = [];
        for (const ex of exercises) {
            if (seen.has(ex.name)) continue;
            seen.add(ex.name);
            out.push(ex);
        }
        return out;
    }

    function chooseExercises(targetPool, equipment, level, desiredCount, includeCore = true) {
        const pool = uniqueByName(filterByLevel(filterByEquipment(targetPool, equipment), level));
        const chosen = [];
        const usedAreas = new Set();
        for (const ex of pool) {
            if (chosen.length >= desiredCount) break;
            if (!usedAreas.has(ex.area)) {
                chosen.push(ex);
                usedAreas.add(ex.area);
            }
        }
        // Fill remaining slots with any exercises
        for (const ex of pool) {
            if (chosen.length >= desiredCount) break;
            if (!chosen.some(c => c.name === ex.name)) chosen.push(ex);
        }
        // Optionally ensure at least one core movement
        if (includeCore && !chosen.some(ex => ex.area === 'core')) {
            const core = filterByLevel(filterByEquipment(LIB.core, equipment), level)[0];
            if (core) chosen.push(core);
        }
        return chosen.slice(0, desiredCount);
    }

    function assembleDay(label, pool, equipment, level, goal, minutes, includeCore) {
        const { reps, sets, rest } = repsAndSetsForGoal(goal, level);
        const count = Math.max(4, Math.min(10, estimateExerciseCount(minutes)));
        const exercises = chooseExercises(pool, equipment, level, count, includeCore);
        return {
            label,
            guidance: `${sets} sets, ${reps} reps · Rest ${rest}`,
            exercises: exercises.map(e => ({ name: e.name, area: e.area }))
        };
    }

    function generatePlanWithLocalHeuristics(input) {
        const split = pickSplit(input.days, input.split);
        const equipment = input.equipment.length ? input.equipment : ['bodyweight'];
        const warmup = input.warmup ? '5–8 min light cardio + dynamic mobility' : null;
        const cooldown = input.cooldown ? '5–8 min easy cardio + static stretching' : null;
        const days = [];

        if (split === 'full_body') {
            for (let i = 1; i <= input.days; i++) {
                days.push(assembleDay(`Day ${i} · Full Body`, LIB.full_body, equipment, input.level, input.goal, input.minutes, true));
            }
        } else if (split === 'upper_lower') {
            const pattern = ['Upper', 'Lower'];
            for (let i = 0; i < input.days; i++) {
                const isUpper = pattern[i % 2] === 'Upper';
                const pool = isUpper ? [...LIB.upper, ...LIB.core] : [...LIB.lower, ...LIB.core];
                days.push(assembleDay(`Day ${i + 1} · ${isUpper ? 'Upper' : 'Lower'}`, pool, equipment, input.level, input.goal, input.minutes, true));
            }
        } else {
            const pattern = ['Push', 'Pull', 'Legs'];
            for (let i = 0; i < input.days; i++) {
                const label = pattern[i % 3];
                const pool = label === 'Push' ? [...LIB.push, ...LIB.core]
                    : label === 'Pull' ? [...LIB.pull, ...LIB.core]
                    : [...LIB.legs, ...LIB.core];
                days.push(assembleDay(`Day ${i + 1} · ${label}`, pool, equipment, input.level, input.goal, input.minutes, true));
            }
        }

        return {
            meta: {
                goal: input.goal,
                level: input.level,
                split,
                days_per_week: input.days,
                session_minutes: input.minutes,
                equipment,
                warmup,
                cooldown,
                notes: input.notes || undefined,
            },
            days
        };
    }

    function planToText(plan) {
        const header = `Goal: ${prettyGoal(plan.meta.goal)}  |  Level: ${capital(plan.meta.level)}  |  Split: ${prettySplit(plan.meta.split)}\n` +
            `Days/Week: ${plan.meta.days_per_week}  |  Session: ${plan.meta.session_minutes} min  |  Equipment: ${plan.meta.equipment.join(', ')}`;
        const notes = plan.meta.notes ? `\nNotes: ${plan.meta.notes}` : '';
        const warmup = plan.meta.warmup ? `\nWarm‑up: ${plan.meta.warmup}` : '';
        const cooldown = plan.meta.cooldown ? `\nCool‑down: ${plan.meta.cooldown}` : '';
        const daysText = plan.days.map(d => {
            const exList = d.exercises.map((e, i) => `${i + 1}. ${e.name}`).join('\n');
            return `\n\n${d.label}\n${d.guidance}\n${exList}`;
        }).join('');
        return header + notes + warmup + cooldown + daysText + '\n';
    }

    function prettyGoal(goal) {
        switch (goal) {
            case 'fat_loss': return 'Fat Loss';
            case 'endurance': return 'Endurance';
            case 'strength': return 'Strength';
            default: return 'Muscle Gain';
        }
    }

    function prettySplit(split) {
        return split === 'full_body' ? 'Full Body' : split === 'upper_lower' ? 'Upper/Lower' : 'Push/Pull/Legs';
    }

    function capital(s) { return s.charAt(0).toUpperCase() + s.slice(1); }

    function render(plan) {
        const text = planToText(plan);
        resultEl.textContent = text;
    }

    function saveToLocalStorage(input, plan) {
        try {
            localStorage.setItem('awp:lastInput', JSON.stringify(input));
            localStorage.setItem('awp:lastPlan', JSON.stringify(plan));
        } catch {}
    }

    function restoreFromLocalStorage() {
        try {
            const raw = localStorage.getItem('awp:lastInput');
            if (!raw) return;
            const input = JSON.parse(raw);
            // Restore key fields
            form.goal.value = input.goal;
            form.level.value = input.level;
            form.location.value = input.location;
            form.days.value = input.days;
            form.minutes.value = input.minutes;
            form.split.value = input.split;
            document.getElementById('daysValue').textContent = String(input.days);
            document.getElementById('minutesValue').textContent = String(input.minutes);

            // Equipment
            const boxes = Array.from(document.querySelectorAll('input[name="equipment"]'));
            for (const box of boxes) box.checked = input.equipment.includes(box.value);
            document.getElementById('warmup').checked = !!input.warmup;
            document.getElementById('cooldown').checked = !!input.cooldown;
            document.getElementById('notes').value = input.notes || '';

            const lastPlanRaw = localStorage.getItem('awp:lastPlan');
            if (lastPlanRaw) {
                const plan = JSON.parse(lastPlanRaw);
                render(plan);
            }
        } catch {}
    }

    form.addEventListener('submit', (e) => {
        e.preventDefault();
        const input = getFormData();
        const plan = generatePlanWithLocalHeuristics(input);
        render(plan);
        saveToLocalStorage(input, plan);
    });

    copyBtn.addEventListener('click', async () => {
        const text = resultEl.textContent || '';
        if (!text.trim()) return;
        try {
            await navigator.clipboard.writeText(text);
            toast('Plan copied to clipboard');
        } catch {
            toast('Copy failed');
        }
    });

    downloadBtn.addEventListener('click', () => {
        const planRaw = localStorage.getItem('awp:lastPlan');
        if (!planRaw) return;
        const blob = new Blob([planRaw], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'workout-plan.json';
        a.click();
        URL.revokeObjectURL(url);
    });

    printBtn.addEventListener('click', () => window.print());

    resetBtn.addEventListener('click', () => {
        form.reset();
        resultEl.textContent = '';
        localStorage.removeItem('awp:lastInput');
        localStorage.removeItem('awp:lastPlan');
        document.getElementById('daysValue').textContent = String(form.days.value);
        document.getElementById('minutesValue').textContent = String(form.minutes.value);
    });

    function toast(message) {
        const t = document.createElement('div');
        t.textContent = message;
        t.style.position = 'fixed';
        t.style.bottom = '18px';
        t.style.left = '50%';
        t.style.transform = 'translateX(-50%)';
        t.style.background = 'rgba(30,41,59,.95)';
        t.style.color = 'white';
        t.style.padding = '.55rem .8rem';
        t.style.borderRadius = '999px';
        t.style.border = '1px solid #334155';
        t.style.zIndex = '9999';
        document.body.appendChild(t);
        setTimeout(() => t.remove(), 1500);
    }

    // Initialize
    restoreFromLocalStorage();
})();


