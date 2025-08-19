(() => {
	const yearEl = document.getElementById('year');
	if (yearEl) yearEl.textContent = String(new Date().getFullYear());

	const form = document.getElementById('plannerForm');
	const output = document.getElementById('planOutput');
	const planDays = document.getElementById('planDays');
	const planNote = document.getElementById('planNote');

	function pickExercises(goal, equipmentSet) {
		const base = {
			push: ['Отжимания', 'Жим гантелей лёжа', 'Жим штанги лёжа', 'Жим на тренажёре'],
			pull: ['Тяга гантели в наклоне', 'Подтягивания', 'Тяга штанги в наклоне', 'Тяга горизонтального блока'],
			legs: ['Приседания', 'Выпады', 'Становая тяга', 'Жим ногами'],
			core: ['Планка', 'Скручивания', 'Подъёмы ног', 'Русские повороты']
		};

		function allow(name) {
			if (equipmentSet.has('none')) return ['Отжимания', 'Приседания', 'Планка', 'Скручивания', 'Подтягивания'].includes(name);
			if (name.includes('гантел') && equipmentSet.has('dumbbells')) return true;
			if (name.includes('штанг') && equipmentSet.has('barbell')) return true;
			if (name.includes('тренаж') && equipmentSet.has('machines')) return true;
			if (name.includes('Подтягив')) return equipmentSet.has('pullup');
			return ['Отжимания', 'Приседания', 'Планка', 'Скручивания'].includes(name);
		}

		const goalBias = {
			fatloss: { reps: '12–15', rest: '60–90с' },
			muscle: { reps: '8–12', rest: '90–120с' },
			strength: { reps: '3–6', rest: '120–180с' },
			endurance: { reps: '15–20', rest: '45–60с' }
		}[goal] || { reps: '8–12', rest: '90–120с' };

		const areas = ['push', 'pull', 'legs', 'core'];
		const plan = {};
		areas.forEach(area => {
			const filtered = base[area].filter(allow);
			plan[area] = (filtered.length ? filtered : base[area]).slice(0, 2).map(name => ({ name, ...goalBias }));
		});
		return plan;
	}

	function buildWeeklyStructure(days) {
		const presets = {
			2: ['Full Body A', 'Full Body B'],
			3: ['Push', 'Pull', 'Legs'],
			4: ['Upper', 'Lower', 'Push', 'Pull'],
			5: ['Upper', 'Lower', 'Push', 'Pull', 'Full Body'],
			6: ['Push', 'Pull', 'Legs', 'Upper', 'Lower', 'Core/Conditioning'],
			7: ['Push', 'Pull', 'Legs', 'Upper', 'Lower', 'Core/Conditioning', 'Mobility']
		};
		return presets[days] || presets[4];
	}

	function generatePlan({ goal, experience, days, equipment, notes }) {
		const eqSet = new Set(equipment);
		const exercises = pickExercises(goal, eqSet);
		const daysLayout = buildWeeklyStructure(days);
		return daysLayout.map((label, idx) => {
			const blocks = [];
			if (label.toLowerCase().includes('push')) blocks.push(...exercises.push);
			if (label.toLowerCase().includes('pull')) blocks.push(...exercises.pull);
			if (label.toLowerCase().includes('leg')) blocks.push(...exercises.legs);
			if (label.toLowerCase().includes('upper')) blocks.push(...exercises.push, ...exercises.pull);
			if (label.toLowerCase().includes('lower')) blocks.push(...exercises.legs);
			if (label.toLowerCase().includes('full')) blocks.push(...exercises.push, ...exercises.pull, ...exercises.legs);
			if (label.toLowerCase().includes('core')) blocks.push(...exercises.core);
			if (label.toLowerCase().includes('mobility')) blocks.push({ name: 'Мобилити + растяжка', reps: '10–15 мин', rest: '—' });
			const unique = [];
			const seen = new Set();
			for (const ex of blocks) {
				if (!seen.has(ex.name)) { unique.push(ex); seen.add(ex.name); }
			}
			return { day: idx + 1, label, items: unique.slice(0, 6) };
		});
	}

	function renderPlan(plan, noteText) {
		planDays.innerHTML = '';
		for (const day of plan) {
			const el = document.createElement('div');
			el.className = 'plan__day';
			el.innerHTML = `
				<h4>День ${day.day}: ${day.label}</h4>
				<ul class="plan__list">
					${day.items.map(it => `<li>${it.name} — ${it.reps} повт., отдых ${it.rest}</li>`).join('')}
				</ul>
			`;
			planDays.appendChild(el);
		}
		planNote.textContent = noteText;
		output.hidden = false;
		output.scrollIntoView({ behavior: 'smooth', block: 'start' });
	}

	form?.addEventListener('submit', (e) => {
		e.preventDefault();
		const goal = document.getElementById('goal').value;
		const experience = document.getElementById('experience').value;
		const days = Math.max(2, Math.min(7, Number(document.getElementById('days').value || 4)));
		const equipment = Array.from(document.querySelectorAll('input[name="equip"]:checked')).map(i => i.value);
		const notes = document.getElementById('notes').value?.trim() || '';

		const plan = generatePlan({ goal, experience, days, equipment, notes });
		const noteText = notes ? `Учитываем пожелания: ${notes}` : 'Совет: начните с лёгкой разминки 5–8 минут и завершайте заминкой.';
		renderPlan(plan, noteText);
	});
})();

