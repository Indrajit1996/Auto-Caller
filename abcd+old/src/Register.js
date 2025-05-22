// src/Register.js
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './App.css';

export default function Register() {
    const [email, setEmail] = useState('');
    const [message, setMessage] = useState('');
    const navigate = useNavigate();

    const handleRegister = async e => {
        e.preventDefault();
        console.log('Registering email:', email);
        try {
            const res = await fetch('/api/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email }),
            });
            console.log('Raw response:', res);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();
            console.log('Register response JSON:', data);
            setMessage(data.message);
        } catch (err) {
            console.error('Register error:', err);
            setMessage('Unable to send verification link. Please check the server.');
        }
    };

    return (
        <div className="login-container">
            <h2>Register</h2>
            <form onSubmit={handleRegister}>
                <input
                    type="email"
                    value={email}
                    onChange={e => setEmail(e.target.value)}
                    placeholder="Enter your email"
                    required
                />
                <button type="submit">Send Verification Link</button>
            </form>
            <button className="cancel-link" onClick={() => navigate('/')}>
                Back to Login
            </button>
            {message && <p className="message">{message}</p>}
        </div>
    );
}
