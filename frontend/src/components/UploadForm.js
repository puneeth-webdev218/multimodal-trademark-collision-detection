import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, Image, X, Search, AlertCircle } from 'lucide-react';

/**
 * UploadForm Component
 * Handles file selection via drag-and-drop or click
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
      onFileSelect(acceptedFiles[0]);
    }
  }, [onFileSelect]);

  // Configure dropzone
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.jpeg', '.jpg', '.png', '.gif', '.bmp', '.webp']
    },
    maxFiles: 1,
    maxSize: 10 * 1024 * 1024, // 10MB
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
            or click to browse • Supports JPG, PNG, GIF, BMP, WebP up to 10MB
          </p>
        </div>
      )}

      {/* Preview */}
      {selectedFile && previewUrl && (
        <div className="preview-container">
          <img 
            src={previewUrl} 
            alt="Preview" 
            className="preview-image"
          />
          <div className="preview-info">
            <h4>{selectedFile.name}</h4>
            <p>
              Size: {formatFileSize(selectedFile.size)}
              <br />
              Type: {selectedFile.type || 'Unknown'}
            </p>
            <div className="btn-group">
              <button 
                className="btn btn-primary"
                onClick={onUpload}
                disabled={loading}
              >
                {loading ? (
                  <>
                    <div className="spinner" style={{ width: 16, height: 16, borderWidth: 2 }} />
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
        <div className="error-message">
          <AlertCircle size={20} />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
}

export default UploadForm;
