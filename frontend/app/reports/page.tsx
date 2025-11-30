'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { FileText, Download, Eye, Calendar, Trash2 } from 'lucide-react'
import Link from 'next/link'

interface Report {
  session_id: string
  title: string
  html_url: string
  pdf_url?: string
  docx_url?: string
  generated_at: string
}

export default function ReportsPage() {
  const [reports, setReports] = useState<Report[]>([])

  useEffect(() => {
    // Load reports from localStorage
    const storedReports = JSON.parse(localStorage.getItem('reports') || '[]')
    // Sort by date, newest first
    storedReports.sort((a: Report, b: Report) => 
      new Date(b.generated_at).getTime() - new Date(a.generated_at).getTime()
    )
    setReports(storedReports)
  }, [])

  const handleDelete = (sessionId: string) => {
    const updatedReports = reports.filter(r => r.session_id !== sessionId)
    setReports(updatedReports)
    localStorage.setItem('reports', JSON.stringify(updatedReports))
  }

  const handleDownload = async (url: string, filename: string) => {
    try {
      const response = await fetch(`http://localhost:8000${url}`)
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
      console.error('Download failed:', err)
    }
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  return (
    <div className="max-w-7xl mx-auto space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold text-[#171717]">Generated Reports</h1>
          <p className="text-[#737373] text-lg mt-1">
            View and download your analysis reports
          </p>
        </div>
        <Link href="/analysis">
          <Button className="rounded-xl">
            Create New Analysis
          </Button>
        </Link>
      </div>

      {reports.length === 0 ? (
        <Card>
          <CardContent className="py-16 text-center">
            <FileText className="h-16 w-16 mx-auto text-[#737373] mb-4" />
            <h3 className="text-xl font-semibold text-[#171717] mb-2">No Reports Yet</h3>
            <p className="text-[#737373] mb-6">
              Generate your first report by running an analysis
            </p>
            <Link href="/analysis">
              <Button className="rounded-xl">
                Go to Analysis
              </Button>
            </Link>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-6">
          {reports.map((report) => (
            <Card key={report.session_id} className="hover:shadow-md transition-all">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <CardTitle className="text-[#171717] flex items-center gap-2">
                      <FileText className="h-5 w-5 text-[#5B197B]" />
                      {report.title}
                    </CardTitle>
                    <CardDescription className="flex items-center gap-2 mt-2">
                      <Calendar className="h-4 w-4" />
                      Generated: {formatDate(report.generated_at)}
                    </CardDescription>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleDelete(report.session_id)}
                    className="text-[#DC2626] hover:text-[#991B1B]"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-3">
                  <Button
                    variant="outline"
                    onClick={() => window.open(`http://localhost:8000${report.html_url}`, '_blank')}
                    className="rounded-xl"
                  >
                    <Eye className="h-4 w-4 mr-2" />
                    View HTML
                  </Button>
                  {report.pdf_url && (
                    <Button
                      variant="outline"
                      onClick={() => handleDownload(report.pdf_url!, `${report.title}.pdf`)}
                      className="rounded-xl"
                    >
                      <Download className="h-4 w-4 mr-2" />
                      Download PDF
                    </Button>
                  )}
                  {report.docx_url && (
                    <Button
                      variant="outline"
                      onClick={() => handleDownload(report.docx_url!, `${report.title}.docx`)}
                      className="rounded-xl"
                    >
                      <Download className="h-4 w-4 mr-2" />
                      Download DOCX
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}

