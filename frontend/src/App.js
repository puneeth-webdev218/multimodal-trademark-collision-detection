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
const TEXT_SEARCH_ENDPOINT = withApiBase('/api/v1/search-text');

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
  const [imageResults, setImageResults] = useState(null);
  const [imageLoading, setImageLoading] = useState(false);
  const [textQuery, setTextQuery] = useState('');
  const [textResults, setTextResults] = useState(null);
  const [textLoading, setTextLoading] = useState(false);
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
    setImageResults(null);
    setError(null);
  }, []);

  // Separate reset for the new text-to-image search path.
  const clearTextSearch = useCallback(() => {
    setTextQuery('');
    setTextResults(null);
    setError(null);
  }, []);

  const handleUpload = async () => {
    if (!selectedFile) {
      setError('Please select an image file first');
      console.warn('No file selected');
      return;
    }

    setImageLoading(true);
    setError(null);
    setImageResults(null);
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
      
      setImageResults(normalizeResultsPayload(data));
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
      setImageLoading(false);
      console.log('Request finished');
    }
  };

  // New text search handler that posts only a text query and reuses the existing FAISS index.
  const handleTextSearch = async () => {
    const trimmedQuery = textQuery.trim();
    if (!trimmedQuery) {
      setError('Please enter a text query first');
      return;
    }

    setTextLoading(true);
    setError(null);
    setTextResults(null);
    let timeoutId;

    try {
      const formData = new FormData();
      formData.append('query', trimmedQuery);
      formData.append('top_k', '5');

      const controller = new AbortController();
      timeoutId = setTimeout(() => controller.abort(), API_TIMEOUT_MS);

      const response = await fetch(TEXT_SEARCH_ENDPOINT, {
        method: 'POST',
        body: formData,
        signal: controller.signal,
      });

      if (!response.ok) {
        let errorMessage = 'Failed to process text query';
        const bodyText = await response.text().catch(() => null);
        if (bodyText) {
          try {
            const errorData = JSON.parse(bodyText);
            errorMessage = errorData.detail || errorData.message || errorMessage;
          } catch (e) {
            console.error('Text error response text (non-JSON):', bodyText);
          }
        }
        throw new Error(errorMessage);
      }

      const data = await response.json();
      setTextResults(normalizeResultsPayload(data));
    } catch (err) {
      console.error('Text search error:', err);

      if (err.name === 'AbortError') {
        setError('Text search timed out. The server might be busy. Please try again.');
      } else if (err.message && err.message.includes('Failed to fetch')) {
        setError('Failed to connect to backend API. Confirm backend is running on port 8000 and CORS is configured.');
      } else {
        setError(err.message || 'An error occurred while processing the text query');
      }
    } finally {
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
      setTextLoading(false);
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

        {/* Text Search Section */}
        <section className="upload-section" style={{
          backgroundColor: '#fff',
          padding: '30px',
          borderRadius: '8px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          marginBottom: '30px',
        }}>
          <h2 style={{
            marginTop: '0',
            marginBottom: '12px',
            color: '#333',
            fontSize: '24px',
          }}>
            Text-to-Image Search
          </h2>
          <p style={{ marginTop: '0', color: '#666', marginBottom: '18px' }}>
            Enter a concept, brand name, or description to search the existing FAISS index with CLIP text embeddings.
          </p>
          <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
            <input
              type="text"
              value={textQuery}
              onChange={(event) => setTextQuery(event.target.value)}
              placeholder="e.g. blue circular logo with stripes"
              disabled={textLoading}
              style={{
                flex: '1 1 320px',
                minWidth: '260px',
                padding: '12px 14px',
                borderRadius: '8px',
                border: '1px solid #d1d5db',
                fontSize: '16px',
              }}
            />
            <button
              type="button"
              onClick={handleTextSearch}
              disabled={textLoading}
              style={{
                padding: '12px 20px',
                backgroundColor: '#1f7a8c',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                cursor: textLoading ? 'not-allowed' : 'pointer',
                opacity: textLoading ? 0.7 : 1,
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
              }}
            >
              {textLoading ? 'Searching...' : 'Search by Text'}
            </button>
            <button
              type="button"
              onClick={clearTextSearch}
              disabled={textLoading}
              style={{
                padding: '12px 20px',
                backgroundColor: 'transparent',
                color: '#333',
                border: '1px solid #ddd',
                borderRadius: '8px',
                cursor: textLoading ? 'not-allowed' : 'pointer',
              }}
            >
              Clear Text
            </button>
          </div>
        </section>

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
            loading={imageLoading}
            error={error}
          />
        </section>

        {/* Text Results Section */}
        {(textLoading || textResults) && (
          <section className="results-section" style={{
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
              Text Search Results
            </h2>
            <ResultsGrid results={textResults} loading={textLoading} loadingLabel="Analyzing text query..." />
          </section>
        )}

        {/* Results Section */}
        {(imageLoading || imageResults) && (
          <section className="results-section" style={{
            backgroundColor: '#fff',
            padding: '30px',
            borderRadius: '8px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          }}>
            <ResultsGrid results={imageResults} loading={imageLoading} />
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
          Dataset: {imageResults?.dataset?.num_images || textResults?.dataset?.num_images || '—'} images across{' '}
          {imageResults?.dataset?.num_brands || textResults?.dataset?.num_brands || '—'} brands and{' '}
          {imageResults?.dataset?.num_categories || textResults?.dataset?.num_categories || '—'} categories
        </p>
      </footer>
    </div>
  );
}

export default App;
