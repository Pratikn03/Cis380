import { useState } from 'react';

/**
 * Result Card Component
 * 
 * Displays analysis results with confidence bars, expandable details,
 * and action buttons for the Sentifargo dashboard.
 */

type Severity = 'low' | 'medium' | 'high' | 'critical';

type ResultCardProps = {
  id: string;
  title: string;
  description: string;
  confidence: number; // 0-1
  severity: Severity;
  category: string;
  timestamp: string;
  details?: Record<string, unknown>;
  onAction?: (action: string, id: string) => void;
};

const severityColors: Record<Severity, { bg: string; border: string; text: string }> = {
  low: { bg: 'bg-green-50', border: 'border-green-200', text: 'text-green-700' },
  medium: { bg: 'bg-yellow-50', border: 'border-yellow-200', text: 'text-yellow-700' },
  high: { bg: 'bg-orange-50', border: 'border-orange-200', text: 'text-orange-700' },
  critical: { bg: 'bg-red-50', border: 'border-red-200', text: 'text-red-700' },
};

const severityIcons: Record<Severity, string> = {
  low: '✓',
  medium: '⚠',
  high: '⚡',
  critical: '🚨',
};

export default function ResultCard({
  id,
  title,
  description,
  confidence,
  severity,
  category,
  timestamp,
  details,
  onAction,
}: ResultCardProps) {
  const [expanded, setExpanded] = useState(false);
  
  const colors = severityColors[severity];
  const confidencePercent = Math.round(confidence * 100);
  
  // Determine confidence bar color based on value
  const getConfidenceColor = (conf: number): string => {
    if (conf >= 0.9) return 'bg-green-500';
    if (conf >= 0.7) return 'bg-blue-500';
    if (conf >= 0.5) return 'bg-yellow-500';
    return 'bg-red-500';
  };
  
  return (
    <div
      className={`rounded-lg border-2 ${colors.border} ${colors.bg} overflow-hidden transition-all duration-200 hover:shadow-md`}
    >
      {/* Header */}
      <div className="p-4">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl">{severityIcons[severity]}</span>
            <div>
              <h3 className="font-semibold text-ink text-lg">{title}</h3>
              <div className="flex items-center gap-2 mt-1">
                <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${colors.text} ${colors.bg} border ${colors.border}`}>
                  {severity.toUpperCase()}
                </span>
                <span className="text-xs text-gray-500">{category}</span>
              </div>
            </div>
          </div>
          <span className="text-xs text-gray-400">{timestamp}</span>
        </div>
        
        <p className="mt-3 text-sm text-gray-600 line-clamp-2">{description}</p>
        
        {/* Confidence Bar */}
        <div className="mt-4">
          <div className="flex justify-between items-center mb-1">
            <span className="text-xs font-medium text-gray-500">Confidence</span>
            <span className="text-xs font-bold text-gray-700">{confidencePercent}%</span>
          </div>
          <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
            <div
              className={`h-full ${getConfidenceColor(confidence)} transition-all duration-500 ease-out`}
              style={{ width: `${confidencePercent}%` }}
            />
          </div>
        </div>
      </div>
      
      {/* Expandable Details */}
      {details && Object.keys(details).length > 0 && (
        <>
          <button
            onClick={() => setExpanded(!expanded)}
            className="w-full px-4 py-2 text-xs font-medium text-gray-500 bg-white/50 hover:bg-white/80 transition-colors flex items-center justify-center gap-1"
          >
            {expanded ? 'Hide Details' : 'Show Details'}
            <svg
              className={`w-4 h-4 transition-transform ${expanded ? 'rotate-180' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          
          {expanded && (
            <div className="px-4 py-3 bg-white/30 border-t border-gray-200">
              <div className="space-y-2">
                {Object.entries(details).map(([key, value]) => (
                  <div key={key} className="flex justify-between text-xs">
                    <span className="text-gray-500 capitalize">{key.replace(/_/g, ' ')}</span>
                    <span className="text-gray-700 font-medium">
                      {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
      
      {/* Action Buttons */}
      {onAction && (
        <div className="px-4 py-3 bg-white/50 border-t border-gray-200 flex gap-2">
          <button
            onClick={() => onAction('investigate', id)}
            className="flex-1 px-3 py-1.5 text-xs font-medium text-white bg-blue-600 rounded hover:bg-blue-700 transition-colors"
          >
            Investigate
          </button>
          <button
            onClick={() => onAction('dismiss', id)}
            className="flex-1 px-3 py-1.5 text-xs font-medium text-gray-600 bg-gray-100 rounded hover:bg-gray-200 transition-colors"
          >
            Dismiss
          </button>
          <button
            onClick={() => onAction('escalate', id)}
            className="flex-1 px-3 py-1.5 text-xs font-medium text-white bg-red-600 rounded hover:bg-red-700 transition-colors"
          >
            Escalate
          </button>
        </div>
      )}
    </div>
  );
}


/**
 * Confidence Bar Component
 * 
 * Standalone confidence indicator with multiple display modes.
 */

type ConfidenceBarProps = {
  value: number; // 0-1
  label?: string;
  showValue?: boolean;
  size?: 'sm' | 'md' | 'lg';
  variant?: 'bar' | 'ring' | 'gauge';
  animated?: boolean;
};

export function ConfidenceBar({
  value,
  label,
  showValue = true,
  size = 'md',
  variant = 'bar',
  animated = true,
}: ConfidenceBarProps) {
  const percent = Math.round(value * 100);
  
  const sizeClasses = {
    sm: { bar: 'h-1', text: 'text-xs', ring: 'w-12 h-12', stroke: 3 },
    md: { bar: 'h-2', text: 'text-sm', ring: 'w-16 h-16', stroke: 4 },
    lg: { bar: 'h-3', text: 'text-base', ring: 'w-24 h-24', stroke: 6 },
  };
  
  type ColorKey = 'green' | 'blue' | 'yellow' | 'red';
  
  const getColor = (v: number): ColorKey => {
    if (v >= 0.9) return 'green';
    if (v >= 0.7) return 'blue';
    if (v >= 0.5) return 'yellow';
    return 'red';
  };
  
  const color = getColor(value);
  const colorClasses: Record<ColorKey, { bg: string; text: string; stroke: string }> = {
    green: { bg: 'bg-green-500', text: 'text-green-600', stroke: 'stroke-green-500' },
    blue: { bg: 'bg-blue-500', text: 'text-blue-600', stroke: 'stroke-blue-500' },
    yellow: { bg: 'bg-yellow-500', text: 'text-yellow-600', stroke: 'stroke-yellow-500' },
    red: { bg: 'bg-red-500', text: 'text-red-600', stroke: 'stroke-red-500' },
  };
  
  const classes = colorClasses[color];
  const sizes = sizeClasses[size];
  
  if (variant === 'ring') {
    const circumference = 2 * Math.PI * 45;
    const offset = circumference - (value * circumference);
    
    return (
      <div className="flex flex-col items-center gap-1">
        {label && <span className={`${sizes.text} text-gray-500`}>{label}</span>}
        <div className={`relative ${sizes.ring}`}>
          <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
            <circle
              cx="50"
              cy="50"
              r="45"
              fill="none"
              stroke="#e5e7eb"
              strokeWidth={sizes.stroke}
            />
            <circle
              cx="50"
              cy="50"
              r="45"
              fill="none"
              className={`${classes.stroke} ${animated ? 'transition-all duration-1000 ease-out' : ''}`}
              strokeWidth={sizes.stroke}
              strokeLinecap="round"
              strokeDasharray={circumference}
              strokeDashoffset={offset}
            />
          </svg>
          {showValue && (
            <div className={`absolute inset-0 flex items-center justify-center ${sizes.text} font-bold ${classes.text}`}>
              {percent}%
            </div>
          )}
        </div>
      </div>
    );
  }
  
  if (variant === 'gauge') {
    const rotation = (value * 180) - 90;
    
    return (
      <div className="flex flex-col items-center gap-1">
        {label && <span className={`${sizes.text} text-gray-500`}>{label}</span>}
        <div className={`relative ${sizes.ring}`}>
          <svg className="w-full h-full" viewBox="0 0 100 60">
            {/* Background arc */}
            <path
              d="M 10 50 A 40 40 0 0 1 90 50"
              fill="none"
              stroke="#e5e7eb"
              strokeWidth={sizes.stroke}
              strokeLinecap="round"
            />
            {/* Foreground arc */}
            <path
              d="M 10 50 A 40 40 0 0 1 90 50"
              fill="none"
              className={`${classes.stroke} ${animated ? 'transition-all duration-1000 ease-out' : ''}`}
              strokeWidth={sizes.stroke}
              strokeLinecap="round"
              strokeDasharray={`${value * 126} 126`}
            />
            {/* Needle */}
            <line
              x1="50"
              y1="50"
              x2="50"
              y2="20"
              stroke="#374151"
              strokeWidth="2"
              strokeLinecap="round"
              className={animated ? 'transition-transform duration-1000 ease-out' : ''}
              style={{ transformOrigin: '50px 50px', transform: `rotate(${rotation}deg)` }}
            />
            <circle cx="50" cy="50" r="4" fill="#374151" />
          </svg>
          {showValue && (
            <div className={`absolute bottom-0 left-1/2 -translate-x-1/2 ${sizes.text} font-bold ${classes.text}`}>
              {percent}%
            </div>
          )}
        </div>
      </div>
    );
  }
  
  // Default bar variant
  return (
    <div className="w-full">
      {(label || showValue) && (
        <div className="flex justify-between items-center mb-1">
          {label && <span className={`${sizes.text} text-gray-500`}>{label}</span>}
          {showValue && <span className={`${sizes.text} font-bold ${classes.text}`}>{percent}%</span>}
        </div>
      )}
      <div className={`w-full ${sizes.bar} bg-gray-200 rounded-full overflow-hidden`}>
        <div
          className={`h-full ${classes.bg} ${animated ? 'transition-all duration-500 ease-out' : ''}`}
          style={{ width: `${percent}%` }}
        />
      </div>
    </div>
  );
}


/**
 * Result Card List Component
 * 
 * Renders a list of result cards with filtering and sorting.
 */

type ResultListProps = {
  results: ResultCardProps[];
  onAction?: (action: string, id: string) => void;
  sortBy?: 'confidence' | 'severity' | 'timestamp';
  filterSeverity?: Severity[];
};

export function ResultCardList({
  results,
  onAction,
  sortBy = 'timestamp',
  filterSeverity,
}: ResultListProps) {
  const severityOrder: Record<Severity, number> = {
    critical: 4,
    high: 3,
    medium: 2,
    low: 1,
  };
  
  let filteredResults = results;
  
  // Filter by severity
  if (filterSeverity && filterSeverity.length > 0) {
    filteredResults = results.filter(r => filterSeverity.includes(r.severity));
  }
  
  // Sort results
  const sortedResults = [...filteredResults].sort((a, b) => {
    switch (sortBy) {
      case 'confidence':
        return b.confidence - a.confidence;
      case 'severity':
        return severityOrder[b.severity] - severityOrder[a.severity];
      case 'timestamp':
      default:
        return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
    }
  });
  
  if (sortedResults.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        <p className="text-lg">No results found</p>
        <p className="text-sm mt-2">Try adjusting your filters</p>
      </div>
    );
  }
  
  return (
    <div className="space-y-4">
      {sortedResults.map((result) => (
        <ResultCard
          key={result.id}
          {...result}
          onAction={onAction}
        />
      ))}
    </div>
  );
}
