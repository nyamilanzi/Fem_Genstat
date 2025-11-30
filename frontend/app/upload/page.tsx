'use client'

import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { useRouter } from 'next/navigation'
import { Upload, FileText, AlertCircle, CheckCircle, Eye, ArrowRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useAppStore } from '@/lib/store'
import { apiClient } from '@/lib/api'

export default function UploadPage() {
  const router = useRouter()
  const { setSessionId, setSchema, setLoading, setError, isLoading, error } = useAppStore()
  
  const [uploadedFile, setUploadedFile] = useState<File | null>(null)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [showPreview, setShowPreview] = useState(false)
  const [previewData, setPreviewData] = useState<any>(null)

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
    maxSize: 50 * 1024 * 1024, // 50MB
  })

  const handleUpload = async () => {
    if (!uploadedFile) return

    setLoading(true)
    setError(null)

    try {
      const response = await apiClient.uploadFile(uploadedFile)
      
      setSessionId(response.session_id)
      setSchema(response.schema, response.gender_candidates, response.file_info)
      
      // Show data preview
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
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed')
    } finally {
      setLoading(false)
    }
  }

  const handleContinue = () => {
    router.push('/configure')
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="text-center space-y-4 py-6">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-[#1A237E] shadow-lg mb-2">
          <Upload className="h-8 w-8 text-white" />
        </div>
        <h1 className="text-4xl font-bold text-[#171717]">
          Upload Your Dataset
        </h1>
        <p className="text-[#737373] text-lg max-w-2xl mx-auto">
          Upload your dataset to begin professional gender-stratified analysis with FEMSTAT
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>File Upload</CardTitle>
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
              ${isDragActive ? 'border-[#3B82F6] bg-[#EFF6FF]' : 'border-[#E5E5E5] bg-[#FAFAFA]'}
              ${uploadedFile ? 'border-[#10B981] bg-[#ECFDF5]' : ''}
              hover:border-[#3B82F6] hover:bg-[#F0F9FF]
            `}
          >
            <input {...getInputProps()} />
            <div className="space-y-4">
              <Upload className="h-12 w-12 mx-auto text-muted-foreground" />
              <div>
                {isDragActive ? (
                  <p className="text-lg font-medium">Drop the file here...</p>
                ) : uploadedFile ? (
                  <div className="space-y-2">
                    <CheckCircle className="h-8 w-8 mx-auto text-green-500" />
                    <p className="text-lg font-medium text-green-700">{uploadedFile.name}</p>
                    <p className="text-sm text-muted-foreground">
                      {formatFileSize(uploadedFile.size)}
                    </p>
                  </div>
                ) : (
                  <div>
                    <p className="text-lg font-medium">Drag and drop a file here</p>
                    <p className="text-muted-foreground">or click to select a file</p>
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
                  <FileText className="h-5 w-5 text-[#3B82F6]" />
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
              
              {isLoading && (
                <div className="w-full bg-[#F5F5F5] rounded-full h-2">
                  <div 
                    className="bg-[#3B82F6] h-2 rounded-full transition-all duration-300"
                    style={{ width: `${uploadProgress}%` }}
                  />
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Data Privacy</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4 text-sm text-[#737373]">
            <div className="flex items-start gap-3">
              <CheckCircle className="h-5 w-5 text-[#10B981] mt-0.5 flex-shrink-0" />
              <p>Your data is stored in memory only and automatically expires after 60 minutes</p>
            </div>
            <div className="flex items-start gap-3">
              <CheckCircle className="h-5 w-5 text-[#10B981] mt-0.5 flex-shrink-0" />
              <p>Small cell suppression protects privacy by hiding counts below 5</p>
            </div>
            <div className="flex items-start gap-3">
              <CheckCircle className="h-5 w-5 text-[#10B981] mt-0.5 flex-shrink-0" />
              <p>No personal data is saved to disk or transmitted to external services</p>
            </div>
            <div className="flex items-start gap-3">
              <CheckCircle className="h-5 w-5 text-[#10B981] mt-0.5 flex-shrink-0" />
              <p>You can manually purge your data at any time</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Data Preview */}
      {showPreview && previewData && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Eye className="h-5 w-5" />
              Data Preview
            </CardTitle>
            <CardDescription>
              Review your uploaded data before proceeding to analysis configuration
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-8">
              {/* File Info */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="space-y-2">
                  <h4 className="font-semibold text-sm text-[#737373]">File Name</h4>
                  <p className="text-sm text-[#171717]">{previewData.filename}</p>
                </div>
                <div className="space-y-2">
                  <h4 className="font-semibold text-sm text-[#737373]">File Size</h4>
                  <p className="text-sm text-[#171717]">{formatFileSize(previewData.fileSize)}</p>
                </div>
                <div className="space-y-2">
                  <h4 className="font-semibold text-sm text-[#737373]">Session ID</h4>
                  <p className="text-sm font-mono text-xs text-[#171717]">{previewData.sessionId}</p>
                </div>
              </div>

              {/* Data Summary */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-3">
                  <h4 className="font-semibold text-sm text-[#737373]">Dataset Dimensions</h4>
                  <div className="flex gap-6 text-sm text-[#171717]">
                    <span><strong className="font-semibold">{previewData.totalRows}</strong> rows</span>
                    <span><strong className="font-semibold">{previewData.totalColumns}</strong> columns</span>
                  </div>
                </div>
                <div className="space-y-3">
                  <h4 className="font-semibold text-sm text-[#737373]">Gender Candidates</h4>
                  <div className="flex flex-wrap gap-2">
                    {previewData.genderCandidates.map((col: string) => (
                      <span key={col} className="px-3 py-1.5 bg-[#EFF6FF] text-[#3B82F6] text-xs font-medium rounded-xl">
                        {col}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              {/* Sample Data */}
              <div className="space-y-4">
                <h4 className="font-semibold text-sm text-[#737373]">Sample Variables</h4>
                <div className="space-y-3">
                  {previewData.sampleData.map((col: any, index: number) => (
                    <div key={index} className="flex items-center justify-between p-4 bg-[#FAFAFA] rounded-xl text-sm border-[0.5px] border-[#E5E5E5]">
                      <div className="flex items-center gap-3">
                        <span className="font-semibold text-[#171717]">{col.name}</span>
                        <span className={`px-3 py-1 text-xs font-medium rounded-xl ${
                          col.type === 'continuous' ? 'bg-[#DBEAFE] text-[#1E40AF]' : 'bg-[#D1FAE5] text-[#065F46]'
                        }`}>
                          {col.type}
                        </span>
                      </div>
                      <div className="flex items-center gap-6 text-xs text-[#737373]">
                        <span>{col.uniqueValues} unique</span>
                        <span>{col.missingPct}% missing</span>
                        <span>Sample: {col.sampleValues.join(', ')}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Continue Button */}
              <div className="flex justify-end pt-2">
                <Button onClick={handleContinue} className="min-w-[180px]">
                  Continue to Configuration
                  <ArrowRight className="h-4 w-4 ml-2" />
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
