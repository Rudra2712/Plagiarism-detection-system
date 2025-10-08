import React, { useEffect, useState, useCallback } from 'react'
import UploadPage from './components/UploadPage.jsx'
import ResultsPage from './components/ResultsPage.jsx'

const RESULTS_KEY = 'plagiarism:results'
const UPLOAD_KEY = 'plagiarism:uploadInfo'

export default function App() {
  const [results, setResults] = useState(null)
  const [uploadInfo, setUploadInfo] = useState(null)

  // Load persisted state on mount
  useEffect(() => {
    try {
      const raw = localStorage.getItem(RESULTS_KEY)
      if (raw) setResults(JSON.parse(raw))
    } catch (e) {
      console.warn('Failed to parse persisted results', e)
    }
    try {
      const u = localStorage.getItem(UPLOAD_KEY)
      if (u) setUploadInfo(JSON.parse(u))
    } catch (e) {
      /* ignore */
    }
  }, [])

  // Persist whenever results change
  useEffect(() => {
    if (results) localStorage.setItem(RESULTS_KEY, JSON.stringify(results))
    else localStorage.removeItem(RESULTS_KEY)
  }, [results])

  useEffect(() => {
    if (uploadInfo) localStorage.setItem(UPLOAD_KEY, JSON.stringify(uploadInfo))
    else localStorage.removeItem(UPLOAD_KEY)
  }, [uploadInfo])

  const clearResults = useCallback(() => {
    setResults(null)
    setUploadInfo(null)
    try {
      localStorage.removeItem(RESULTS_KEY)
      localStorage.removeItem(UPLOAD_KEY)
    } catch (e) {
      /* ignore */
    }
  }, [])

  return (
    <div className="container mx-auto p-6">
      <header className="app-header">
        <div>
          <h1 className="app-title">Plagiarism Checker</h1>
          <p className="app-subtitle">Quick, language-agnostic code similarity scanning for assignments</p>
        </div>
      </header>

      <main className="mt-6">
        <UploadPage onUploaded={setUploadInfo} onResults={setResults} onClearResults={clearResults} uploadInfo={uploadInfo} />
        <ResultsPage results={results} onClear={clearResults} />
      </main>
    </div>
  )
}


