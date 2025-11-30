'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Users } from 'lucide-react'

export default function TeamPage() {
  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div className="text-center space-y-4 py-6">
        <h1 className="text-4xl font-bold text-[#171717]">Team</h1>
        <p className="text-[#737373] text-lg">
          Information about the FEMSTAT team
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            About FEMSTAT
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4 text-[#737373]">
            <p>
              <strong className="text-[#5B197B]">FEMSTAT</strong> is developed by <strong>Femanalytica</strong>, 
              a team dedicated to advancing gender equity through data-driven insights.
            </p>
            <p>
              Our platform combines rigorous statistical methods with gender-transformative approaches 
              to help organizations understand and address gender disparities in their data.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

