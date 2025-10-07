import React, { useState } from 'react'
import UploadPage from './components/UploadPage.jsx'
import ResultsPage from './components/ResultsPage.jsx'
import Navbar from './components/Navbar.jsx'

export default function App() {
  const [results, setResults] = useState(null)
  const [uploadInfo, setUploadInfo] = useState(null)

  return (
    <div className="container mx-auto p-4">
      <Navbar />
      <UploadPage onUploaded={setUploadInfo} onResults={setResults} />
      <ResultsPage results={results} />
    </div>
  )
}


