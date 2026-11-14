import { useState } from 'react';
// import heroImg from './assets/hero.png'
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import "./App.css";


function App() {
  const [count, setCount] = useState(0);
  const isAuth = true;

  return (
    <>
    {
      isAuth
      ? <DashboardPage />
      : <LoginPage />
    }
    </>
  )
}

export default App
