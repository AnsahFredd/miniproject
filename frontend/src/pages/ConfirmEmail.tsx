import React, { useEffect, useState } from 'react';
import { useSearchParams, Link, useNavigate } from 'react-router-dom';
import axios from 'axios';

const API = import.meta.env.VITE_API_BASE_URL;

const ConfirmEmail: React.FC = () => {
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();
    const [message, setMessage] = useState("Confirming your email...");
    const [resendStatus, setResendStatus] = useState<string | null>(null);
    const [showResend, setShowResend] = useState(false);
    const [isSuccess, setIsSuccess] = useState(false);
    const [isLoading, setIsLoading] = useState(true);
    
    const token = searchParams.get("token");
    const email = searchParams.get("email");
    const status = searchParams.get("status");
    const urlMessage = searchParams.get("message");

    useEffect(() => {
        // Handle direct confirmation via token using window.location
        const confirmEmailWithToken = () => {
            // Instead of axios call, redirect directly to the backend endpoint
            // The backend will handle the confirmation and redirect appropriately
            window.location.href = `${API}/auth/confirm-email?token=${token}`;
        };

        // Handle status from redirect (like from backend)
        const handleStatus = () => {
            if (status === 'success') {
                setMessage("Email confirmed successfully! You can now log in.");
                setIsSuccess(true);
                setShowResend(false);
                setIsLoading(false);
                return true;
            }

            if (status === 'already_confirmed') {
                setMessage("Your email is already confirmed! You can log in now.");
                setIsSuccess(true);
                setShowResend(false);
                setIsLoading(false);
                return true;
            }

            if (status === 'info') {
                const infoMessage = urlMessage?.replace(/_/g, ' ') || 
                    "If you have already confirmed your email, please log in. Otherwise, request a new confirmation email.";
                setMessage(infoMessage);
                setIsSuccess(false);
                setShowResend(true);
                setIsLoading(false);
                return true;
            }

            if (status === "error") {
                let errorMsg = "Email confirmation failed";
                if (urlMessage === 'no_token') {
                    errorMsg = "No confirmation token found";
                } else if (urlMessage === 'confirmation_failed') {
                    errorMsg = "Email confirmation failed. Please try again.";
                } else if (urlMessage) {
                    errorMsg = urlMessage.replace(/_/g, ' ');   
                }
                setMessage(errorMsg);
                setIsSuccess(false);
                setShowResend(urlMessage !== 'no_token');
                setIsLoading(false);
                return true;
            }
            return false;
        };

        // Check if we have a status from URL (meaning we were redirected from backend)
        if (handleStatus()) {
            return;
        }

        // If we have a token and no status, process the token
        if (token) {
            confirmEmailWithToken();
            return;
        }

        // Handle pending registration case
        if (email && status === 'pending') {
            setMessage("Registration successful! We've sent a confirmation email to your inbox.");
            setShowResend(true);
            setIsLoading(false);
            return;
        }

        // No token and no status
        setMessage("No confirmation token found.");
        setShowResend(false);
        setIsLoading(false);

    }, [token, email, status, urlMessage, navigate]);

    const handleResend = async () => {
        setResendStatus(null);
        try {
            let userEmail = email;
            if (!userEmail) {
                userEmail = prompt("Please enter your email address:") || "";
                if (!userEmail) return;
            }
            
            const response = await axios.post(`${API}/auth/resend-confirmation`, { 
                email: userEmail 
            });
            
            if (response.status === 200) {
                setResendStatus("Confirmation email sent successfully. Please check your inbox.");
                // Update the email in case it was entered via prompt
                if (!email) {
                    navigate(`?email=${encodeURIComponent(userEmail)}&status=pending`, {
                        replace: true
                    });
                }
            }
        } catch (error: any) {
            setResendStatus(
                error.response?.data?.detail || "Failed to resend confirmation email."
            );
        }
    };

    if (isLoading) {
        return (
            <div className='max-w-[500px] m-auto p-[32px] text-center'>
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
                <h2 className="text-xl font-semibold mb-4">Confirming Email</h2>
                <p>Please wait while we confirm your email address...</p>
            </div>
        );
    }

    return (
        <div className='max-w-[500px] m-auto p-[32px] text-center'>
            <div className={`mb-6 ${isSuccess ? 'text-green-600' : 'text-gray-700'}`}>
                {isSuccess && (
                    <div className="text-green-500 text-5xl mb-4">✓</div>
                )}
                <h2 className="text-2xl font-semibold mb-4">
                    {isSuccess ? 'Email Confirmed!' : 'Email Confirmation'}
                </h2>
                <p className="text-base leading-relaxed">{message}</p>
            </div>

            {isSuccess ? (
                <div className="space-y-4">
                    <Link 
                        to="/login" 
                        className="inline-block bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors"
                    >
                        Go to Login
                    </Link>
                </div>
            ) : (
                showResend && (
                    <div className="mt-6 space-y-4">
                        <button 
                            className='bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors'
                            onClick={handleResend}
                        >
                            Resend Confirmation Email
                        </button>
                        
                        {resendStatus && (
                            <div className={`p-3 rounded-lg text-sm ${
                                resendStatus.includes('successfully') 
                                    ? 'bg-green-100 text-green-800' 
                                    : 'bg-red-100 text-red-800'
                            }`}>
                                {resendStatus}
                            </div>
                        )}
                        
                        <p className="text-sm text-gray-600 mt-4">
                            Already confirmed? <Link to="/login" className="text-blue-600 hover:underline">Go to Login</Link>
                        </p>
                    </div>
                )
            )}
        </div>
    );
};

export default ConfirmEmail;
