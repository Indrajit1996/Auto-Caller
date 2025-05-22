// src/ResetPassword.js
import React, { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import './App.css';

export default function ResetPassword() {
    const [searchParams] = useSearchParams();
    const token = searchParams.get('token') || '';

    const [newUsername, setNewUsername] = useState('');
    const [confirmUsername, setConfirmUsername] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [message, setMessage] = useState('');

    const handleReset = async (e) => {
        e.preventDefault();

        // Validation
        if (newUsername !== confirmUsername) {
            setMessage('Usernames do not match.');
            return;
        }

        if (newPassword !== confirmPassword) {
            setMessage('Passwords do not match.');
            return;
        }

        try {
            const res = await fetch('/api/reset-password', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ token, newUsername, newPassword }),
            });

            if (!res.ok) throw new Error(`Server error ${res.status}`);
            const data = await res.json();
            setMessage(data.message);
        } catch (err) {
            console.error('Reset error:', err);
            setMessage('Unable to reset password. Please try again.');
        }
    };

    return (
        <div className="login-container">
            <h2>Set New Username & Password</h2>
            <form onSubmit={handleReset}>
                <input
                    type="text"
                    value={newUsername}
                    onChange={e => setNewUsername(e.target.value)}
                    placeholder="New Username"
                    required
                />
                <input
                    type="text"
                    value={confirmUsername}
                    onChange={e => setConfirmUsername(e.target.value)}
                    placeholder="Confirm Username"
                    required
                />
                <input
                    type="password"
                    value={newPassword}
                    onChange={e => setNewPassword(e.target.value)}
                    placeholder="New Password"
                    required
                />
                <input
                    type="password"
                    value={confirmPassword}
                    onChange={e => setConfirmPassword(e.target.value)}
                    placeholder="Confirm Password"
                    required
                />
                <button type="submit">Update Credentials</button>
            </form>
            {message && <p className="message">{message}</p>}
        </div>
    );
}
