'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useAppStore } from '@/lib/store'
import { apiClient } from '@/lib/api'
import ContinuousChart from '@/components/charts/ContinuousChart'
import CategoricalChart from '@/components/charts/CategoricalChart'
import { Download, FileText, BarChart3, AlertCircle, CheckCircle } from 'lucide-react'

export default function ResultsPage() {
  const router = useRouter()
  const { 
    sessionId, 
    analysisResults, 
    setAnalysisResults, 
    setLoading, 
    setError, 
    isLoading, 
    error 
  } = useAppStore()

  const [activeTab, setActiveTab] = useState('overview')
  const [reportModalOpen, setReportModalOpen] = useState(false)

  // Redirect if no results
  useEffect(() => {
    if (!analysisResults) {
      router.push('/upload')
    }
  }, [analysisResults, router])

  const handleDownload = async (url: string, filename: string) => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}${url}`)
      const blob = await response.blob()
      const downloadUrl = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = downloadUrl
      link.download = filename
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(downloadUrl)
    } catch (err) {
      setError('Download failed')
    }
  }

  const generateReport = async () => {
    if (!sessionId) return

    setLoading(true)
    try {
      const response = await apiClient.generateReport({
        session_id: sessionId,
        title: 'Gender Analysis Report',
        organization: 'Analysis Tool',
        authors: ['Analysis Tool'],
        notes: 'Generated automatically'
      })
      
      // Open report in new tab
      window.open(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}${response.html_url}`, '_blank')
    } catch (err) {
      setError('Report generation failed')
    } finally {
      setLoading(false)
    }
  }

  if (!analysisResults) {
    return <div>Loading...</div>
  }

  return (
    <div className="max-w-7xl mx-auto space-y-8">
      <div className="flex items-center justify-between py-6">
        <div>
          <div className="flex items-center gap-3 mb-3">
            <div className="w-12 h-12 rounded-xl bg-[#1A237E] flex items-center justify-center shadow-md">
              <BarChart3 className="h-6 w-6 text-white" />
            </div>
            <h1 className="text-4xl font-bold text-[#171717]">Analysis Results</h1>
          </div>
          <p className="text-[#737373] text-lg mt-1">
            Gender-stratified statistical analysis results
          </p>
        </div>
        <div className="flex gap-3">
          <Button
            variant="outline"
            onClick={() => handleDownload(analysisResults.files.csv_wide_url, 'results_wide.csv')}
            className="rounded-xl"
          >
            <Download className="h-4 w-4 mr-2" />
            CSV Wide
          </Button>
          <Button
            variant="outline"
            onClick={() => handleDownload(analysisResults.files.csv_long_url, 'results_long.csv')}
            className="rounded-xl"
          >
            <Download className="h-4 w-4 mr-2" />
            CSV Long
          </Button>
          <Button
            variant="outline"
            onClick={() => handleDownload(analysisResults.files.json_url, 'results.json')}
            className="rounded-xl"
          >
            <Download className="h-4 w-4 mr-2" />
            JSON
          </Button>
          <Button onClick={generateReport} disabled={isLoading} className="rounded-xl">
            <FileText className="h-4 w-4 mr-2" />
            Generate Report
          </Button>
        </div>
      </div>

      {error && (
        <div className="p-6 bg-[#FEF2F2] border-[0.5px] border-[#FECACA] rounded-xl">
          <div className="flex items-center gap-3 text-[#DC2626]">
            <AlertCircle className="h-5 w-5" />
            <span className="font-semibold">Error</span>
          </div>
          <p className="mt-2 text-sm text-[#991B1B]">{error}</p>
        </div>
      )}

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-8">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="continuous">Continuous</TabsTrigger>
          <TabsTrigger value="categorical">Categorical</TabsTrigger>
          <TabsTrigger value="missingness">Missingness</TabsTrigger>
          <TabsTrigger value="settings">Settings</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-8">
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {analysisResults.by_gender.map((gender) => (
              <Card key={gender.gender}>
                <CardHeader className="pb-4">
                  <CardTitle className="text-lg capitalize text-[#171717]">{gender.gender}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-sm text-[#737373]">Count:</span>
                      <span className="font-semibold text-[#171717]">{gender.n}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-[#737373]">Percent:</span>
                      <span className="font-semibold text-[#171717]">{gender.pct}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-[#737373]">Missing:</span>
                      <span className="font-semibold text-[#171717]">{gender.missing_pct}%</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          <Card>
            <CardHeader>
              <CardTitle className="text-[#171717]">Analysis Summary</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid md:grid-cols-2 gap-8">
                <div>
                  <h4 className="font-semibold mb-3 text-[#171717]">Continuous Variables</h4>
                  <p className="text-sm text-[#737373]">
                    {analysisResults.continuous.length} variables analyzed
                  </p>
                </div>
                <div>
                  <h4 className="font-semibold mb-3 text-[#171717]">Categorical Variables</h4>
                  <p className="text-sm text-[#737373]">
                    {analysisResults.categorical.length} variables analyzed
                  </p>
                </div>
                <div>
                  <h4 className="font-semibold mb-3 text-[#171717]">Multiple Testing</h4>
                  <p className="text-sm text-[#737373]">
                    {analysisResults.diagnostics.multiple_testing.adjusted ? 'FDR correction applied' : 'No correction'}
                  </p>
                </div>
                <div>
                  <h4 className="font-semibold mb-3 text-[#171717]">Small Cell Suppression</h4>
                  <p className="text-sm text-[#737373]">
                    Threshold: {analysisResults.settings.suppress_threshold}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Continuous Variables Tab */}
        <TabsContent value="continuous" className="space-y-8">
          {analysisResults.continuous.map((variable) => (
            <Card key={variable.var}>
              <CardHeader>
                <CardTitle className="text-[#171717]">{variable.var}</CardTitle>
                <CardDescription className="text-[#737373]">Continuous variable analysis</CardDescription>
              </CardHeader>
              <CardContent className="space-y-8">
                {/* Summary Table */}
                <div className="overflow-x-auto">
                  <table className="w-full border-collapse border-[0.5px] border-[#E5E5E5] rounded-xl overflow-hidden">
                    <thead>
                      <tr className="bg-[#FAFAFA]">
                        <th className="border-[0.5px] border-[#E5E5E5] p-4 text-left text-sm font-semibold text-[#171717]">Gender</th>
                        <th className="border-[0.5px] border-[#E5E5E5] p-4 text-left text-sm font-semibold text-[#171717]">N</th>
                        <th className="border-[0.5px] border-[#E5E5E5] p-4 text-left text-sm font-semibold text-[#171717]">Mean</th>
                        <th className="border-[0.5px] border-[#E5E5E5] p-4 text-left text-sm font-semibold text-[#171717]">SD</th>
                        <th className="border-[0.5px] border-[#E5E5E5] p-4 text-left text-sm font-semibold text-[#171717]">Median</th>
                        <th className="border-[0.5px] border-[#E5E5E5] p-4 text-left text-sm font-semibold text-[#171717]">IQR</th>
                        <th className="border-[0.5px] border-[#E5E5E5] p-4 text-left text-sm font-semibold text-[#171717]">Min</th>
                        <th className="border-[0.5px] border-[#E5E5E5] p-4 text-left text-sm font-semibold text-[#171717]">Max</th>
                      </tr>
                    </thead>
                    <tbody>
                      {variable.table.map((stat, index) => (
                        <tr key={index} className="hover:bg-[#FAFAFA] transition-colors">
                          <td className="border-[0.5px] border-[#E5E5E5] p-4 text-sm text-[#171717]">{stat.gender}</td>
                          <td className="border-[0.5px] border-[#E5E5E5] p-4 text-sm text-[#171717]">{stat.n}</td>
                          <td className="border-[0.5px] border-[#E5E5E5] p-4 text-sm text-[#171717]">{stat.mean}</td>
                          <td className="border-[0.5px] border-[#E5E5E5] p-4 text-sm text-[#171717]">{stat.sd}</td>
                          <td className="border-[0.5px] border-[#E5E5E5] p-4 text-sm text-[#171717]">{stat.median}</td>
                          <td className="border-[0.5px] border-[#E5E5E5] p-4 text-sm text-[#171717]">{stat.iqr}</td>
                          <td className="border-[0.5px] border-[#E5E5E5] p-4 text-sm text-[#171717]">{stat.min}</td>
                          <td className="border-[0.5px] border-[#E5E5E5] p-4 text-sm text-[#171717]">{stat.max}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Charts */}
                <div className="grid md:grid-cols-2 gap-8">
                  <div>
                    <h4 className="font-semibold mb-4 text-[#171717]">Box Plot</h4>
                    <ContinuousChart
                      data={variable.table}
                      variableName={variable.var}
                      chartType="boxplot"
                    />
                  </div>
                  <div>
                    <h4 className="font-semibold mb-4 text-[#171717]">Distribution</h4>
                    <ContinuousChart
                      data={variable.table}
                      variableName={variable.var}
                      chartType="histogram"
                    />
                  </div>
                </div>

                {/* Statistical Test */}
                <div className="bg-[#FAFAFA] p-6 rounded-xl border-[0.5px] border-[#E5E5E5]">
                  <h4 className="font-semibold mb-4 text-[#171717]">Statistical Test</h4>
                  <div className="grid md:grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-muted-foreground">Test:</p>
                      <p className="font-medium">{variable.test.name}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">P-value:</p>
                      <p className="font-medium">{variable.test.p}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Statistic:</p>
                      <p className="font-medium">{variable.test.statistic}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Assumptions Met:</p>
                      <div className="flex items-center gap-1">
                        {variable.test.assumptions_met ? (
                          <CheckCircle className="h-4 w-4 text-green-500" />
                        ) : (
                          <AlertCircle className="h-4 w-4 text-red-500" />
                        )}
                        <span className="text-sm">
                          {variable.test.assumptions_met ? 'Yes' : 'No'}
                        </span>
                      </div>
                    </div>
                  </div>
                  {variable.test.note && (
                    <p className="text-sm text-muted-foreground mt-2">
                      Note: {variable.test.note}
                    </p>
                  )}
                </div>

                {/* Effect Sizes */}
                {variable.effects.length > 0 && (
                  <div className="bg-muted/50 p-4 rounded-lg">
                    <h4 className="font-medium mb-2">Effect Sizes</h4>
                    <div className="space-y-2">
                      {variable.effects.map((effect, index) => (
                        <div key={index} className="flex justify-between items-center">
                          <span className="font-medium">{effect.name}:</span>
                          <span>
                            {effect.value}
                            {effect.ci_lower && effect.ci_upper && (
                              <span className="text-sm text-muted-foreground ml-2">
                                (95% CI: {effect.ci_lower}, {effect.ci_upper})
                              </span>
                            )}
                            {effect.interpretation && (
                              <span className="text-sm text-muted-foreground ml-2">
                                - {effect.interpretation}
                              </span>
                            )}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </TabsContent>

        {/* Categorical Variables Tab */}
        <TabsContent value="categorical" className="space-y-8">
          {analysisResults.categorical.map((variable) => (
            <Card key={variable.var}>
              <CardHeader>
                <CardTitle className="text-[#171717]">{variable.var}</CardTitle>
                <CardDescription className="text-[#737373]">Categorical variable analysis</CardDescription>
              </CardHeader>
              <CardContent className="space-y-8">
                {/* Summary Table */}
                <div className="overflow-x-auto">
                  <table className="w-full border-collapse border-[0.5px] border-[#E5E5E5] rounded-xl overflow-hidden">
                    <thead>
                      <tr className="bg-[#FAFAFA]">
                        <th className="border-[0.5px] border-[#E5E5E5] p-4 text-left text-sm font-semibold text-[#171717]">Level</th>
                        <th className="border-[0.5px] border-[#E5E5E5] p-4 text-left text-sm font-semibold text-[#171717]">Gender</th>
                        <th className="border-[0.5px] border-[#E5E5E5] p-4 text-left text-sm font-semibold text-[#171717]">Count</th>
                        <th className="border-[0.5px] border-[#E5E5E5] p-4 text-left text-sm font-semibold text-[#171717]">Percent</th>
                      </tr>
                    </thead>
                    <tbody>
                      {variable.table.map((level, index) => (
                        <tr key={index} className="hover:bg-[#FAFAFA] transition-colors">
                          <td className="border-[0.5px] border-[#E5E5E5] p-4 text-sm text-[#171717]">{level.level}</td>
                          <td className="border-[0.5px] border-[#E5E5E5] p-4 text-sm text-[#171717]">{level.gender}</td>
                          <td className="border-[0.5px] border-[#E5E5E5] p-4 text-sm text-[#171717]">{level.n}</td>
                          <td className="border-[0.5px] border-[#E5E5E5] p-4 text-sm text-[#171717]">{level.pct}%</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Charts */}
                <div className="grid md:grid-cols-2 gap-8">
                  <div>
                    <h4 className="font-semibold mb-4 text-[#171717]">Stacked Bar Chart</h4>
                    <CategoricalChart
                      data={variable.table}
                      variableName={variable.var}
                      chartType="stacked"
                    />
                  </div>
                  <div>
                    <h4 className="font-semibold mb-4 text-[#171717]">Grouped Bar Chart</h4>
                    <CategoricalChart
                      data={variable.table}
                      variableName={variable.var}
                      chartType="grouped"
                    />
                  </div>
                </div>

                {/* Statistical Test */}
                <div className="bg-[#FAFAFA] p-6 rounded-xl border-[0.5px] border-[#E5E5E5]">
                  <h4 className="font-semibold mb-4 text-[#171717]">Statistical Test</h4>
                  <div className="grid md:grid-cols-2 gap-6">
                    <div>
                      <p className="text-sm text-[#737373] mb-1">Test:</p>
                      <p className="font-semibold text-[#171717]">{variable.test.name}</p>
                    </div>
                    <div>
                      <p className="text-sm text-[#737373] mb-1">P-value:</p>
                      <p className="font-semibold text-[#171717]">{variable.test.p}</p>
                    </div>
                    <div>
                      <p className="text-sm text-[#737373] mb-1">Statistic:</p>
                      <p className="font-semibold text-[#171717]">{variable.test.statistic}</p>
                    </div>
                    <div>
                      <p className="text-sm text-[#737373] mb-1">Assumptions Met:</p>
                      <div className="flex items-center gap-2">
                        {variable.test.assumptions_met ? (
                          <CheckCircle className="h-5 w-5 text-[#10B981]" />
                        ) : (
                          <AlertCircle className="h-5 w-5 text-[#EF4444]" />
                        )}
                        <span className="text-sm font-medium text-[#171717]">
                          {variable.test.assumptions_met ? 'Yes' : 'No'}
                        </span>
                      </div>
                    </div>
                  </div>
                  {variable.test.note && (
                    <p className="text-sm text-[#737373] mt-4">
                      Note: {variable.test.note}
                    </p>
                  )}
                </div>

                {/* Effect Sizes */}
                {variable.effects.length > 0 && (
                  <div className="bg-[#FAFAFA] p-6 rounded-xl border-[0.5px] border-[#E5E5E5]">
                    <h4 className="font-semibold mb-4 text-[#171717]">Effect Sizes</h4>
                    <div className="space-y-3">
                      {variable.effects.map((effect, index) => (
                        <div key={index} className="flex justify-between items-center p-3 bg-white rounded-xl">
                          <span className="font-semibold text-[#171717]">{effect.name}:</span>
                          <span className="text-[#171717]">
                            {effect.value}
                            {effect.ci_lower && effect.ci_upper && (
                              <span className="text-sm text-[#737373] ml-2">
                                (95% CI: {effect.ci_lower}, {effect.ci_upper})
                              </span>
                            )}
                            {effect.interpretation && (
                              <span className="text-sm text-[#737373] ml-2">
                                - {effect.interpretation}
                              </span>
                            )}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </TabsContent>

        {/* Missingness Tab */}
        <TabsContent value="missingness" className="space-y-8">
          <Card>
            <CardHeader>
              <CardTitle className="text-[#171717]">Missing Data Analysis</CardTitle>
              <CardDescription className="text-[#737373]">Missing data patterns by gender</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full border-collapse border-[0.5px] border-[#E5E5E5] rounded-xl overflow-hidden">
                  <thead>
                    <tr className="bg-[#FAFAFA]">
                      <th className="border-[0.5px] border-[#E5E5E5] p-4 text-left text-sm font-semibold text-[#171717]">Variable</th>
                      <th className="border-[0.5px] border-[#E5E5E5] p-4 text-left text-sm font-semibold text-[#171717]">Gender</th>
                      <th className="border-[0.5px] border-[#E5E5E5] p-4 text-left text-sm font-semibold text-[#171717]">Missing Count</th>
                      <th className="border-[0.5px] border-[#E5E5E5] p-4 text-left text-sm font-semibold text-[#171717]">Missing %</th>
                    </tr>
                  </thead>
                  <tbody>
                    {analysisResults.missingness.map((missing, index) => (
                      <tr key={index} className="hover:bg-[#FAFAFA] transition-colors">
                        <td className="border-[0.5px] border-[#E5E5E5] p-4 text-sm text-[#171717]">{missing.var}</td>
                        <td className="border-[0.5px] border-[#E5E5E5] p-4 text-sm text-[#171717]">{missing.gender}</td>
                        <td className="border-[0.5px] border-[#E5E5E5] p-4 text-sm text-[#171717]">{missing.missing_n}</td>
                        <td className="border-[0.5px] border-[#E5E5E5] p-4 text-sm text-[#171717]">{missing.missing_pct}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Settings Tab */}
        <TabsContent value="settings" className="space-y-8">
          <Card>
            <CardHeader>
              <CardTitle className="text-[#171717]">Analysis Settings</CardTitle>
              <CardDescription className="text-[#737373]">Configuration used for this analysis</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid md:grid-cols-2 gap-8">
                <div className="space-y-6">
                  <div>
                    <h4 className="font-semibold mb-2 text-[#171717]">Gender Variable</h4>
                    <p className="text-sm text-[#737373]">{analysisResults.settings.gender_col}</p>
                  </div>
                  <div>
                    <h4 className="font-semibold mb-2 text-[#171717]">Missing Data Policy</h4>
                    <p className="text-sm text-[#737373]">{analysisResults.settings.missing_policy}</p>
                  </div>
                  <div>
                    <h4 className="font-semibold mb-2 text-[#171717]">Small Cell Threshold</h4>
                    <p className="text-sm text-[#737373]">{analysisResults.settings.suppress_threshold}</p>
                  </div>
                </div>
                <div className="space-y-6">
                  <div>
                    <h4 className="font-semibold mb-2 text-[#171717]">Multiple Testing</h4>
                    <p className="text-sm text-[#737373]">
                      {analysisResults.settings.fdr ? 'FDR correction applied' : 'No correction'}
                    </p>
                  </div>
                  <div>
                    <h4 className="font-semibold mb-2 text-[#171717]">Weight Variable</h4>
                    <p className="text-sm text-[#737373]">
                      {analysisResults.settings.weight_col || 'None'}
                    </p>
                  </div>
                  <div>
                    <h4 className="font-semibold mb-2 text-[#171717]">Robust Standard Errors</h4>
                    <p className="text-sm text-[#737373]">
                      {analysisResults.settings.robust_se ? 'Yes' : 'No'}
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <div className="flex justify-between pt-4">
        <Button
          variant="outline"
          onClick={() => router.push('/configure')}
          className="rounded-xl"
        >
          Back to Configuration
        </Button>
        <Button
          variant="outline"
          onClick={() => router.push('/upload')}
          className="rounded-xl"
        >
          Start New Analysis
        </Button>
      </div>
    </div>
  )
}
