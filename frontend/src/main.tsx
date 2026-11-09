import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import './style.css';
import './typography.css';
import './responsive.css';
import './icons.css';
import App from './App.tsx';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
