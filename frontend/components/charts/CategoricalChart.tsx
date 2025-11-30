'use client'

import dynamic from 'next/dynamic'
import { useMemo } from 'react'

// Dynamically import Plotly to avoid SSR issues
const Plot = dynamic(() => import('react-plotly.js'), { ssr: false })

interface CategoricalChartProps {
  data: Array<{
    level: string
    gender: string
    n: number | string
    pct: number | string
  }>
  variableName: string
  chartType: 'stacked' | 'grouped'
}

export default function CategoricalChart({ data, variableName, chartType }: CategoricalChartProps) {
  const plotData = useMemo(() => {
    // Get unique levels and genders
    const levels = [...new Set(data.map(d => d.level))]
    const genders = [...new Set(data.map(d => d.gender))]
    
    if (chartType === 'stacked') {
      // Stacked bar chart
      return genders.map(gender => {
        const genderData = data.filter(d => d.gender === gender)
        
        return {
          x: levels,
          y: levels.map(level => {
            const item = genderData.find(d => d.level === level)
            return item ? (typeof item.pct === 'number' ? item.pct : 0) : 0
          }),
          name: gender,
          type: 'bar' as const,
          stackgroup: 'one',
        }
      })
    } else {
      // Grouped bar chart
      return levels.map(level => {
        const levelData = data.filter(d => d.level === level)
        
        return {
          x: genders,
          y: genders.map(gender => {
            const item = levelData.find(d => d.gender === gender)
            return item ? (typeof item.pct === 'number' ? item.pct : 0) : 0
          }),
          name: level,
          type: 'bar' as const,
        }
      })
    }
  }, [data, chartType])

  const layout = useMemo(() => ({
    title: `${variableName} - ${chartType === 'stacked' ? 'Stacked' : 'Grouped'} Bar Chart by Gender`,
    xaxis: {
      title: chartType === 'stacked' ? 'Category Level' : 'Gender',
    },
    yaxis: {
      title: 'Percentage (%)',
      range: [0, 100],
    },
    showlegend: true,
    legend: {
      orientation: 'h',
      y: -0.2,
    },
    margin: { t: 60, b: 60, l: 60, r: 60 },
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    barmode: chartType === 'stacked' ? 'stack' : 'group',
  }), [variableName, chartType])

  const config = {
    displayModeBar: true,
    displaylogo: false,
    modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d'],
    responsive: true,
  }

  if (plotData.length === 0 || plotData.every(series => series.y.every(val => val === 0))) {
    return (
      <div className="w-full h-96 flex items-center justify-center bg-muted/20 rounded-lg">
        <div className="text-center text-muted-foreground">
          <p className="text-sm">No data available for visualization</p>
          <p className="text-xs mt-1">Data may be suppressed due to small cell sizes</p>
        </div>
      </div>
    )
  }

  return (
    <div className="w-full h-96">
      <Plot
        data={plotData}
        layout={layout}
        config={config}
        style={{ width: '100%', height: '100%' }}
      />
    </div>
  )
}
