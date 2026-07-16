const API_URL = 'http://192.168.66.74:8000';

async function login(email, password) {
  try {
    const formData = new FormData();
    formData.append('username', email);
    formData.append('password', password);

    const response = await fetch(`${API_URL}/login`, {
      method: 'POST',
      body: formData
    });

    const data = await response.json();

    if (!response.ok) {
      return { success: false, error: data.detail || 'Login failed' };
    }

    localStorage.setItem('token', data.access_token);
    localStorage.setItem('user', JSON.stringify(data.user));
    return { success: true };
  } catch (err) {
    return { success: false, error: 'Could not connect to server.' };
  }
}

async function register(fullName, email, password) {
  try {
    const response = await fetch(`${API_URL}/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ full_name: fullName, email, password })
    });

    const data = await response.json();

    if (!response.ok) {
      return { success: false, error: data.detail || 'Registration failed' };
    }

    localStorage.setItem('token', data.access_token);
    localStorage.setItem('user', JSON.stringify(data.user));
    return { success: true };
  } catch (err) {
    return { success: false, error: 'Could not connect to server.' };
  }
}

function logout() {
  localStorage.removeItem('token');
  localStorage.removeItem('user');
  window.location.href = 'login.html';
}

function getToken() {
  return localStorage.getItem('token');
}

function getUser() {
  const user = localStorage.getItem('user');
  return user ? JSON.parse(user) : null;
}

function requireAuth() {
  if (!getToken()) {
    window.location.href = 'login.html';
    return false;
  }
  return true;
}