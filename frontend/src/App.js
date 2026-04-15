import React, { useState, useCallback } from 'react';
import UploadForm from './components/UploadForm';
import ResultsGrid from './components/ResultsGrid';
import { Shield, Github } from 'lucide-react';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function App() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleFileSelect = useCallback((file) => {
    setSelectedFile(file);
    setError(null);
    
    // Create preview URL
    if (file) {
      const url = URL.createObjectURL(file);
      setPreviewUrl(url);
    } else {
      setPreviewUrl(null);
    }
  }, []);

  const handleUpload = async () => {
    if (!selectedFile) {
      setError('Please select an image file first');
      return;
    }

    setLoading(true);
    setError(null);
    setResults(null);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('top_k', '5');

      const response = await fetch(`${API_BASE_URL}/api/v1/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to process image');
      }

      const data = await response.json();
      setResults(data);
    } catch (err) {
      console.error('Upload error:', err);
      setError(err.message || 'An error occurred while processing the image');
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setSelectedFile(null);
    setPreviewUrl(null);
    setResults(null);
    setError(null);
  };

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <h1>
          <Shield size={32} />
          AI Trademark Collision Detection
        </h1>
        <p>
          Upload a trademark or logo image to detect potential collisions with existing trademarks 
          using advanced deep learning technology.
        </p>
      </header>

      {/* Main Content */}
      <main className="main-content">
        {/* Upload Section */}
        <section className="upload-section">
          <h2>Upload Trademark Image</h2>
          <UploadForm
            selectedFile={selectedFile}
            previewUrl={previewUrl}
            onFileSelect={handleFileSelect}
            onUpload={handleUpload}
            onClear={handleClear}
            loading={loading}
            error={error}
          />
        </section>

        {/* Results Section */}
        {(loading || results) && (
          <section className="results-section">
            <ResultsGrid
              results={results}
              loading={loading}
            />
          </section>
        )}
      </main>

      {/* Footer */}
      <footer className="footer">
        <p>
          AI Trademark Collision Detection System - Powered by Deep Learning
          <span style={{ margin: '0 1rem' }}>|</span>
          <a 
            href="https://github.com" 
            target="_blank" 
            rel="noopener noreferrer"
            style={{ color: 'inherit', textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}
          >
            <Github size={14} /> GitHub
          </a>
        </p>
      </footer>
    </div>
  );
}

export default App;
