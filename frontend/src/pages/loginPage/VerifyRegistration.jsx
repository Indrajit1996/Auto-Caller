// src/VerifyRegistration.js
import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import './Login.css';

export default function VerifyRegistration() {
    const [searchParams] = useSearchParams();
    const token = searchParams.get('token') || '';
    const [message, setMessage] = useState('Verifying...');

    useEffect(() => {
        if (!token) {
            setMessage('No token provided.');
            return;
        }

        async function verify() {
            try {
                const res = await fetch('/api/register/verify', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ token }),
                });
                const data = await res.json();
                if (!res.ok) throw new Error(data.message || res.status);
                setMessage(data.message);
            } catch (err) {
                console.error('Verification error:', err);
                setMessage(err.message || 'Verification failed.');
            }
        }

        verify();
    }, [token]);

    return (
        <div className="login-container">
            <h2>Verify Registration</h2>
            <p>{message}</p>
        </div>
    );
}
