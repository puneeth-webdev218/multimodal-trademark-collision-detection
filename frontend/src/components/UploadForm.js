import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, X, Search, AlertCircle } from 'lucide-react';

/**
 * UploadForm Component
 * Handles file selection and upload with proper async handling
 */
function UploadForm({ 
  selectedFile, 
  previewUrl, 
  onFileSelect, 
  onUpload, 
  onClear, 
  loading, 
  error 
}) {
  // Handle file drop
  const onDrop = useCallback((acceptedFiles) => {
    if (acceptedFiles && acceptedFiles.length > 0) {
      const file = acceptedFiles[0];
      console.log('File selected:', file.name, file.size);
      onFileSelect(file);
    }
  }, [onFileSelect]);

  // Configure dropzone
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.jpeg', '.jpg', '.png', '.gif', '.bmp', '.webp']
    },
    maxFiles: 1,
    maxSize: 50 * 1024 * 1024, // 50MB
    disabled: loading
  });

  // Format file size
  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  return (
    <div>
      {/* Dropzone */}
      {!selectedFile && (
        <div 
          {...getRootProps()} 
          className={`dropzone ${isDragActive ? 'active' : ''}`}
          style={{
            border: isDragActive ? '3px solid #4CAF50' : '2px dashed #999',
            padding: '40px',
            textAlign: 'center',
            cursor: loading ? 'not-allowed' : 'pointer',
            opacity: loading ? 0.6 : 1,
          }}
        >
          <input {...getInputProps()} />
          <div className="dropzone-icon">
            <Upload size={48} />
          </div>
          <h3>
            {isDragActive 
              ? 'Drop your image here' 
              : 'Drag & drop your trademark image'}
          </h3>
          <p>
            or click to browse • Supports JPG, PNG, GIF, BMP, WebP up to 50MB
          </p>
        </div>
      )}

      {/* Preview */}
      {selectedFile && previewUrl && (
        <div className="preview-container" style={{
          display: 'flex',
          gap: '20px',
          marginTop: '20px',
          padding: '20px',
          border: '1px solid #ddd',
          borderRadius: '8px',
          backgroundColor: '#f9f9f9',
        }}>
          <img 
            src={previewUrl} 
            alt="Preview" 
            className="preview-image"
            style={{
              maxWidth: '300px',
              maxHeight: '300px',
              objectFit: 'contain',
              borderRadius: '4px',
            }}
          />
          <div className="preview-info" style={{ flex: 1 }}>
            <h4>{selectedFile.name}</h4>
            <p>
              Size: {formatFileSize(selectedFile.size)}
              <br />
              Type: {selectedFile.type || 'Unknown'}
            </p>
            <div className="btn-group" style={{ display: 'flex', gap: '10px', marginTop: '10px' }}>
              <button 
                className="btn btn-primary"
                onClick={onUpload}
                disabled={loading}
                style={{
                  padding: '10px 20px',
                  backgroundColor: '#4CAF50',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: loading ? 'not-allowed' : 'pointer',
                  opacity: loading ? 0.6 : 1,
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                }}
              >
                {loading ? (
                  <>
                    <div className="spinner" style={{ 
                      width: 16, 
                      height: 16, 
                      borderWidth: 2,
                      border: '2px solid #f3f3f3',
                      borderTop: '2px solid #4CAF50',
                      borderRadius: '50%',
                      animation: 'spin 1s linear infinite',
                    }} />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <Search size={16} />
                    Check for Collisions
                  </>
                )}
              </button>
              <button 
                className="btn btn-outline"
                onClick={onClear}
                disabled={loading}
                style={{
                  padding: '10px 20px',
                  backgroundColor: 'transparent',
                  color: '#333',
                  border: '1px solid #ddd',
                  borderRadius: '4px',
                  cursor: loading ? 'not-allowed' : 'pointer',
                  opacity: loading ? 0.6 : 1,
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                }}
              >
                <X size={16} />
                Clear
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="error-message" style={{
          marginTop: '20px',
          padding: '15px',
          backgroundColor: '#ffebee',
          color: '#c62828',
          borderRadius: '4px',
          display: 'flex',
          gap: '10px',
          alignItems: 'flex-start',
        }}>
          <AlertCircle size={20} style={{ marginTop: '2px', flexShrink: 0 }} />
          <span>{error}</span>
        </div>
      )}

      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}

export default UploadForm;
