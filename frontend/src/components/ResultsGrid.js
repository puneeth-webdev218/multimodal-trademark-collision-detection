import React from 'react';
import { AlertTriangle, CheckCircle, AlertOctagon, Shield } from 'lucide-react';
import SimilarityScore from './SimilarityScore';

/**
 * ResultsGrid Component
 * Displays similar trademarks and collision risk assessment
 */
function ResultsGrid({ results, loading }) {
  // Loading state
  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
        <p>Analyzing trademark similarity...</p>
      </div>
    );
  }

  // No results
  if (!results) {
    return null;
  }

  const { uploaded_image, similar_trademarks, collision_risk } = results;

  // Get risk icon
  const getRiskIcon = (riskLevel) => {
    switch (riskLevel?.toUpperCase()) {
      case 'HIGH':
        return <AlertOctagon size={24} />;
      case 'MEDIUM':
        return <AlertTriangle size={24} />;
      case 'LOW':
      default:
        return <CheckCircle size={24} />;
    }
  };

  // Get risk class
  const getRiskClass = (riskLevel) => {
    switch (riskLevel?.toUpperCase()) {
      case 'HIGH':
        return 'high';
      case 'MEDIUM':
        return 'medium';
      case 'LOW':
      default:
        return 'low';
    }
  };

  return (
    <div>
      {/* Header */}
      <div className="results-header">
        <h2>Analysis Results</h2>
        {collision_risk && (
          <div className={`risk-badge ${getRiskClass(collision_risk.risk_level)}`}>
            {getRiskIcon(collision_risk.risk_level)}
            {collision_risk.risk_level} Risk
          </div>
        )}
      </div>

      {/* Uploaded Image and Risk Info */}
      {uploaded_image && (
        <div className="uploaded-image-display">
          <img 
            src={uploaded_image.url || uploaded_image.path}
            alt="Uploaded trademark"
            className="uploaded-img"
            onError={(e) => {
              e.target.style.display = 'none';
            }}
          />
          <div className="risk-info">
            <h3>
              <Shield size={20} style={{ marginRight: '0.5rem', verticalAlign: 'middle' }} />
              Collision Risk Assessment
            </h3>
            {collision_risk && (
              <>
                <div className={`risk-badge ${getRiskClass(collision_risk.risk_level)}`}>
                  {getRiskIcon(collision_risk.risk_level)}
                  {collision_risk.risk_level} Collision Risk
                </div>
                <p>{collision_risk.message}</p>
                {collision_risk.similarity_score > 0 && (
                  <p>
                    Highest Similarity: <strong>{(collision_risk.similarity_score * 100).toFixed(1)}%</strong>
                  </p>
                )}
              </>
            )}
          </div>
        </div>
      )}

      {/* Similar Trademarks */}
      {similar_trademarks && similar_trademarks.length > 0 ? (
        <>
          <h3 style={{ marginBottom: '1rem', fontSize: '1rem', fontWeight: 600 }}>
            Top {similar_trademarks.length} Similar Trademarks
          </h3>
          <div className="results-grid">
            {similar_trademarks.map((trademark, index) => (
              <TrademarkCard 
                key={index} 
                trademark={trademark} 
                rank={index + 1}
              />
            ))}
          </div>
        </>
      ) : (
        <div className="no-results">
          <div className="no-results-icon">
            <CheckCircle size={64} />
          </div>
          <h3>No Similar Trademarks Found</h3>
          <p>Your trademark appears to be unique in our database.</p>
        </div>
      )}
    </div>
  );
}

/**
 * TrademarkCard Component
 * Displays individual similar trademark result
 */
function TrademarkCard({ trademark, rank }) {
  const similarity = trademark.similarity_percentage || (trademark.similarity_score * 100);
  
  return (
    <div className="trademark-card">
      <div className="card-image-container">
        <span className="card-rank">#{rank}</span>
        <img 
          src={trademark.image_url || `/api/trademarks/${trademark.image_name}`}
          alt={trademark.image_name}
          className="card-image"
          onError={(e) => {
            e.target.src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"><rect fill="%23f0f0f0" width="100" height="100"/><text x="50" y="50" text-anchor="middle" dy="0.3em" font-family="sans-serif" font-size="12" fill="%23999">No Image</text></svg>';
          }}
        />
      </div>
      <div className="card-body">
        <div className="card-name" title={trademark.image_name}>
          {trademark.image_name}
        </div>
        <SimilarityScore score={similarity} />
      </div>
    </div>
  );
}

export default ResultsGrid;
