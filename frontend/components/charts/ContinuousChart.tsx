'use client'

import dynamic from 'next/dynamic'
import { useMemo } from 'react'

// Dynamically import Plotly to avoid SSR issues
const Plot = dynamic(() => import('react-plotly.js'), { ssr: false })

interface ContinuousChartProps {
  data: Array<{
    gender: string
    n: number | string
    mean: number | string
    sd: number | string
    median: number | string
    iqr: number | string
    min: number | string
    max: number | string
  }>
  variableName: string
  chartType: 'boxplot' | 'histogram'
}

export default function ContinuousChart({ data, variableName, chartType }: ContinuousChartProps) {
  const plotData = useMemo(() => {
    if (chartType === 'boxplot') {
      // For boxplot, we need to simulate data from summary statistics
      // This is a simplified approach - in practice, you'd want to use the actual data
      const boxData = data
        .filter(d => typeof d.n === 'number' && d.n > 0 && typeof d.mean === 'number' && typeof d.sd === 'number')
        .map(d => {
          const n = d.n as number
          const mean = d.mean as number
          const sd = d.sd as number
          
          // Generate synthetic data points for visualization
          // This is just for demonstration - real implementation would use actual data
          const syntheticData = Array.from({ length: Math.min(n, 100) }, () => {
            // Simple normal distribution approximation
            return mean + (Math.random() - 0.5) * sd * 2
          })
          
          return {
            y: syntheticData,
            name: d.gender,
            type: 'box' as const,
            boxpoints: 'outliers' as const,
            jitter: 0.3,
            pointpos: -1.8,
          }
        })
      
      return boxData
    } else {
      // Histogram
      const histData = data
        .filter(d => typeof d.n === 'number' && d.n > 0 && typeof d.mean === 'number' && typeof d.sd === 'number')
        .map(d => {
          const n = d.n as number
          const mean = d.mean as number
          const sd = d.sd as number
          
          // Generate synthetic histogram data
          const bins = 20
          const min = (d.min as number) || mean - 3 * sd
          const max = (d.max as number) || mean + 3 * sd
          const binSize = (max - min) / bins
          
          const histogram = Array.from({ length: bins }, (_, i) => {
            const binStart = min + i * binSize
            const binEnd = min + (i + 1) * binSize
            const binCenter = (binStart + binEnd) / 2
            
            // Approximate normal distribution
            const density = Math.exp(-0.5 * Math.pow((binCenter - mean) / sd, 2)) / (sd * Math.sqrt(2 * Math.PI))
            const count = density * n * binSize
            
            return {
              x: binCenter,
              y: count,
            }
          })
          
          return {
            x: histogram.map(h => h.x),
            y: histogram.map(h => h.y),
            name: d.gender,
            type: 'bar' as const,
            opacity: 0.7,
          }
        })
      
      return histData
    }
  }, [data, chartType])

  const layout = useMemo(() => ({
    title: `${variableName} - ${chartType === 'boxplot' ? 'Box Plot' : 'Histogram'} by Gender`,
    xaxis: {
      title: chartType === 'boxplot' ? 'Gender' : variableName,
    },
    yaxis: {
      title: chartType === 'boxplot' ? variableName : 'Count',
    },
    showlegend: true,
    legend: {
      orientation: 'h',
      y: -0.2,
    },
    margin: { t: 60, b: 60, l: 60, r: 60 },
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
  }), [variableName, chartType])

  const config = {
    displayModeBar: true,
    displaylogo: false,
    modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d'],
    responsive: true,
  }

  if (plotData.length === 0) {
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
