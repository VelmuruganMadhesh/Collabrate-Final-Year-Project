import { StrictMode } from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'

import './index.css'
import App from './App'
import { logger } from './utils/logger'

logger.info('Frontend application starting', {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
})

ReactDOM.createRoot(document.getElementById('app')!).render(
  <StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </StrictMode>,
)

