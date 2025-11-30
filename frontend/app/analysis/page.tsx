'use client'

import { useState, useCallback, useEffect } from 'react'
import { useDropzone } from 'react-dropzone'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
import { Upload, FileText, AlertCircle, CheckCircle, Settings, BarChart3, Download, Eye } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Modal } from '@/components/ui/modal'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useAppStore } from '@/lib/store'
import { apiClient } from '@/lib/api'
import ContinuousChart from '@/components/charts/ContinuousChart'
import CategoricalChart from '@/components/charts/CategoricalChart'
import { Plus, Trash2 } from 'lucide-react'

const configurationSchema = z.object({
  gender_col: z.string().min(1, 'Gender column is required'),
  categories_order: z.array(z.string()).min(1, 'At least one category is required'),
  vars_continuous: z.array(z.string()).min(1, 'At least one continuous variable is required'),
  vars_categorical: z.array(z.string()).min(1, 'At least one categorical variable is required'),
  weight_col: z.string().optional(),
  cluster_id: z.string().optional(),
  robust_se: z.boolean().default(false),
  missing_policy: z.enum(['listwise', 'pairwise', 'flag']).default('listwise'),
  suppress_threshold: z.number().min(1).max(100).default(5),
  fdr: z.boolean().default(false),
})

type ConfigurationForm = z.infer<typeof configurationSchema>

export default function AnalysisPage() {
  const { 
    sessionId, 
    schema, 
    genderCandidates, 
    analysisSettings, 
    analysisResults,
    setSessionId, 
    setSchema, 
    setAnalysisSettings, 
    setAnalysisResults,
    setLoading, 
    setError, 
    isLoading, 
    error 
  } = useAppStore()

  const [activeTab, setActiveTab] = useState('upload')
  const [uploadedFile, setUploadedFile] = useState<File | null>(null)
  const [showPreview, setShowPreview] = useState(false)
  const [previewData, setPreviewData] = useState<any>(null)
  const [genderMappings, setGenderMappings] = useState<Array<{from_value: string, to_value: string}>>([])
  const [availableValues, setAvailableValues] = useState<string[]>([])
  const [showErrorModal, setShowErrorModal] = useState(false)
  const [errorDetails, setErrorDetails] = useState<string>('')

  const form = useForm<ConfigurationForm>({
    resolver: zodResolver(configurationSchema),
    defaultValues: {
      gender_col: analysisSettings.gender_col || '',
      categories_order: analysisSettings.categories_order || ['female', 'male', 'other', 'missing'],
      vars_continuous: analysisSettings.vars_continuous || [],
      vars_categorical: analysisSettings.vars_categorical || [],
      weight_col: analysisSettings.weight_col || '',
      cluster_id: analysisSettings.cluster_id || '',
      robust_se: analysisSettings.robust_se || false,
      missing_policy: analysisSettings.missing_policy || 'listwise',
      suppress_threshold: analysisSettings.suppress_threshold || 5,
      fdr: analysisSettings.fdr || false,
    }
  })

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const file = acceptedFiles[0]
    if (file) {
      setUploadedFile(file)
      setError(null)
    }
  }, [setError])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
      'application/vnd.ms-excel': ['.xls'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/x-spss-sav': ['.sav'],
      'application/x-stata': ['.dta'],
      'application/parquet': ['.parquet'],
    },
    maxFiles: 1,
    maxSize: 50 * 1024 * 1024,
  })

  const handleUpload = async () => {
    if (!uploadedFile) return

    setLoading(true)
    setError(null)

    try {
      const response = await apiClient.uploadFile(uploadedFile)
      
      setSessionId(response.session_id)
      setSchema(response.schema, response.gender_candidates, response.file_info)
      
      setShowPreview(true)
      setPreviewData({
        sessionId: response.session_id,
        filename: uploadedFile.name,
        fileSize: uploadedFile.size,
        totalRows: response.schema.reduce((sum, col) => Math.max(sum, col.sample_values?.length || 0), 0),
        totalColumns: response.schema.length,
        genderCandidates: response.gender_candidates,
        sampleData: response.schema.slice(0, 5).map(col => ({
          name: col.name,
          type: col.variable_type,
          uniqueValues: col.unique_n,
          missingPct: col.missing_pct,
          sampleValues: col.sample_values?.slice(0, 3) || []
        }))
      })
      
      setActiveTab('configure')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed')
    } finally {
      setLoading(false)
    }
  }

  // Auto-populate gender mappings
  useEffect(() => {
    if (form.watch('gender_col') && schema.length > 0) {
      const genderVar = schema.find(v => v.name === form.watch('gender_col'))
      if (genderVar) {
        const values = genderVar.sample_values.map(v => String(v)).filter(v => v !== 'null')
        setAvailableValues(values)

        if (genderMappings.length === 0 && values.length > 0) {
          const defaultMappings = []
          const valueMap: { [key: string]: string } = {
            'F': 'female', 'Female': 'female', 'Woman': 'female', 'female': 'female',
            'M': 'male', 'Male': 'male', 'Man': 'male', 'male': 'male',
            'Non-binary': 'other', 'Other': 'other', 'other': 'other',
            'Prefer not to say': 'missing', 'Missing': 'missing', 'missing': 'missing'
          }
          values.forEach(value => {
            if (valueMap[value]) {
              defaultMappings.push({
                from_value: value,
                to_value: valueMap[value]
              })
            }
          })
          if (defaultMappings.length > 0) {
            setGenderMappings(defaultMappings)
          }
        }
      }
    }
  }, [form.watch('gender_col'), schema, genderMappings.length])

  const continuousVars = schema.filter(v => v.variable_type === 'continuous')
  const categoricalVars = schema.filter(v => v.variable_type === 'categorical')

  useEffect(() => {
    if (continuousVars.length > 0 && form.watch('vars_continuous').length === 0) {
      const defaultContinuous = continuousVars.slice(0, 3).map(v => v.name)
      form.setValue('vars_continuous', defaultContinuous)
    }

    if (categoricalVars.length > 0 && form.watch('vars_categorical').length === 0) {
      const defaultCategorical = categoricalVars
        .filter(v => v.name !== form.watch('gender_col'))
        .slice(0, 3)
        .map(v => v.name)
      form.setValue('vars_categorical', defaultCategorical)
    }
  }, [continuousVars, categoricalVars, form])

  const addGenderMapping = () => {
    setGenderMappings([...genderMappings, { from_value: '', to_value: '' }])
  }

  const removeGenderMapping = (index: number) => {
    setGenderMappings(genderMappings.filter((_, i) => i !== index))
  }

  const updateGenderMapping = (index: number, field: 'from_value' | 'to_value', value: string) => {
    const updated = [...genderMappings]
    updated[index][field] = value
    setGenderMappings(updated)
  }

  const onSubmit = async (data: ConfigurationForm) => {
    if (!sessionId) return

    if (genderMappings.length === 0) {
      setError('Please add at least one gender mapping')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const request = {
        session_id: sessionId,
        gender_col: data.gender_col,
        gender_map: genderMappings,
        categories_order: data.categories_order,
        vars_continuous: data.vars_continuous,
        vars_categorical: data.vars_categorical,
        weight_col: data.weight_col || undefined,
        cluster_id: data.cluster_id || undefined,
        robust_se: data.robust_se,
        missing_policy: data.missing_policy,
        impute: undefined,
        suppress_threshold: data.suppress_threshold,
        fdr: data.fdr,
      }

      const results = await apiClient.runAnalysis(request)
      setAnalysisResults(results)
      setAnalysisSettings(data)
      setActiveTab('results')
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Analysis failed'
      setError(errorMessage)
      setErrorDetails(errorMessage)
      setShowErrorModal(true)
    } finally {
      setLoading(false)
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const handleGenerateReport = async () => {
    if (!sessionId) return

    setLoading(true)
    try {
      const token = localStorage.getItem('token')
      const user = token ? JSON.parse(localStorage.getItem('user') || '{}') : null
      
      const response = await apiClient.generateReport({
        session_id: sessionId,
        title: 'Gender Analysis Report',
        organization: user?.name || 'Not specified',
        authors: user?.name ? [user.name] : ['Analysis Tool'],
        notes: 'Generated automatically'
      })
      
      // Store report in localStorage for Reports page
      const reports = JSON.parse(localStorage.getItem('reports') || '[]')
      reports.push({
        session_id: sessionId,
        title: 'Gender Analysis Report',
        html_url: response.html_url,
        pdf_url: response.pdf_url,
        docx_url: response.docx_url,
        generated_at: new Date().toISOString()
      })
      localStorage.setItem('reports', JSON.stringify(reports))
      
      alert('Report generated successfully! Check the Reports tab to view it.')
    } catch (err) {
      setError('Report generation failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-7xl mx-auto space-y-8">
      <div className="text-center space-y-4 py-6">
        <h1 className="text-4xl font-bold text-[#171717]">Data Analysis</h1>
        <p className="text-[#737373] text-lg">
          Upload, configure, and analyze your gender-disaggregated data
        </p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-8">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="upload">1. Upload Data</TabsTrigger>
          <TabsTrigger value="configure" disabled={!sessionId}>2. Configure</TabsTrigger>
          <TabsTrigger value="results" disabled={!analysisResults}>3. Results</TabsTrigger>
        </TabsList>

        {/* Upload Tab */}
        <TabsContent value="upload" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Upload className="h-5 w-5" />
                File Upload
              </CardTitle>
              <CardDescription>
                Supported formats: CSV, Excel (.xlsx, .xls), SPSS (.sav), Stata (.dta), Parquet
                <br />
                Maximum file size: 50MB
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div
                {...getRootProps()}
                className={`
                  border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-all
                  ${isDragActive ? 'border-[#5B197B] bg-[#F3E8FF]' : 'border-[#E5E5E5] bg-[#FAFAFA]'}
                  ${uploadedFile ? 'border-[#10B981] bg-[#ECFDF5]' : ''}
                  hover:border-[#5B197B] hover:bg-[#F3E8FF]
                `}
              >
                <input {...getInputProps()} />
                <div className="space-y-4">
                  <Upload className="h-12 w-12 mx-auto text-[#737373]" />
                  <div>
                    {isDragActive ? (
                      <p className="text-lg font-medium">Drop the file here...</p>
                    ) : uploadedFile ? (
                      <div className="space-y-2">
                        <CheckCircle className="h-8 w-8 mx-auto text-[#10B981]" />
                        <p className="text-lg font-medium text-[#10B981]">{uploadedFile.name}</p>
                        <p className="text-sm text-[#737373]">
                          {formatFileSize(uploadedFile.size)}
                        </p>
                      </div>
                    ) : (
                      <div>
                        <p className="text-lg font-medium">Drag and drop a file here</p>
                        <p className="text-[#737373]">or click to select a file</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {error && (
                <div className="mt-6 p-6 bg-[#FEF2F2] border-[0.5px] border-[#FECACA] rounded-xl">
                  <div className="flex items-center gap-3 text-[#DC2626]">
                    <AlertCircle className="h-5 w-5" />
                    <span className="font-semibold">Upload Error</span>
                  </div>
                  <p className="mt-2 text-sm text-[#991B1B]">{error}</p>
                </div>
              )}

              {uploadedFile && (
                <div className="mt-6 space-y-6">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <FileText className="h-5 w-5 text-[#5B197B]" />
                      <span className="font-semibold text-[#171717]">Ready to upload</span>
                    </div>
                    <Button
                      onClick={handleUpload}
                      disabled={isLoading}
                      className="min-w-[140px]"
                    >
                      {isLoading ? (
                        <div className="flex items-center gap-2">
                          <div className="loading-spinner h-4 w-4" />
                          Uploading...
                        </div>
                      ) : (
                        'Upload & Continue'
                      )}
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {showPreview && previewData && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Eye className="h-5 w-5" />
                  Data Preview
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div>
                    <h4 className="font-semibold text-sm text-[#737373] mb-2">File Name</h4>
                    <p className="text-sm text-[#171717]">{previewData.filename}</p>
                  </div>
                  <div>
                    <h4 className="font-semibold text-sm text-[#737373] mb-2">Dimensions</h4>
                    <p className="text-sm text-[#171717]">{previewData.totalRows} rows × {previewData.totalColumns} columns</p>
                  </div>
                  <div>
                    <h4 className="font-semibold text-sm text-[#737373] mb-2">Gender Candidates</h4>
                    <div className="flex flex-wrap gap-2">
                      {previewData.genderCandidates.map((col: string) => (
                        <span key={col} className="px-3 py-1 bg-[#F3E8FF] text-[#5B197B] text-xs font-medium rounded-xl">
                          {col}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Configure Tab */}
        <TabsContent value="configure" className="space-y-8">
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
            {/* Gender Variable Selection */}
            <Card>
              <CardHeader>
                <CardTitle>Gender Variable</CardTitle>
                <CardDescription>
                  Select the variable that contains gender information
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <Label htmlFor="gender_col">Gender Column</Label>
                    <Select
                      value={form.watch('gender_col')}
                      onValueChange={(value) => form.setValue('gender_col', value)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select gender column" />
                      </SelectTrigger>
                      <SelectContent>
                        {genderCandidates.map((col) => (
                          <SelectItem key={col} value={col}>
                            {col}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  {form.watch('gender_col') && (
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <Label>Gender Value Mapping</Label>
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={addGenderMapping}
                        >
                          <Plus className="h-4 w-4 mr-2" />
                          Add Mapping
                        </Button>
                      </div>
                      
                      {genderMappings.map((mapping, index) => (
                        <div key={index} className="flex items-end gap-4 p-4 bg-[#FAFAFA] rounded-xl border-[0.5px] border-[#E5E5E5]">
                          <div className="flex-1">
                            <Label className="text-[#737373] text-sm font-medium mb-2 block">From (Dataset Value)</Label>
                            <Select
                              value={mapping.from_value}
                              onValueChange={(value) => updateGenderMapping(index, 'from_value', value)}
                            >
                              <SelectTrigger className="rounded-xl">
                                <SelectValue placeholder="Select value" />
                              </SelectTrigger>
                              <SelectContent>
                                {availableValues.map((value) => (
                                  <SelectItem key={value} value={value}>
                                    {value}
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          </div>
                          <div className="flex-1">
                            <Label className="text-[#737373] text-sm font-medium mb-2 block">To (Standard Category)</Label>
                            <Select
                              value={mapping.to_value}
                              onValueChange={(value) => updateGenderMapping(index, 'to_value', value)}
                            >
                              <SelectTrigger className="rounded-xl">
                                <SelectValue placeholder="Select category" />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="female">Female</SelectItem>
                                <SelectItem value="male">Male</SelectItem>
                                <SelectItem value="other">Other</SelectItem>
                                <SelectItem value="missing">Missing</SelectItem>
                              </SelectContent>
                            </Select>
                          </div>
                          <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            onClick={() => removeGenderMapping(index)}
                            className="rounded-xl"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Variable Selection */}
            <div className="grid md:grid-cols-2 gap-8">
              <Card>
                <CardHeader>
                  <CardTitle>Continuous Variables</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {continuousVars.map((variable) => (
                      <div key={variable.name} className="flex items-center space-x-3 p-3 rounded-xl hover:bg-[#FAFAFA] transition-colors">
                        <input
                          type="checkbox"
                          id={`continuous-${variable.name}`}
                          checked={form.watch('vars_continuous').includes(variable.name)}
                          onChange={(e) => {
                            const current = form.watch('vars_continuous')
                            if (e.target.checked) {
                              form.setValue('vars_continuous', [...current, variable.name])
                            } else {
                              form.setValue('vars_continuous', current.filter(v => v !== variable.name))
                            }
                          }}
                          className="rounded-xl h-4 w-4 text-[#5B197B]"
                        />
                        <Label htmlFor={`continuous-${variable.name}`} className="flex-1 cursor-pointer">
                          <span className="font-medium text-[#171717]">{variable.name}</span>
                          <span className="text-sm text-[#737373] ml-2">
                            ({variable.dtype}, {variable.missing_pct}% missing)
                          </span>
                        </Label>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Categorical Variables</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {categoricalVars.map((variable) => (
                      <div key={variable.name} className="flex items-center space-x-3 p-3 rounded-xl hover:bg-[#FAFAFA] transition-colors">
                        <input
                          type="checkbox"
                          id={`categorical-${variable.name}`}
                          checked={form.watch('vars_categorical').includes(variable.name)}
                          onChange={(e) => {
                            const current = form.watch('vars_categorical')
                            if (e.target.checked) {
                              form.setValue('vars_categorical', [...current, variable.name])
                            } else {
                              form.setValue('vars_categorical', current.filter(v => v !== variable.name))
                            }
                          }}
                          className="rounded-xl h-4 w-4 text-[#5B197B]"
                        />
                        <Label htmlFor={`categorical-${variable.name}`} className="flex-1 cursor-pointer">
                          <span className="font-medium text-[#171717]">{variable.name}</span>
                          <span className="text-sm text-[#737373] ml-2">
                            ({variable.dtype}, {variable.unique_n} unique)
                          </span>
                        </Label>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Analysis Options */}
            <Card>
              <CardHeader>
                <CardTitle>Analysis Options</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid md:grid-cols-2 gap-8">
                  <div className="space-y-6">
                    <div>
                      <Label htmlFor="missing_policy">Missing Data Policy</Label>
                      <Select
                        value={form.watch('missing_policy')}
                        onValueChange={(value: 'listwise' | 'pairwise' | 'flag') => 
                          form.setValue('missing_policy', value)
                        }
                      >
                        <SelectTrigger className="rounded-xl">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="listwise">Listwise deletion</SelectItem>
                          <SelectItem value="pairwise">Pairwise deletion</SelectItem>
                          <SelectItem value="flag">Flag as missing</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div>
                      <Label htmlFor="suppress_threshold">Small Cell Suppression Threshold</Label>
                      <Input
                        type="number"
                        min="1"
                        max="100"
                        value={form.watch('suppress_threshold')}
                        onChange={(e) => form.setValue('suppress_threshold', parseInt(e.target.value))}
                        className="rounded-xl"
                      />
                    </div>
                  </div>

                  <div className="space-y-6">
                    <div className="flex items-center space-x-3 p-3 rounded-xl hover:bg-[#FAFAFA] transition-colors">
                      <input
                        type="checkbox"
                        id="fdr"
                        checked={form.watch('fdr')}
                        onChange={(e) => form.setValue('fdr', e.target.checked)}
                        className="rounded-xl h-4 w-4 text-[#5B197B]"
                      />
                      <Label htmlFor="fdr" className="cursor-pointer text-[#171717]">Apply FDR correction for multiple testing</Label>
                    </div>

                    <div className="flex items-center space-x-3 p-3 rounded-xl hover:bg-[#FAFAFA] transition-colors">
                      <input
                        type="checkbox"
                        id="robust_se"
                        checked={form.watch('robust_se')}
                        onChange={(e) => form.setValue('robust_se', e.target.checked)}
                        className="rounded-xl h-4 w-4 text-[#5B197B]"
                      />
                      <Label htmlFor="robust_se" className="cursor-pointer text-[#171717]">Use robust standard errors</Label>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {error && (
              <div className="p-6 bg-[#FEF2F2] border-[0.5px] border-[#FECACA] rounded-xl">
                <div className="flex items-center gap-3 text-[#DC2626]">
                  <AlertCircle className="h-5 w-5" />
                  <span className="font-semibold">Configuration Error</span>
                </div>
                <p className="mt-2 text-sm text-[#991B1B]">{error}</p>
              </div>
            )}

            <div className="flex justify-end gap-4 pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={() => setActiveTab('upload')}
                className="rounded-xl"
              >
                Back to Upload
              </Button>
              <Button
                type="submit"
                disabled={isLoading}
                className="min-w-[140px] rounded-xl"
              >
                {isLoading ? (
                  <div className="flex items-center gap-2">
                    <div className="loading-spinner h-4 w-4" />
                    Running Analysis...
                  </div>
                ) : (
                  'Run Analysis'
                )}
              </Button>
            </div>
          </form>

          <Modal
            isOpen={showErrorModal}
            onClose={() => setShowErrorModal(false)}
            title="Analysis Failed"
            size="lg"
          >
            <div className="space-y-4">
              <div className="flex items-start gap-3">
                <AlertCircle className="h-5 w-5 text-[#DC2626] mt-0.5 flex-shrink-0" />
                <div className="space-y-2">
                  <p className="text-sm text-[#737373]">
                    The analysis could not be completed due to the following issue:
                  </p>
                  <div className="p-3 bg-[#FEF2F2] border border-[#FECACA] rounded-lg">
                    <p className="text-sm font-mono">{errorDetails}</p>
                  </div>
                </div>
              </div>
              <div className="flex justify-end gap-2">
                <Button
                  variant="outline"
                  onClick={() => setShowErrorModal(false)}
                  className="rounded-xl"
                >
                  Close
                </Button>
              </div>
            </div>
          </Modal>
        </TabsContent>

        {/* Results Tab */}
        <TabsContent value="results" className="space-y-8">
          {analysisResults ? (
            <>
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-3xl font-bold text-[#171717]">Analysis Results</h2>
                  <p className="text-[#737373] mt-1">Gender-stratified statistical analysis results</p>
                </div>
                <Button onClick={handleGenerateReport} disabled={isLoading} className="rounded-xl">
                  <FileText className="h-4 w-4 mr-2" />
                  Generate Report
                </Button>
              </div>

              {/* Gender Summary */}
              <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
                {analysisResults.by_gender.map((gender: any) => (
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
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>

              {/* Continuous Variables */}
              {analysisResults.continuous && analysisResults.continuous.length > 0 && (
                <div className="space-y-8">
                  <h3 className="text-2xl font-bold text-[#171717]">Continuous Variables</h3>
                  {analysisResults.continuous.map((variable: any) => (
                    <Card key={variable.var}>
                      <CardHeader>
                        <CardTitle className="text-[#171717]">{variable.var}</CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-8">
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
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}

              {/* Categorical Variables */}
              {analysisResults.categorical && analysisResults.categorical.length > 0 && (
                <div className="space-y-8">
                  <h3 className="text-2xl font-bold text-[#171717]">Categorical Variables</h3>
                  {analysisResults.categorical.map((variable: any) => (
                    <Card key={variable.var}>
                      <CardHeader>
                        <CardTitle className="text-[#171717]">{variable.var}</CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-8">
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
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </>
          ) : (
            <Card>
              <CardContent className="py-12 text-center">
                <p className="text-[#737373]">No analysis results available. Please run an analysis first.</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  )
}

