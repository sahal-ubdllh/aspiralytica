// frontend/src/api/auth.ts
import { BASE_URL } from './config';

interface User {
  id: number;
  name: string;
  email: string;
  bio?: string;
}

let currentUser: User | null = null;

export async function loginUser(email: string, password: string): Promise<User> {
  const response = await fetch(`${BASE_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'Login gagal');
  }
  const data = await response.json();
  currentUser = data.user;
  return data.user;
}

export async function registerUser(name: string, email: string, password: string): Promise<User> {
  const response = await fetch(`${BASE_URL}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, email, password }),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'Pendaftaran gagal');
  }
  const data = await response.json();
  return data.user;
}

export function getCurrentUser(): User | null {
  return currentUser;
}

export function logoutUser(): void {
  currentUser = null;
}