// src/App.js
import React, { useState, useEffect } from 'react';
import {
    BrowserRouter as Router,
    Routes,
    Route,
    useNavigate,
    useLocation,
    Navigate,
} from 'react-router-dom';
import './App.css';

import Register from './Register';
import VerifyRegistration from './VerifyRegistration';
import ResetPassword from './ResetPassword';
import Dashboard from './Dashboard';

function LoginForm() {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [loginMessage, setLoginMessage] = useState('');
    const navigate = useNavigate();

    const handleLogin = async e => {
        e.preventDefault();
        try {
            const res = await fetch('http://localhost:5001/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password }),
            });
            const data = await res.json();
            setLoginMessage(data.message);
            if (data.success) {
                navigate('/dashboard');
            }
        } catch (err) {
            console.error('Login error', err);
            setLoginMessage('Cannot reach server.');
        }
    };

    return (
        <div className="login-container">
            <h2>Login</h2>
            <form onSubmit={handleLogin}>
                <input
                    type="text"
                    value={username}
                    onChange={e => setUsername(e.target.value)}
                    placeholder="Username"
                    required
                />
                <input
                    type="password"
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                    placeholder="Password"
                    required
                />
                <button type="submit">Login</button>
            </form>

            {/* Forgot Password link */}
            <button
                className="forgot-link"
                onClick={() => {
                    setLoginMessage('');
                    navigate('/forgot-password');
                }}
            >
                Forgot Password or Username?
            </button>

            {/* Register link styled like the forgot link */}
            <button
                className="forgot-link"
                onClick={() => {
                    setLoginMessage('');
                    navigate('/register');
                }}
            >
                Register
            </button>

            {loginMessage && <p className="message">{loginMessage}</p>}
        </div>
    );
}

function ForgotPasswordForm() {
    const [email, setEmail] = useState('');
    const [resetMessage, setResetMessage] = useState('');
    const navigate = useNavigate();

    const handleReset = async (e) => {
        e.preventDefault();
        try {
            const res = await fetch('/api/forgot-password', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email }),
            });
            const data = await res.json();
            setResetMessage(data.message);
        } catch (err) {
            console.error('Forgot-password error', err);
            setResetMessage('Cannot reach server.');
        }
    };

    return (
        <div className="login-container">
            <h2>Forgot Password</h2>
            <form onSubmit={handleReset}>
                <input
                    type="email"
                    value={email}
                    onChange={e => setEmail(e.target.value)}
                    placeholder="Enter your email"
                    required
                />
                <button type="submit">Send Reset Link</button>
            </form>
            <button
                className="cancel-link"
                onClick={() => {
                    setResetMessage('');
                    navigate('/');
                }}
            >
                Cancel
            </button>
            {resetMessage && <p className="message">{resetMessage}</p>}
        </div>
    );
}

function App() {
    const location = useLocation();

    useEffect(() => {
        if (location.pathname === '/register') {
            document.title = 'Register';
        } else if (location.pathname.startsWith('/register/verify')) {
            document.title = 'Verify Registration';
        } else if (location.pathname === '/forgot-password') {
            document.title = 'Reset Password';
        } else if (location.pathname === '/reset-password') {
            document.title = 'Set New Password';
        } else if (location.pathname === '/dashboard') {
            document.title = 'Dashboard';
        } else {
            document.title = 'Login';
        }
    }, [location]);

    return (
        <Routes>
            <Route path="/" element={<LoginForm />} />
            <Route path="/register" element={<Register />} />
            <Route path="/register/verify" element={<VerifyRegistration />} />
            <Route path="/forgot-password" element={<ForgotPasswordForm />} />
            <Route path="/reset-password" element={<ResetPassword />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="*" element={<Navigate to="/" />} />
        </Routes>
    );
}

export default function RoutedApp() {
    return (
        <Router>
            <App />
        </Router>
    );
}
