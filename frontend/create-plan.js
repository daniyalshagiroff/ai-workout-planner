async function me() {
  const res = await fetch('/api/v2/auth/me', { credentials: 'include' });
  return res.json();
}

function getProgramContext() {
  const programId = window.localStorage.getItem('program_id');
  return programId ? parseInt(programId, 10) : null;
}

function setProgramContext(id) {
  window.localStorage.setItem('program_id', String(id));
}

function getWeekDayContext() {
  const week = parseInt(document.getElementById('week-number').value, 10);
  const day = parseInt(document.getElementById('day-of-week').value, 10);
  return { week, day };
}

async function createExercise(owner_user_id, name, muscle_group, equipment, is_global) {
  const params = new URLSearchParams({
    name,
    muscle_group,
    equipment: equipment || '',
    is_global: is_global ? 'true' : 'false',
  });
  if (owner_user_id) params.append('owner_user_id', String(owner_user_id));
  const res = await fetch('/api/v2/exercises', { method: 'POST', body: params });
  if (!res.ok) throw new Error('Create exercise failed');
  return res.json();
}

async function createProgram(owner_user_id, title, description) {
  const params = new URLSearchParams({ owner_user_id: String(owner_user_id), title, description: description || '' });
  const res = await fetch('/api/v2/programs', { method: 'POST', body: params });
  if (!res.ok) throw new Error('Create program failed');
  return res.json();
}

async function ensureWeek(program_id, week_number) {
  const res = await fetch(`/api/v2/programs/${program_id}/weeks/${week_number}`, { method: 'POST' });
  if (!res.ok) throw new Error('Ensure week failed');
  return res.json();
}

async function ensureDay(program_id, week_number, day_of_week) {
  const res = await fetch(`/api/v2/programs/${program_id}/weeks/${week_number}/days/${day_of_week}`, { method: 'POST' });
  if (!res.ok) throw new Error('Ensure day failed');
  return res.json();
}

async function addDayExercise(program_id, week_number, day_of_week, exercise_id, position, notes) {
  const params = new URLSearchParams({ exercise_id: String(exercise_id), position: String(position), notes: notes || '' });
  const res = await fetch(`/api/v2/programs/${program_id}/weeks/${week_number}/days/${day_of_week}/exercises`, { method: 'POST', body: params });
  if (!res.ok) throw new Error('Add day exercise failed');
  return res.json();
}

async function addPlannedSet(program_id, week_number, day_of_week, position, set_number, reps, weight, rpe, rest_seconds) {
  const params = new URLSearchParams({
    set_number: String(set_number),
    reps: String(reps),
    weight: weight ? String(weight) : '',
    rpe: rpe ? String(rpe) : '',
    rest_seconds: rest_seconds ? String(rest_seconds) : '',
  });
  const res = await fetch(`/api/v2/programs/${program_id}/weeks/${week_number}/days/${day_of_week}/exercises/${position}/planned-sets`, { method: 'POST', body: params });
  if (!res.ok) throw new Error('Add planned set failed');
  return res.json();
}

function wire() {
  const exRes = document.getElementById('ex-result');
  const pgRes = document.getElementById('pg-result');
  const wdRes = document.getElementById('wd-result');
  const pdeRes = document.getElementById('pde-result');
  const psRes = document.getElementById('ps-result');

  document.getElementById('btn-create-exercise').addEventListener('click', async () => {
    try {
      const scope = document.getElementById('ex-scope').value;
      const info = await me();
      const userId = info.authenticated ? info.user.id : null;
      const ex = await createExercise(
        scope === 'user' ? userId : null,
        document.getElementById('ex-name').value,
        document.getElementById('ex-muscle').value,
        document.getElementById('ex-equipment').value,
        scope === 'global'
      );
      exRes.textContent = `Exercise created: id=${ex.id}, name=${ex.name || ex.exercise_name || ''}`;
    } catch (e) { exRes.textContent = e.message; }
  });

  document.getElementById('btn-create-program').addEventListener('click', async () => {
    try {
      const info = await me();
      if (!info.authenticated) { pgRes.textContent = 'Please log in'; return; }
      const p = await createProgram(info.user.id, document.getElementById('pg-title').value, document.getElementById('pg-desc').value);
      setProgramContext(p.id);
      pgRes.textContent = `Program created: id=${p.id}, title=${p.title || p.name || ''}`;
    } catch (e) { pgRes.textContent = e.message; }
  });

  document.getElementById('btn-ensure-week').addEventListener('click', async () => {
    try {
      const programId = getProgramContext(); if (!programId) { wdRes.textContent = 'Create/select program first'; return; }
      const { week } = getWeekDayContext();
      const w = await ensureWeek(programId, week);
      wdRes.textContent = `Week ensured: id=${w.id}, number=${w.week_number}`;
    } catch (e) { wdRes.textContent = e.message; }
  });

  document.getElementById('btn-ensure-day').addEventListener('click', async () => {
    try {
      const programId = getProgramContext(); if (!programId) { wdRes.textContent = 'Create/select program first'; return; }
      const { week, day } = getWeekDayContext();
      const d = await ensureDay(programId, week, day);
      wdRes.textContent = `Day ensured: id=${d.id}, dow=${d.day_of_week}`;
    } catch (e) { wdRes.textContent = e.message; }
  });

  document.getElementById('btn-add-day-exercise').addEventListener('click', async () => {
    try {
      const programId = getProgramContext(); if (!programId) { pdeRes.textContent = 'Create/select program first'; return; }
      const { week, day } = getWeekDayContext();
      const exId = parseInt(document.getElementById('pde-exercise-id').value, 10);
      const pos = parseInt(document.getElementById('pde-position').value, 10);
      const notes = document.getElementById('pde-notes').value;
      const r = await addDayExercise(programId, week, day, exId, pos, notes);
      pdeRes.textContent = `Day exercise added: id=${r.id}, position=${r.position}`;
    } catch (e) { pdeRes.textContent = e.message; }
  });

  document.getElementById('btn-add-planned-set').addEventListener('click', async () => {
    try {
      const programId = getProgramContext(); if (!programId) { psRes.textContent = 'Create/select program first'; return; }
      const { week, day } = getWeekDayContext();
      const position = parseInt(document.getElementById('ps-position').value, 10);
      const setn = parseInt(document.getElementById('ps-set-number').value, 10);
      const reps = parseInt(document.getElementById('ps-reps').value, 10);
      const weight = parseFloat(document.getElementById('ps-weight').value);
      const rpe = parseFloat(document.getElementById('ps-rpe').value);
      const rest = parseInt(document.getElementById('ps-rest').value, 10);
      const r = await addPlannedSet(programId, week, day, position, setn, reps, isNaN(weight)? undefined: weight, isNaN(rpe)? undefined: rpe, isNaN(rest)? undefined: rest);
      psRes.textContent = `Planned set added: id=${r.id}, set=${r.set_number}`;
    } catch (e) { psRes.textContent = e.message; }
  });
}

document.addEventListener('DOMContentLoaded', wire);


