// src/ForgotPassword.js
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './Login.css';

export default function ForgotPassword() {
    const [email, setEmail] = useState('');
    const [message, setMessage] = useState('');
    const navigate = useNavigate();

    const handleReset = async e => {
        e.preventDefault();
        const host = window.location.hostname;
        try {
            const res = await fetch(`http://${host}:5001/api/forgot-password`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email }),
            });
            if (!res.ok) throw new Error(`Server error ${res.status}`);
            const data = await res.json();
            setMessage(data.message);
        } catch (err) {
            console.error('Forgot password error:', err);
            setMessage('Unable to send reset link. Please check your server or email setup.');
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
            {/* <p className="message">
                {message ||
                    'Enter your registered email address. You’ll receive a link to set and confirm a new password.'}
            </p> */}
            <button className="cancel-link" onClick={() => navigate('/')}>
                Back to Login
            </button>
        </div>
    );
}
