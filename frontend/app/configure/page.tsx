'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Modal } from '@/components/ui/modal'
import { useAppStore } from '@/lib/store'
import { apiClient } from '@/lib/api'
import { Plus, Trash2, AlertCircle, Settings } from 'lucide-react'

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

export default function ConfigurePage() {
  const router = useRouter()
  const { 
    sessionId, 
    schema, 
    genderCandidates, 
    analysisSettings, 
    setAnalysisSettings, 
    setAnalysisResults,
    setLoading, 
    setError, 
    isLoading, 
    error 
  } = useAppStore()

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

  // Redirect if no session
  useEffect(() => {
    if (!sessionId) {
      router.push('/upload')
    }
  }, [sessionId, router])

  // Get available values for gender mapping
  useEffect(() => {
    if (form.watch('gender_col') && schema.length > 0) {
      const genderVar = schema.find(v => v.name === form.watch('gender_col'))
      if (genderVar) {
        const values = genderVar.sample_values.map(v => String(v)).filter(v => v !== 'null')
        setAvailableValues(values)
        
        // Auto-populate some default mappings if none exist
        if (genderMappings.length === 0 && values.length > 0) {
          const defaultMappings = []
          
          // Try to map common gender values
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

  // Auto-select some default variables if none are selected
  useEffect(() => {
    if (continuousVars.length > 0 && form.watch('vars_continuous').length === 0) {
      // Auto-select first few continuous variables
      const defaultContinuous = continuousVars.slice(0, 3).map(v => v.name)
      form.setValue('vars_continuous', defaultContinuous)
    }
    
    if (categoricalVars.length > 0 && form.watch('vars_categorical').length === 0) {
      // Auto-select first few categorical variables (excluding gender)
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

    // Validate that we have gender mappings
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
        impute: undefined, // TODO: Add imputation options
        suppress_threshold: data.suppress_threshold,
        fdr: data.fdr,
      }

      const results = await apiClient.runAnalysis(request)
      setAnalysisResults(results)
      setAnalysisSettings(data)
      
      router.push('/results')
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Analysis failed'
      setError(errorMessage)
      setErrorDetails(errorMessage)
      setShowErrorModal(true)
    } finally {
      setLoading(false)
    }
  }

  if (!sessionId) {
    return <div>Redirecting...</div>
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="text-center space-y-4 py-6">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-[#1A237E] shadow-lg mb-2">
          <Settings className="h-8 w-8 text-white" />
        </div>
        <h1 className="text-4xl font-bold text-[#171717]">
          Configure Analysis
        </h1>
        <p className="text-[#737373] text-lg max-w-2xl mx-auto">
          Set up your gender-stratified analysis parameters and options
        </p>
      </div>

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
                {form.formState.errors.gender_col && (
                  <p className="text-sm text-destructive mt-1">
                    {form.formState.errors.gender_col.message}
                  </p>
                )}
              </div>

              {/* Gender Mapping */}
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
                          <SelectTrigger className="rounded-xl border-[0.5px] border-[#E5E5E5]">
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
                          <SelectTrigger className="rounded-xl border-[0.5px] border-[#E5E5E5]">
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
              <CardDescription>
                Select numeric variables for analysis
              </CardDescription>
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
                      className="rounded-xl h-4 w-4 text-[#3B82F6] focus:ring-[#3B82F6]"
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
              <CardDescription>
                Select categorical variables for analysis
              </CardDescription>
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
                      className="rounded-xl h-4 w-4 text-[#3B82F6] focus:ring-[#3B82F6]"
                    />
                    <Label htmlFor={`categorical-${variable.name}`} className="flex-1 cursor-pointer">
                      <span className="font-medium text-[#171717]">{variable.name}</span>
                      <span className="text-sm text-[#737373] ml-2">
                        ({variable.dtype}, {variable.unique_n} unique values)
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
            <CardDescription>
              Configure statistical analysis parameters
            </CardDescription>
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
                    <SelectTrigger>
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
                    className="rounded-xl h-4 w-4 text-[#3B82F6] focus:ring-[#3B82F6]"
                  />
                  <Label htmlFor="fdr" className="cursor-pointer text-[#171717]">Apply FDR correction for multiple testing</Label>
                </div>

                <div className="flex items-center space-x-3 p-3 rounded-xl hover:bg-[#FAFAFA] transition-colors">
                  <input
                    type="checkbox"
                    id="robust_se"
                    checked={form.watch('robust_se')}
                    onChange={(e) => form.setValue('robust_se', e.target.checked)}
                    className="rounded-xl h-4 w-4 text-[#3B82F6] focus:ring-[#3B82F6]"
                  />
                  <Label htmlFor="robust_se" className="cursor-pointer text-[#171717]">Use robust standard errors (if weights provided)</Label>
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
            onClick={() => router.push('/upload')}
          >
            Back to Upload
          </Button>
          <Button
            type="submit"
            disabled={isLoading}
            className="min-w-[120px]"
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

      {/* Error Modal */}
      <Modal
        isOpen={showErrorModal}
        onClose={() => setShowErrorModal(false)}
        title="Analysis Failed"
        size="lg"
      >
        <div className="space-y-4">
          <div className="flex items-start gap-3">
            <AlertCircle className="h-5 w-5 text-destructive mt-0.5 flex-shrink-0" />
            <div className="space-y-2">
              <p className="text-sm text-muted-foreground">
                The analysis could not be completed due to the following issue:
              </p>
              <div className="p-3 bg-destructive/10 border border-destructive/20 rounded-lg">
                <p className="text-sm font-mono">{errorDetails}</p>
              </div>
            </div>
          </div>
          
          <div className="space-y-2">
            <h4 className="font-medium text-sm">Common causes and solutions:</h4>
            <ul className="text-sm text-muted-foreground space-y-1">
              <li>• <strong>Insufficient data:</strong> Check that you have enough observations for each gender group</li>
              <li>• <strong>Missing gender values:</strong> Ensure your gender column has valid values mapped</li>
              <li>• <strong>Invalid variable types:</strong> Verify continuous variables contain numeric data</li>
              <li>• <strong>Small cell sizes:</strong> Try reducing the suppression threshold or selecting different variables</li>
              <li>• <strong>Data format issues:</strong> Check that your data was uploaded correctly</li>
            </ul>
          </div>

          <div className="flex justify-end gap-2">
            <Button
              variant="outline"
              onClick={() => setShowErrorModal(false)}
            >
              Close
            </Button>
            <Button
              onClick={() => {
                setShowErrorModal(false)
                // Optionally navigate back to upload
                router.push('/upload')
              }}
            >
              Upload New Data
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
