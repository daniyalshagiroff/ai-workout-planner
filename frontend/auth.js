async function apiMe() {
  const res = await fetch('/api/v2/auth/me', { credentials: 'include' });
  return res.json();
}

async function apiRegister(email, password) {
  const params = new URLSearchParams({ email, password });
  const res = await fetch('/api/v2/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: params.toString(),
  });
  if (!res.ok) throw new Error((await res.json()).detail || 'Register failed');
  return res.json();
}

async function apiLogin(email, password) {
  const params = new URLSearchParams({ email, password });
  const res = await fetch('/api/v2/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: params.toString(),
    credentials: 'include',
  });
  if (!res.ok) throw new Error((await res.json()).detail || 'Login failed');
  return res.json();
}

async function apiLogout() {
  await fetch('/api/v2/auth/logout', { method: 'POST', credentials: 'include' });
}

function show(el) { el.style.display = ''; }
function hide(el) { el.style.display = 'none'; }

function attachAuthUI() {
  const btnRegister = document.getElementById('btn-register');
  const btnLogin = document.getElementById('btn-login');
  const btnProfile = document.getElementById('btn-profile');
  const btnLogout = document.getElementById('btn-logout');

  const modalRegister = document.getElementById('modal-register');
  const modalLogin = document.getElementById('modal-login');

  const regEmail = document.getElementById('reg-email');
  const regPassword = document.getElementById('reg-password');
  const regSubmit = document.getElementById('reg-submit');

  const loginEmail = document.getElementById('login-email');
  const loginPassword = document.getElementById('login-password');
  const loginSubmit = document.getElementById('login-submit');

  function openModal(m) { m.style.display = 'block'; }
  function closeModals() { modalRegister.style.display = 'none'; modalLogin.style.display = 'none'; }

  document.querySelectorAll('.modal .modal-close').forEach(b => b.addEventListener('click', closeModals));

  // Navigate to dedicated pages
  btnRegister.addEventListener('click', () => { window.location.href = '/static/register.html'; });
  btnLogin.addEventListener('click', () => { window.location.href = '/static/login.html'; });
  btnProfile.addEventListener('click', () => { window.location.href = '/static/profile.html'; });
  btnLogout.addEventListener('click', async () => { await apiLogout(); window.location.href = '/'; });

  regSubmit.addEventListener('click', async () => {
    try {
      await apiRegister(regEmail.value, regPassword.value);
      closeModals();
      alert('Registered. Now log in.');
    } catch (e) { alert(e.message); }
  });

  loginSubmit.addEventListener('click', async () => {
    try {
      await apiLogin(loginEmail.value, loginPassword.value);
      closeModals();
      await refreshAuthBar();
    } catch (e) { alert(e.message); }
  });

  async function refreshAuthBar() {
    const me = await apiMe();
    if (me.authenticated) {
      hide(btnRegister); hide(btnLogin);
      show(btnProfile); show(btnLogout);
    } else {
      show(btnRegister); show(btnLogin);
      hide(btnProfile); hide(btnLogout);
    }
  }

  refreshAuthBar();
}

document.addEventListener('DOMContentLoaded', attachAuthUI);


