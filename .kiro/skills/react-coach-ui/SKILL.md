# SKILL: React Coach UI Components

## Objectif
Fournir des patterns de composants React réutilisables et optimisés pour visualiser les données NFL, avec focus sur performance, accessibilité et interactivité.

---

## 1. Architecture Composants

### 1.1 Structure Recommandée
```
src/
├── components/
│   ├── heatmap/
│   │   ├── HeatmapMatchup.tsx          # Composant principal
│   │   ├── HeatmapMatchup.test.tsx     # Tests unitaires
│   │   ├── HeatmapMatchup.stories.tsx  # Storybook
│   │   └── types.ts                     # Types TypeScript
│   ├── timeseries/
│   │   ├── TimeSeriesClosing.tsx
│   │   └── ...
│   └── route-viz/
│       ├── RouteVisualization.tsx
│       └── ...
├── hooks/
│   ├── useNFLData.ts                    # Custom hook fetch DuckDB
│   └── useAnimation.ts                  # Gestion frame-by-frame
├── utils/
│   ├── nflGeometry.ts                   # Import logique géométrique
│   └── colorScales.ts                   # Échelles couleurs
└── types/
    └── nfl.ts                           # Types partagés
```

---

## 2. Composant Heatmap

### 2.1 Interface TypeScript
```typescript
// components/heatmap/types.ts
export interface ClosingRateData {
  routeType: string;        // 'slant', 'go', 'out', 'corner', 'post'
  cbAlignment: string;      // 'press', 'off', 'bail'
  avgClosingRate: number;   // yards/second (négatif = fermeture)
  stdClosingRate: number;
  nPlays: number;
  successRate: number;      // 0.0 - 1.0
}

export interface HeatmapMatchupProps {
  data: ClosingRateData[];
  onCellClick?: (route: string, alignment: string) => void;
  colorScale?: 'RdYlGn' | 'Viridis' | 'Plasma';
  showTooltip?: boolean;
}
```

### 2.2 Implémentation Plotly.js
```tsx
// components/heatmap/HeatmapMatchup.tsx
import React, { useMemo } from 'react';
import Plot from 'react-plotly.js';
import type { HeatmapMatchupProps, ClosingRateData } from './types';

export const HeatmapMatchup: React.FC<HeatmapMatchupProps> = ({
  data,
  onCellClick,
  colorScale = 'RdYlGn',
  showTooltip = true
}) => {
  // Transformation données en matrices 2D
  const { zMatrix, xLabels, yLabels } = useMemo(() => {
    const routes = [...new Set(data.map(d => d.routeType))].sort();
    const alignments = [...new Set(data.map(d => d.cbAlignment))].sort();
    
    const matrix: number[][] = alignments.map(alignment =>
      routes.map(route => {
        const cell = data.find(
          d => d.routeType === route && d.cbAlignment === alignment
        );
        return cell?.avgClosingRate ?? NaN;
      })
    );
    
    return {
      zMatrix: matrix,
      xLabels: routes,
      yLabels: alignments
    };
  }, [data]);

  // Génération texte hover
  const hoverText = useMemo(() => {
    return yLabels.map((alignment, i) =>
      xLabels.map((route, j) => {
        const cell = data.find(
          d => d.routeType === route && d.cbAlignment === alignment
        );
        if (!cell) return 'No data';
        
        return `
          <b>${route} vs ${alignment}</b><br>
          Closing Rate: ${cell.avgClosingRate.toFixed(2)} yd/s<br>
          Std Dev: ${cell.stdClosingRate.toFixed(2)}<br>
          Success: ${(cell.successRate * 100).toFixed(1)}%<br>
          Plays: ${cell.nPlays}
        `.trim();
      })
    );
  }, [data, xLabels, yLabels]);

  const handleClick = (event: any) => {
    if (!onCellClick || !event.points?.[0]) return;
    
    const point = event.points[0];
    const route = xLabels[point.x];
    const alignment = yLabels[point.y];
    
    onCellClick(route, alignment);
  };

  return (
    <div className="heatmap-container">
      <Plot
        data={[
          {
            z: zMatrix,
            x: xLabels,
            y: yLabels,
            type: 'heatmap',
            colorscale: colorScale,
            reversescale: true,  // Rouge = négatif (mauvais)
            hovertext: showTooltip ? hoverText : undefined,
            hoverinfo: showTooltip ? 'text' : 'none',
            colorbar: {
              title: 'Closing Rate<br>(yd/s)',
              titleside: 'right',
              tickmode: 'linear',
              tick0: -4,
              dtick: 1
            }
          }
        ]}
        layout={{
          title: {
            text: 'Window Erosion by Route & CB Alignment',
            font: { size: 20, family: 'Inter, sans-serif' }
          },
          xaxis: {
            title: 'Route Type',
            side: 'bottom',
            tickfont: { size: 14 }
          },
          yaxis: {
            title: 'CB Alignment',
            tickfont: { size: 14 }
          },
          margin: { l: 100, r: 150, t: 80, b: 80 },
          height: 500,
          paper_bgcolor: '#f9fafb',
          plot_bgcolor: '#ffffff'
        }}
        config={{
          displayModeBar: true,
          displaylogo: false,
          modeBarButtonsToRemove: ['lasso2d', 'select2d']
        }}
        onClick={handleClick}
        style={{ width: '100%', height: '100%' }}
      />
    </div>
  );
};
```

### 2.3 Tests Unitaires (Vitest + React Testing Library)
```tsx
// components/heatmap/HeatmapMatchup.test.tsx
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { HeatmapMatchup } from './HeatmapMatchup';

const mockData = [
  {
    routeType: 'slant',
    cbAlignment: 'press',
    avgClosingRate: -2.3,
    stdClosingRate: 0.8,
    nPlays: 45,
    successRate: 0.67
  },
  // ... more test data
];

describe('HeatmapMatchup', () => {
  it('renders heatmap with correct title', () => {
    render(<HeatmapMatchup data={mockData} />);
    expect(screen.getByText(/Window Erosion/i)).toBeInTheDocument();
  });

  it('calls onCellClick with correct arguments', async () => {
    const handleClick = vi.fn();
    render(<HeatmapMatchup data={mockData} onCellClick={handleClick} />);
    
    // Simulate Plotly click event
    const plot = screen.getByRole('img', { hidden: true });
    await userEvent.click(plot);
    
    expect(handleClick).toHaveBeenCalledWith('slant', 'press');
  });

  it('handles empty data gracefully', () => {
    render(<HeatmapMatchup data={[]} />);
    const plot = screen.getByRole('img', { hidden: true });
    expect(plot).toBeInTheDocument();
  });
});
```

---

## 3. Composant TimeSeries

### 3.1 Implémentation Recharts (Alternative Légère)
```tsx
// components/timeseries/TimeSeriesClosing.tsx
import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ReferenceArea,
  ResponsiveContainer
} from 'recharts';

interface TimeSeriesData {
  time: number;           // Secondes depuis pass_release
  distance: number;       // yards (WR-CB)
  closingRate: number;    // yards/s
  event?: string;         // 'ball_arrived', 'tackle', etc.
}

interface TimeSeriesClosingProps {
  data: TimeSeriesData[];
  highlightCloseWindow?: boolean;  // Zone rouge si distance < 3 yards
}

export const TimeSeriesClosing: React.FC<TimeSeriesClosingProps> = ({
  data,
  highlightCloseWindow = true
}) => {
  // Identifier périodes où fenêtre est fermée
  const closeWindowPeriods = highlightCloseWindow
    ? data.reduce<Array<{ start: number; end: number }>>((acc, point, i) => {
        if (point.distance < 3.0) {
          const lastPeriod = acc[acc.length - 1];
          if (lastPeriod && lastPeriod.end === data[i - 1]?.time) {
            lastPeriod.end = point.time;
          } else {
            acc.push({ start: point.time, end: point.time });
          }
        }
        return acc;
      }, [])
    : [];

  return (
    <div className="grid grid-cols-1 gap-6">
      {/* Graphique 1: Distance WR-CB */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4">
          WR-CB Separation Distance
        </h3>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="time" 
              label={{ value: 'Time Since Release (s)', position: 'bottom' }}
            />
            <YAxis 
              label={{ value: 'Distance (yards)', angle: -90, position: 'left' }}
            />
            <Tooltip 
              formatter={(value: number) => value.toFixed(2)}
              labelFormatter={(time) => `T+${time.toFixed(1)}s`}
            />
            <Legend />
            
            {/* Zones de fenêtre fermée */}
            {closeWindowPeriods.map((period, i) => (
              <ReferenceArea
                key={i}
                x1={period.start}
                x2={period.end}
                fill="red"
                fillOpacity={0.2}
                label="Close"
              />
            ))}
            
            {/* Seuil fenêtre fermée */}
            <Line 
              type="monotone" 
              dataKey={() => 3.0} 
              stroke="#ef4444" 
              strokeDasharray="5 5"
              dot={false}
              name="Close Threshold"
            />
            
            <Line
              type="monotone"
              dataKey="distance"
              stroke="#3b82f6"
              strokeWidth={2}
              dot={{ r: 4 }}
              name="WR-CB Distance"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Graphique 2: Closing Rate */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4">
          Window Closing Rate
        </h3>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="time" 
              label={{ value: 'Time Since Release (s)', position: 'bottom' }}
            />
            <YAxis 
              label={{ value: 'Rate (yd/s)', angle: -90, position: 'left' }}
            />
            <Tooltip />
            <Legend />
            
            {/* Ligne zéro (neutre) */}
            <Line 
              type="monotone" 
              dataKey={() => 0} 
              stroke="#9ca3af" 
              strokeDasharray="3 3"
              dot={false}
              name="Neutral"
            />
            
            <Line
              type="monotone"
              dataKey="closingRate"
              stroke="#10b981"
              strokeWidth={2}
              dot={{ r: 4 }}
              name="Closing Rate"
            />
            
            {/* Annotations événements */}
            {data
              .filter(d => d.event)
              .map((d, i) => (
                <text
                  key={i}
                  x={d.time}
                  y={0}
                  fill="#6b7280"
                  fontSize={12}
                  textAnchor="middle"
                >
                  {d.event}
                </text>
              ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
```

---

## 4. Hook Custom : Fetch Données DuckDB

### 4.1 Configuration Fetch MCP
```typescript
// hooks/useNFLData.ts
import { useState, useEffect } from 'react';
import type { ClosingRateData } from '@/types/nfl';

interface UseDuckDBQueryOptions {
  enabled?: boolean;
  refetchInterval?: number;
}

export function useDuckDBQuery<T>(
  query: string,
  options: UseDuckDBQueryOptions = {}
) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    if (!options.enabled) return;

    const fetchData = async () => {
      setLoading(true);
      try {
        // Appel MCP DuckDB (adapter selon votre setup)
        const response = await fetch('/api/duckdb/query', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ sql: query })
        });

        if (!response.ok) {
          throw new Error(`Query failed: ${response.statusText}`);
        }

        const result = await response.json();
        setData(result.data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err : new Error('Unknown error'));
      } finally {
        setLoading(false);
      }
    };

    fetchData();

    // Auto-refetch si configuré
    if (options.refetchInterval) {
      const interval = setInterval(fetchData, options.refetchInterval);
      return () => clearInterval(interval);
    }
  }, [query, options.enabled, options.refetchInterval]);

  return { data, loading, error };
}

// Hook spécialisé pour heatmap
export function useClosingRateHeatmap() {
  const query = `
    WITH route_metrics AS (
      SELECT 
        pff.pff_routeConcept AS route_type,
        pff.pff_coverageType AS cb_alignment,
        -- ... (voir spec.md REQ-DATA-2)
      FROM read_csv_auto('data/tracking/*.csv') t
      -- ... reste de la requête
    )
    SELECT * FROM route_metrics;
  `;

  return useDuckDBQuery<ClosingRateData[]>(query, { enabled: true });
}
```

---

## 5. Animations & Performance

### 5.1 Hook Animation Frame-by-Frame
```typescript
// hooks/useAnimation.ts
import { useState, useEffect, useCallback, useRef } from 'react';

interface AnimationControls {
  isPlaying: boolean;
  currentFrame: number;
  play: () => void;
  pause: () => void;
  reset: () => void;
  seekTo: (frame: number) => void;
}

export function useAnimation(
  totalFrames: number,
  fps: number = 10
): AnimationControls {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentFrame, setCurrentFrame] = useState(0);
  const animationRef = useRef<number>();

  const frameInterval = 1000 / fps;

  useEffect(() => {
    if (!isPlaying) return;

    let lastTimestamp = Date.now();
    
    const animate = () => {
      const now = Date.now();
      const elapsed = now - lastTimestamp;

      if (elapsed >= frameInterval) {
        setCurrentFrame(prev => {
          const next = prev + 1;
          if (next >= totalFrames) {
            setIsPlaying(false);
            return 0;
          }
          return next;
        });
        lastTimestamp = now;
      }

      animationRef.current = requestAnimationFrame(animate);
    };

    animationRef.current = requestAnimationFrame(animate);

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [isPlaying, totalFrames, frameInterval]);

  const play = useCallback(() => setIsPlaying(true), []);
  const pause = useCallback(() => setIsPlaying(false), []);
  const reset = useCallback(() => {
    setIsPlaying(false);
    setCurrentFrame(0);
  }, []);
  const seekTo = useCallback((frame: number) => {
    setCurrentFrame(Math.max(0, Math.min(frame, totalFrames - 1)));
  }, [totalFrames]);

  return { isPlaying, currentFrame, play, pause, reset, seekTo };
}
```

### 5.2 Optimisation Rendering (React.memo + useMemo)
```tsx
// Éviter re-renders inutiles des graphiques lourds
export const HeatmapMatchup = React.memo<HeatmapMatchupProps>(
  ({ data, onCellClick, colorScale }) => {
    // ... implementation
  },
  (prevProps, nextProps) => {
    // Custom comparison (shallow equality par défaut)
    return (
      prevProps.data === nextProps.data &&
      prevProps.colorScale === nextProps.colorScale
    );
  }
);
```

---

## 6. Accessibilité (A11y)

### 6.1 Checklist WCAG 2.1 AA
```tsx
// Bonnes pratiques à suivre:

// ✅ Contraste couleurs suffisant (ratio 4.5:1 minimum)
const COLOR_PALETTE = {
  success: '#10b981',    // WCAG AA compliant sur fond blanc
  warning: '#f59e0b',
  danger: '#ef4444',
  neutral: '#6b7280'
};

// ✅ Labels explicites pour screen readers
<Plot
  data={[...]}
  layout={{
    title: 'Window Erosion Heatmap',
    xaxis: { 
      title: 'Route Type',
      'aria-label': 'Horizontal axis showing route types'
    }
  }}
  config={{
    'aria-label': 'Interactive heatmap showing closing rates by route and alignment'
  }}
/>

// ✅ Navigation clavier
<button
  onClick={play}
  aria-label="Play animation"
  onKeyDown={(e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      play();
    }
  }}
>
  ▶ Play
</button>

// ✅ Focus visible
// Ajouter dans Tailwind config:
// ring-2 ring-blue-500 focus:outline-none
```

---

## 7. Style Guide (Tailwind CSS)

### 7.1 Classes Utilitaires Réutilisables
```typescript
// utils/classNames.ts
export const COMPONENT_STYLES = {
  card: 'bg-white rounded-lg shadow-md p-6 border border-gray-200',
  cardHover: 'hover:shadow-lg transition-shadow duration-200',
  
  heading: {
    h1: 'text-3xl font-bold text-gray-900',
    h2: 'text-2xl font-semibold text-gray-800',
    h3: 'text-lg font-medium text-gray-700'
  },
  
  button: {
    primary: 'bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700',
    secondary: 'bg-gray-200 text-gray-800 px-4 py-2 rounded hover:bg-gray-300'
  }
};
```

### 7.2 Theme Configuration
```javascript
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        nfl: {
          field: '#2d5016',     // Vert terrain
          endzone: '#003087',   // Bleu end zone
          offense: '#3b82f6',   // Bleu équipe offensive
          defense: '#ef4444'    // Rouge équipe défensive
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif']
      }
    }
  }
};
```

---

## 8. Exemples Complets

### 8.1 Page Cockpit Principale
```tsx
// pages/CockpitDashboard.tsx
import React, { useState } from 'react';
import { HeatmapMatchup } from '@/components/heatmap/HeatmapMatchup';
import { TimeSeriesClosing } from '@/components/timeseries/TimeSeriesClosing';
import { useClosingRateHeatmap } from '@/hooks/useNFLData';

export default function CockpitDashboard() {
  const { data: heatmapData, loading } = useClosingRateHeatmap();
  const [selectedMatchup, setSelectedMatchup] = useState<{
    route: string;
    alignment: string;
  } | null>(null);

  const handleHeatmapClick = (route: string, alignment: string) => {
    setSelectedMatchup({ route, alignment });
    // Déclencher fetch détails TimeSeries
  };

  if (loading) {
    return <div className="flex items-center justify-center h-screen">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
    </div>;
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <header className="mb-8">
        <h1 className="text-4xl font-bold text-gray-900">
          Coach Cockpit – Window Erosion Analysis
        </h1>
        <p className="text-gray-600 mt-2">
          Tactical insights for offensive coordinators
        </p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Heatmap */}
        <section>
          <HeatmapMatchup
            data={heatmapData || []}
            onCellClick={handleHeatmapClick}
          />
        </section>

        {/* TimeSeries (conditionnelle) */}
        {selectedMatchup && (
          <section>
            <TimeSeriesClosing
              data={/* fetch depuis selectedMatchup */}
            />
          </section>
        )}
      </div>
    </div>
  );
}
```

---

## 9. Checklist Pre-Commit

Avant de commit un composant React:
- [ ] Tests unitaires passent (`npm run test`)
- [ ] Linter sans erreurs (`npm run lint`)
- [ ] Types TypeScript corrects (`npm run type-check`)
- [ ] Accessibilité validée (axe DevTools)
- [ ] Performance vérifiée (React DevTools Profiler)
- [ ] Storybook story créé (si applicable)

---

**Version** : 1.0.0  
**Dernière MAJ** : 2026-10-21  
**Mainteneur** : Équipe Coach Cockpit NFL
