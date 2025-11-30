import { render, screen } from '@testing-library/react'
import HomePage from '@/app/page'

describe('HomePage', () => {
  it('renders the main heading', () => {
    render(<HomePage />)
    
    const heading = screen.getByRole('heading', { level: 1 })
    expect(heading).toHaveTextContent('Gender Analysis Tool')
  })

  it('renders the upload button', () => {
    render(<HomePage />)
    
    const uploadButton = screen.getByRole('link', { name: /start analysis/i })
    expect(uploadButton).toBeInTheDocument()
  })

  it('renders feature cards', () => {
    render(<HomePage />)
    
    expect(screen.getByText('Upload Data')).toBeInTheDocument()
    expect(screen.getByText('Configure')).toBeInTheDocument()
    expect(screen.getByText('View Results')).toBeInTheDocument()
    expect(screen.getByText('Export Report')).toBeInTheDocument()
  })
})

