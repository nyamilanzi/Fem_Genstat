'use client'

import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Upload, BarChart3, FileText, Shield, TrendingUp, Sparkles } from 'lucide-react'

export default function LandingPage() {
  return (
    <div className="min-h-screen">
      {/* Hero Section - Purple Background */}
      <div className="bg-gradient-to-br from-[#5B197B] via-[#7B2CBF] to-[#9D4EDD] py-20 px-6">
        <div className="max-w-4xl mx-auto text-center space-y-8">
          <h1 className="text-5xl md:text-6xl font-bold text-white leading-tight">
            Transform Your Data Into<br />Gender Equity Insights
          </h1>
          <p className="text-xl text-white/90 max-w-2xl mx-auto">
            Upload datasets, analyze gender-disaggregated data, and generate comprehensive reports with Femanalytica Insight
          </p>
          <div className="pt-6">
            <Link href="/analysis">
              <Button size="lg" className="bg-white text-[#5B197B] hover:bg-white/90 text-lg px-8 py-6 rounded-xl shadow-lg">
                Get Started
                <TrendingUp className="ml-2 h-5 w-5" />
              </Button>
            </Link>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="py-16 px-6 bg-white">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-bold text-[#171717] mb-4">
              Powerful Gender Analysis Platform
            </h2>
            <p className="text-lg text-[#737373] max-w-2xl mx-auto">
              Comprehensive tools for gender-stratified statistical analysis and bias assessment
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="p-8 rounded-2xl border-[0.5px] border-[#E5E5E5] bg-white hover:shadow-md transition-all">
              <div className="w-14 h-14 rounded-xl bg-[#5B197B] flex items-center justify-center mb-4">
                <Upload className="h-7 w-7 text-white" />
              </div>
              <h3 className="text-xl font-semibold text-[#171717] mb-3">Easy Data Upload</h3>
              <p className="text-[#737373]">
                Upload CSV, Excel, SPSS, or Stata files. Our platform automatically detects variable types and suggests gender columns.
              </p>
            </div>

            <div className="p-8 rounded-2xl border-[0.5px] border-[#E5E5E5] bg-white hover:shadow-md transition-all">
              <div className="w-14 h-14 rounded-xl bg-[#5B197B] flex items-center justify-center mb-4">
                <BarChart3 className="h-7 w-7 text-white" />
              </div>
              <h3 className="text-xl font-semibold text-[#171717] mb-3">Comprehensive Analysis</h3>
              <p className="text-[#737373]">
                Perform gender-stratified statistical tests, effect size calculations, and gender bias assessments using proven methodologies.
              </p>
            </div>

            <div className="p-8 rounded-2xl border-[0.5px] border-[#E5E5E5] bg-white hover:shadow-md transition-all">
              <div className="w-14 h-14 rounded-xl bg-[#5B197B] flex items-center justify-center mb-4">
                <FileText className="h-7 w-7 text-white" />
              </div>
              <h3 className="text-xl font-semibold text-[#171717] mb-3">Professional Reports</h3>
              <p className="text-[#737373]">
                Generate comprehensive reports with textual explanations, gender bias assessments, and actionable recommendations.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* What is FEMSTAT Section */}
      <div className="py-16 px-6 bg-[#F5F5F5]">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-bold text-[#171717] mb-4">What is FEMSTAT?</h2>
          </div>
          
          <div className="space-y-6 text-[#737373] text-lg leading-relaxed">
            <p>
              <strong className="text-[#5B197B]">FEMSTAT</strong> is a professional gender analysis platform developed by <strong>Femanalytica</strong> that enables researchers, 
              organizations, and policymakers to conduct comprehensive gender-stratified statistical analysis.
            </p>
            
            <p>
              Our platform uses <strong>gender-transformative approaches</strong> and established gender analysis frameworks to help you:
            </p>
            
            <ul className="space-y-3 list-disc list-inside ml-4">
              <li>Identify gender-based differences and disparities in your data</li>
              <li>Assess gender bias using multiple analytical dimensions</li>
              <li>Generate actionable insights and recommendations</li>
              <li>Create professional reports suitable for publication and decision-making</li>
              <li>Understand the root causes of gender inequalities</li>
            </ul>
            
            <p>
              FEMSTAT combines rigorous statistical methods with gender analysis expertise to provide you with 
              comprehensive insights that go beyond simple descriptive statistics.
            </p>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="py-16 px-6 bg-gradient-to-r from-[#5B197B] to-[#7B2CBF]">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-4xl font-bold text-white mb-6">
            Ready to Transform Your Data?
          </h2>
          <p className="text-xl text-white/90 mb-8">
            Start analyzing your data today and discover gender equity insights
          </p>
          <Link href="/analysis">
            <Button size="lg" className="bg-white text-[#5B197B] hover:bg-white/90 text-lg px-8 py-6 rounded-xl shadow-lg">
              Start Analysis
              <Sparkles className="ml-2 h-5 w-5" />
            </Button>
          </Link>
        </div>
      </div>
    </div>
  )
}
