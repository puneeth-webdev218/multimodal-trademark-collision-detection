import React from 'react';

/**
 * SimilarityScore Component
 * Displays a visual similarity score with progress bar
 */
function SimilarityScore({ score }) {
  // Determine risk level based on score
  const getRiskLevel = (score) => {
    if (score >= 85) return 'high';
    if (score >= 70) return 'medium';
    return 'low';
  };

  const riskLevel = getRiskLevel(score);
  
  return (
    <div className="similarity-score">
      <div className="score-bar">
        <div 
          className={`score-fill ${riskLevel}`}
          style={{ width: `${Math.min(score, 100)}%` }}
        />
      </div>
      <span className={`score-value ${riskLevel}`}>
        {score.toFixed(1)}%
      </span>
    </div>
  );
}

export default SimilarityScore;
