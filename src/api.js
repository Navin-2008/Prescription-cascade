import axios from 'axios';

const BASE_URL = ''

export async function checkHealth() {
  const res = await axios.get(`${BASE_URL}/healthz`);
  return res.data;
}

export async function ingestRecord(patientRecord) {
  const res = await axios.post(`${BASE_URL}/api/ingest/record`, patientRecord);
  return res.data;
}

export async function analyzeCascade(patientRecord) {
  const res = await axios.post(`${BASE_URL}/api/cascade/analyze`, patientRecord);
  return res.data;
}
