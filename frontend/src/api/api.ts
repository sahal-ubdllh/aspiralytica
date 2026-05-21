// frontend/src/api/api.ts
import { BASE_URL } from './config';

export interface AnalysisResult {
  id: number;
  text: string;
  sentiment: string;
  intent: string;
  priority: string;
  is_sarcasm: boolean;
  status: string;
  created_at: string;
}

export async function analyzeReport(text: string): Promise<AnalysisResult> {
  const response = await fetch(`${BASE_URL}/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'Server error');
  }
  return response.json();
}

export async function getHistory(): Promise<AnalysisResult[]> {
  const response = await fetch(`${BASE_URL}/history`);
  if (!response.ok) throw new Error('Gagal mengambil riwayat');
  return response.json();
}

export async function getReport(id: number): Promise<AnalysisResult> {
  const response = await fetch(`${BASE_URL}/history/${id}`);
  if (!response.ok) throw new Error('Laporan tidak ditemukan');
  return response.json();
}

export async function deleteReport(id: number): Promise<void> {
  const response = await fetch(`${BASE_URL}/history/${id}`, {
    method: 'DELETE',
  });
  if (!response.ok) throw new Error('Gagal menghapus laporan');
}