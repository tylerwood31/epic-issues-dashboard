import React, { useState } from 'react';
import './Login.css';

const Login = ({ onLogin }) => {
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    const API_URL = process.env.REACT_APP_API_URL || '';

    try {
      const response = await fetch(`${API_URL}/auth/login?password=${encodeURIComponent(password)}`, {
        method: 'POST',
      });

      const data = await response.json();

      if (data.success) {
        // Store authentication in localStorage
        localStorage.setItem('dashboard_auth', 'true');
        onLogin();
      } else {
        setError('Invalid password. Please try again.');
        setPassword('');
      }
    } catch (err) {
      setError('Failed to connect to server. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-header">
          <h1>EPIC Issues Dashboard</h1>
          <p>Please enter the password to access the dashboard</p>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          <div className="form-group">
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter password"
              className="password-input"
              autoFocus
              disabled={loading}
            />
          </div>

          {error && <div className="error-message">{error}</div>}

          <button
            type="submit"
            className="login-button"
            disabled={loading || !password}
          >
            {loading ? 'Authenticating...' : 'Access Dashboard'}
          </button>
        </form>

        <div className="login-footer">
          <p>Protected access • CoverWallet Internal</p>
        </div>
      </div>
    </div>
  );
};

export default Login;
