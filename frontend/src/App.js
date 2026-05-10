import React, { useState, useCallback, useEffect } from 'react';
import UploadForm from './components/UploadForm';
import ResultsGrid from './components/ResultsGrid';
import { Shield } from 'lucide-react';

const API_BASE_URL = (process.env.REACT_APP_API_URL || '').trim().replace(/\/$/, '');
const API_TIMEOUT_MS = 60000;

const withApiBase = (url) => {
  if (!url || typeof url !== 'string') {
    return url;
  }
  if (url.startsWith('http://') || url.startsWith('https://')) {
    return url;
  }
  return `${API_BASE_URL}${url.startsWith('/') ? url : `/${url}`}`;
};

const ANALYZE_ENDPOINT = withApiBase('/api/v1/analyze-trademark');

const normalizeResultsPayload = (payload) => {
  if (!payload || typeof payload !== 'object') {
    return payload;
  }
  const normalized = { ...payload };
  if (normalized.uploaded_image?.url) {
    normalized.uploaded_image = {
      ...normalized.uploaded_image,
      url: withApiBase(normalized.uploaded_image.url),
    };
  }
  if (Array.isArray(normalized.similar_trademarks)) {
    normalized.similar_trademarks = normalized.similar_trademarks.map((item) => ({
      ...item,
      image_url: withApiBase(item.image_url),
    }));
  }
  return normalized;
};

console.log('API Base URL:', API_BASE_URL || '(using relative /api/v1/* via dev proxy)');

function App() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleFileSelect = useCallback((file) => {
    console.log('File selected:', file ? file.name : 'None');
    setSelectedFile(file);
    setError(null);
    
    // Create preview URL
    if (file) {
      const url = URL.createObjectURL(file);
      setPreviewUrl(url);
      console.log('Preview URL created');
    } else {
      setPreviewUrl(null);
    }
  }, []);

  const clearPreview = useCallback(() => {
    setSelectedFile(null);
    setPreviewUrl((currentUrl) => {
      if (currentUrl) {
        URL.revokeObjectURL(currentUrl);
      }
      return null;
    });
    setResults(null);
    setError(null);
  }, []);

  const handleUpload = async () => {
    if (!selectedFile) {
      setError('Please select an image file first');
      console.warn('No file selected');
      return;
    }

    setLoading(true);
    setError(null);
    setResults(null);
    let timeoutId;

    console.log('Request started:', selectedFile.name);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('name', selectedFile.name.replace(/\.[^.]+$/, ''));
      formData.append('top_k', '5');

      console.log('Sending request to:', ANALYZE_ENDPOINT);

      const controller = new AbortController();
      timeoutId = setTimeout(() => controller.abort(), API_TIMEOUT_MS);

      const response = await fetch(ANALYZE_ENDPOINT, {
        method: 'POST',
        body: formData,
        signal: controller.signal,
      });

      console.log('Response received:', response.status);

      if (!response.ok) {
        let errorMessage = 'Failed to process image';
        // Read body once as text and attempt to parse JSON from it.
        const bodyText = await response.text().catch(() => null);
        if (bodyText) {
          try {
            const errorData = JSON.parse(bodyText);
            errorMessage = errorData.detail || errorData.message || errorMessage;
          } catch (e) {
            console.error('Error response text (non-JSON):', bodyText);
          }
        }
        throw new Error(errorMessage);
      }

      const data = await response.json();
      console.log('Response received successfully:', data);
      
      setResults(normalizeResultsPayload(data));
      console.log('Results updated');

    } catch (err) {
      console.error('Upload error:', err);
      
      if (err.name === 'AbortError') {
        setError('Request timed out. The server might be busy. Please try again.');
      } else if (err.message && err.message.includes('Failed to fetch')) {
        setError('Failed to connect to backend API. Confirm backend is running on port 8000 and CORS is configured.');
      } else {
        setError(err.message || 'An error occurred while processing the image');
      }
    } finally {
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
      setLoading(false);
      console.log('Request finished');
    }
  };

  const handleClear = () => {
    console.log('Clearing all data');
    clearPreview();
  };

  useEffect(() => {
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [previewUrl]);

  return (
    <div className="app" style={{
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      backgroundColor: '#f5f5f5',
    }}>
      {/* Header */}
      <header className="header" style={{
        backgroundColor: '#fff',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
        padding: '30px 20px',
        textAlign: 'center',
        borderBottom: '3px solid #4CAF50',
      }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
          <h1 style={{
            margin: '0 0 10px 0',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '15px',
            fontSize: '32px',
            color: '#333',
          }}>
            <Shield size={40} style={{ color: '#4CAF50' }} />
            AI Trademark Collision Detection
          </h1>
          <p style={{
            margin: '0',
            color: '#666',
            fontSize: '16px',
            maxWidth: '600px',
            marginLeft: 'auto',
            marginRight: 'auto',
          }}>
            Upload a trademark or logo image to detect potential collisions with existing trademarks 
            using advanced deep learning technology. Powered by ResNet50 image embeddings and FAISS similarity search.
          </p>
        </div>
      </header>

      {/* Main Content */}
      <main className="main-content" style={{
        flex: 1,
        padding: '30px 20px',
        maxWidth: '1200px',
        width: '100%',
        margin: '0 auto',
      }}>
        {error && (
          <div style={{
            marginBottom: '20px',
            padding: '14px 16px',
            borderRadius: '12px',
            background: '#fff1f1',
            color: '#9b1c1c',
            border: '1px solid #f5c2c7',
            fontWeight: 600,
          }}>
            {error}
          </div>
        )}

        {/* Upload Section */}
        <section className="upload-section" style={{
          backgroundColor: '#fff',
          padding: '30px',
          borderRadius: '8px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          marginBottom: '30px',
        }}>
          <h2 style={{
            marginTop: '0',
            marginBottom: '20px',
            color: '#333',
            fontSize: '24px',
          }}>
            Upload Trademark Image
          </h2>
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
          <section className="results-section" style={{
            backgroundColor: '#fff',
            padding: '30px',
            borderRadius: '8px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          }}>
            <ResultsGrid
              results={results}
              loading={loading}
            />
          </section>
        )}
      </main>

      {/* Footer */}
      <footer className="footer" style={{
        backgroundColor: '#333',
        color: '#fff',
        textAlign: 'center',
        padding: '20px',
        marginTop: 'auto',
        fontSize: '14px',
      }}>
        <p style={{ margin: 0 }}>
          AI Trademark Collision Detection System - Powered by Deep Learning
          <span style={{ margin: '0 1rem' }}>|</span>
          Advanced Visual Similarity Matching using CLIP/ResNet50 + FAISS
        </p>
        <p style={{ margin: '8px 0 0 0', fontSize: '12px', opacity: 0.8 }}>
          Dataset: {results?.dataset?.num_images || '—'} images across{' '}
          {results?.dataset?.num_brands || '—'} brands and{' '}
          {results?.dataset?.num_categories || '—'} categories
        </p>
      </footer>
    </div>
  );
}

export default App;
