import React, { useState, useEffect } from 'react';
import Dashboard from './components/Dashboard';
import Login from './components/Login';
import './App.css';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    // Check if user is already authenticated
    const auth = localStorage.getItem('dashboard_auth');
    setIsAuthenticated(auth === 'true');
    setIsChecking(false);
  }, []);

  const handleLogin = () => {
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    localStorage.removeItem('dashboard_auth');
    setIsAuthenticated(false);
  };

  if (isChecking) {
    return null; // Or a loading spinner
  }

  return (
    <div className="App">
      {isAuthenticated ? (
        <Dashboard onLogout={handleLogout} />
      ) : (
        <Login onLogin={handleLogin} />
      )}
    </div>
  );
}

export default App;
