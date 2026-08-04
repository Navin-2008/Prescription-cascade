import { useEffect, useState } from 'react'
import './App.css'
import { checkHealth, ingestRecord, analyzeCascade } from './api.js'

const DEFAULT_RECORD = {
  patient_id: 'p1',
  clinical_note: 'Patient started amlodipine and later developed ankle swelling.',
  prescriptions: [
    { drug_name: 'Amlodipine', start_date: '2026-06-01' },
    { drug_name: 'Furosemide', start_date: '2026-06-30' },
  ],
  symptoms: [{ symptom_name: 'Ankle swelling', onset_date: '2026-06-21' }],
}

function App() {
  const [record, setRecord] = useState(DEFAULT_RECORD)
  const [status, setStatus] = useState('Ready to connect')
  const [loading, setLoading] = useState(false)
  const [response, setResponse] = useState(null)
  const [error, setError] = useState('')
  const [health, setHealth] = useState(false)

  useEffect(() => {
    healthCheck()
  }, [])

  const updateField = (field, value) => {
    setRecord((current) => ({ ...current, [field]: value }))
  }

  const updatePrescription = (index, field, value) => {
    setRecord((current) => {
      const prescriptions = [...current.prescriptions]
      prescriptions[index] = { ...prescriptions[index], [field]: value }
      return { ...current, prescriptions }
    })
  }

  const updateSymptom = (index, field, value) => {
    setRecord((current) => {
      const symptoms = [...current.symptoms]
      symptoms[index] = { ...symptoms[index], [field]: value }
      return { ...current, symptoms }
    })
  }

  const addPrescription = () => {
    setRecord((current) => ({
      ...current,
      prescriptions: [...current.prescriptions, { drug_name: '', start_date: '' }],
    }))
  }

  const removePrescription = (index) => {
    setRecord((current) => ({
      ...current,
      prescriptions: current.prescriptions.filter((_, position) => position !== index),
    }))
  }

  const addSymptom = () => {
    setRecord((current) => ({
      ...current,
      symptoms: [...current.symptoms, { symptom_name: '', onset_date: '' }],
    }))
  }

  const removeSymptom = (index) => {
    setRecord((current) => ({
      ...current,
      symptoms: current.symptoms.filter((_, position) => position !== index),
    }))
  }

  const getErrorMessage = (error) => {
    if (!error) return 'Unknown error'
    if (error.response?.data) return JSON.stringify(error.response.data)
    return error.message || String(error)
  }

  const healthCheck = async () => {
    setError('')
    setStatus('Checking backend health...')
    setLoading(true)

    try {
      await checkHealth()
      setHealth(true)
      setStatus('Backend is healthy')
    } catch (err) {
      setHealth(false)
      setError(getErrorMessage(err))
      setStatus('Backend health check failed')
    } finally {
      setLoading(false)
    }
  }

  const handleIngest = async () => {
    setError('')
    setStatus('Sending ingest request...')
    setLoading(true)

    try {
      const data = await ingestRecord(record)
      setResponse(data)
      setStatus('Record ingested successfully')
    } catch (err) {
      setResponse(null)
      setError(getErrorMessage(err))
      setStatus('Ingest request failed')
    } finally {
      setLoading(false)
    }
  }

  const handleAnalyze = async () => {
    setError('')
    setStatus('Sending analyze request...')
    setLoading(true)

    try {
      const data = await analyzeCascade(record)
      setResponse(data)
      setStatus('Analysis completed')
    } catch (err) {
      setResponse(null)
      setError(getErrorMessage(err))
      setStatus('Analyze request failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app-shell">
      <header className="page-header">
        <div>
          <h1>Prescription Cascade Frontend</h1>
          <p>Use this UI to ingest patient records and analyze prescription cascades.</p>
        </div>

        <div className="health-card">
          <div>
            <span className={`badge ${health ? 'online' : 'offline'}`}>
              {health ? 'Backend online' : 'Backend offline'}
            </span>
            <div className="status-text">{status}</div>
          </div>
          <button type="button" onClick={healthCheck} disabled={loading}>
            Refresh health
          </button>
        </div>
      </header>

      <main className="panel-grid">
        <section className="panel">
          <h2>Patient record</h2>

          <div className="form-group">
            <label htmlFor="patient_id">Patient ID</label>
            <input
              id="patient_id"
              value={record.patient_id}
              onChange={(event) => updateField('patient_id', event.target.value)}
              placeholder="Enter patient ID"
            />
          </div>

          <div className="form-group">
            <label htmlFor="clinical_note">Clinical note</label>
            <textarea
              id="clinical_note"
              rows="4"
              value={record.clinical_note}
              onChange={(event) => updateField('clinical_note', event.target.value)}
              placeholder="Optional clinical note"
            />
          </div>

          <div className="row">
            <div className="column">
              <h3>Prescriptions</h3>
              {record.prescriptions.map((prescription, index) => (
                <div className="array-row" key={`prescription-${index}`}>
                  <input
                    value={prescription.drug_name}
                    onChange={(event) => updatePrescription(index, 'drug_name', event.target.value)}
                    placeholder="Drug name"
                  />
                  <input
                    type="date"
                    value={prescription.start_date}
                    onChange={(event) => updatePrescription(index, 'start_date', event.target.value)}
                  />
                  <button type="button" className="text-button" onClick={() => removePrescription(index)}>
                    Remove
                  </button>
                </div>
              ))}
              <button type="button" className="action-button secondary" onClick={addPrescription}>
                Add prescription
              </button>
            </div>

            <div className="column">
              <h3>Symptoms</h3>
              {record.symptoms.map((symptom, index) => (
                <div className="array-row" key={`symptom-${index}`}>
                  <input
                    value={symptom.symptom_name}
                    onChange={(event) => updateSymptom(index, 'symptom_name', event.target.value)}
                    placeholder="Symptom"
                  />
                  <input
                    type="date"
                    value={symptom.onset_date}
                    onChange={(event) => updateSymptom(index, 'onset_date', event.target.value)}
                  />
                  <button type="button" className="text-button" onClick={() => removeSymptom(index)}>
                    Remove
                  </button>
                </div>
              ))}
              <button type="button" className="action-button secondary" onClick={addSymptom}>
                Add symptom
              </button>
            </div>
          </div>
        </section>

        <section className="panel">
          <h2>Actions</h2>
          <div className="button-group">
            <button type="button" className="action-button" onClick={handleIngest} disabled={loading}>
              Ingest record
            </button>
            <button type="button" className="action-button primary" onClick={handleAnalyze} disabled={loading}>
              Analyze cascade
            </button>
          </div>

          <div className="info-box">
            <p>
              The backend expects JSON payloads only. Clinical note is optional; arrays can be empty.
            </p>
            <p>
              Use <code>/api/ingest/record</code> to save data and <code>/api/cascade/analyze</code> to get the cascade result.
            </p>
          </div>

          {loading && <div className="message info">Waiting for backend response…</div>}
          {error && <div className="message error">{error}</div>}

          {response && (
            <div className="message success">
              <strong>Last API response</strong>
              <pre>{JSON.stringify(response, null, 2)}</pre>
            </div>
          )}
        </section>
      </main>
    </div>
  )
}

export default App
