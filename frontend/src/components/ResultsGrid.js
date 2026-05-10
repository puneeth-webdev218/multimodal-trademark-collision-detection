import React from 'react';
import { AlertTriangle, AlertCircle, CheckCircle, TrendingUp } from 'lucide-react';

/**
 * ResultsGrid Component
 * Displays similar trademarks with proper result formatting
 */
function ResultsGrid({ results, loading }) {
  if (loading) {
    return (
      <div style={{
        textAlign: 'center',
        padding: '40px',
        color: '#666',
      }}>
        <div style={{
          display: 'inline-block',
          width: '40px',
          height: '40px',
          border: '4px solid #f3f3f3',
          borderTop: '4px solid #4CAF50',
          borderRadius: '50%',
          animation: 'spin 1s linear infinite',
        }} />
        <p style={{ marginTop: '20px', fontSize: '16px' }}>
          Analyzing trademark image...
        </p>
      </div>
    );
  }

  if (!results) {
    return null;
  }

  const { 
    similar_trademarks = [], 
    collision_risk = {}, 
    dataset = {},
    uploaded_image = {},
    processing_time_seconds = 0,
  } = results;

  const getRiskColor = (riskLevel) => {
    switch (riskLevel?.toUpperCase()) {
      case 'HIGH':
        return '#d32f2f';
      case 'MEDIUM':
        return '#f57c00';
      case 'LOW':
        return '#388e3c';
      default:
        return '#666';
    }
  };

  const getRiskIcon = (riskLevel) => {
    switch (riskLevel?.toUpperCase()) {
      case 'HIGH':
        return <AlertTriangle size={24} />;
      case 'MEDIUM':
        return <AlertCircle size={24} />;
      case 'LOW':
        return <CheckCircle size={24} />;
      default:
        return <TrendingUp size={24} />;
    }
  };

  return (
    <div style={{ marginTop: '30px' }}>
      {/* Collision Risk Summary */}
      <div style={{
        padding: '20px',
        backgroundColor: getRiskColor(collision_risk.risk_level),
        color: 'white',
        borderRadius: '8px',
        marginBottom: '30px',
      }}>
        <div style={{ display: 'flex', gap: '15px', alignItems: 'center' }}>
          <div style={{ fontSize: '32px' }}>
            {getRiskIcon(collision_risk.risk_level)}
          </div>
          <div style={{ flex: 1 }}>
            <h3 style={{ margin: '0 0 8px 0' }}>
              {collision_risk.risk_level || 'UNKNOWN'} Collision Risk
            </h3>
            <p style={{ margin: 0, opacity: 0.9 }}>
              {collision_risk.message}
            </p>
            <p style={{ margin: '8px 0 0 0', fontSize: '12px', opacity: 0.8 }}>
              Similarity Score: {((collision_risk.similarity_score || 0) * 100).toFixed(1)}%
            </p>
          </div>
        </div>
      </div>

      {uploaded_image?.url && (
        <div style={{
          display: 'flex',
          gap: '16px',
          alignItems: 'center',
          marginBottom: '30px',
          padding: '16px',
          border: '1px solid #e0e0e0',
          borderRadius: '8px',
          backgroundColor: '#fcfcfc',
        }}>
          <img
            src={uploaded_image.url}
            alt={uploaded_image.filename || 'Uploaded logo'}
            style={{ width: '96px', height: '96px', objectFit: 'contain', borderRadius: '8px', backgroundColor: '#fff', border: '1px solid #eee' }}
          />
          <div>
            <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>Uploaded image</div>
            <div style={{ fontSize: '14px', color: '#666' }}>{uploaded_image.filename || uploaded_image.path || 'Uploaded file'}</div>
          </div>
        </div>
      )}

      {/* Dataset Stats */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
        gap: '15px',
        marginBottom: '30px',
      }}>
        <div style={{
          padding: '15px',
          backgroundColor: '#f5f5f5',
          borderRadius: '4px',
          textAlign: 'center',
        }}>
          <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#4CAF50' }}>
            {dataset.num_images || 0}
          </div>
          <div style={{ fontSize: '12px', color: '#666', marginTop: '5px' }}>
            Total Images
          </div>
        </div>
        <div style={{
          padding: '15px',
          backgroundColor: '#f5f5f5',
          borderRadius: '4px',
          textAlign: 'center',
        }}>
          <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#2196F3' }}>
            {dataset.num_brands || 0}
          </div>
          <div style={{ fontSize: '12px', color: '#666', marginTop: '5px' }}>
            Brands
          </div>
        </div>
        <div style={{
          padding: '15px',
          backgroundColor: '#f5f5f5',
          borderRadius: '4px',
          textAlign: 'center',
        }}>
          <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#FF9800' }}>
            {dataset.num_categories || 0}
          </div>
          <div style={{ fontSize: '12px', color: '#666', marginTop: '5px' }}>
            Categories
          </div>
        </div>
        {processing_time_seconds > 0 && (
          <div style={{
            padding: '15px',
            backgroundColor: '#f5f5f5',
            borderRadius: '4px',
            textAlign: 'center',
          }}>
            <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#9C27B0' }}>
              {processing_time_seconds.toFixed(2)}s
            </div>
            <div style={{ fontSize: '12px', color: '#666', marginTop: '5px' }}>
              Processing Time
            </div>
          </div>
        )}
      </div>

      {/* Similar Trademarks */}
      {similar_trademarks && similar_trademarks.length > 0 ? (
        <div>
          <h3 style={{ marginTop: '30px', marginBottom: '20px' }}>
            Top {similar_trademarks.length} Similar Trademarks
          </h3>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))',
            gap: '20px',
          }}>
            {similar_trademarks.map((trademark, idx) => (
              <div key={idx} style={{
                border: '1px solid #ddd',
                borderRadius: '8px',
                padding: '15px',
                backgroundColor: '#fafafa',
                transition: 'transform 0.2s, box-shadow 0.2s',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-5px)';
                e.currentTarget.style.boxShadow = '0 8px 16px rgba(0,0,0,0.1)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = 'none';
              }}>
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: '10px',
                }}>
                  <span style={{
                    fontWeight: 'bold',
                    fontSize: '18px',
                    color: '#4CAF50',
                  }}>
                    #{trademark.rank}
                  </span>
                  <span style={{
                    fontSize: '14px',
                    fontWeight: 'bold',
                    color: '#2196F3',
                  }}>
                    {trademark.similarity_percentage}%
                  </span>
                </div>
                
                <p style={{ margin: '10px 0', fontSize: '14px', wordBreak: 'break-word' }}>
                  <strong>Brand:</strong> {trademark.brand_name || 'N/A'}
                </p>

                {trademark.image_url && (
                  <img
                    src={trademark.image_url}
                    alt={trademark.image_name || trademark.brand_name || 'Similar logo'}
                    style={{
                      width: '100%',
                      height: '140px',
                      objectFit: 'contain',
                      borderRadius: '6px',
                      border: '1px solid #ececec',
                      backgroundColor: '#fff',
                      marginBottom: '10px',
                    }}
                  />
                )}
                
                {trademark.category && (
                  <p style={{ margin: '8px 0', fontSize: '13px', color: '#666' }}>
                    <strong>Category:</strong> {trademark.category}
                  </p>
                )}
                
                <p style={{ margin: '8px 0', fontSize: '12px', color: '#999', wordBreak: 'break-word' }}>
                  <strong>Image:</strong> {trademark.image_name}
                </p>
                
                <div style={{
                  marginTop: '12px',
                  padding: '10px',
                  backgroundColor: '#f0f0f0',
                  borderRadius: '4px',
                  fontSize: '12px',
                }}>
                  <div style={{ marginBottom: '5px' }}>
                    <strong>Similarity Score:</strong> {(trademark.similarity_score || 0).toFixed(4)}
                  </div>
                  <div>
                    <strong>Distance:</strong> {(trademark.distance || 0).toFixed(6)}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div style={{
          padding: '40px',
          textAlign: 'center',
          color: '#666',
          backgroundColor: '#f9f9f9',
          borderRadius: '4px',
        }}>
          <p>No similar trademarks found above detection threshold.</p>
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

export default ResultsGrid;
