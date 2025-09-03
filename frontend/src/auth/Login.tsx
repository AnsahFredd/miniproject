import React, { useEffect, useState } from "react";
import Form from "../components/ui/Form";
import Button from "../components/ui/Button";
import AuthSpinner from "../components/ui/AuthSpinner";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "./AuthContext";
import { useLocation } from "react-router-dom";

const API = import.meta.env.VITE_API_BASE_URL

const Login: React.FC = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [showSpinner, setShowSpinner] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [showResendOption, setShowResendOption] = useState(false);

  const location = useLocation()
  const params = new URLSearchParams(location.search)
  const isConfirmed = params.get("confirmed") === "true"
  const status = params.get("status")

  const navigate = useNavigate();
  const { login } = useAuth();

  const fields = [
    {
      label: "Email",
      name: "email",
      type: "email",
      placeholder: "Enter your email",
      required: true,
    },
    {
      label: "Password",
      name: "password",
      type: "password",
      placeholder: "Enter password",
      required: true,
    },
  ];

  // Clear confirmation message after 5 seconds
  useEffect(() => {
    if (isConfirmed && status === "success") {
      setError("")
      const timer = setTimeout(() => {
        // Remove the confirmed parameter from URL
        navigate(location.pathname, { replace: true })
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [isConfirmed, status, navigate, location.pathname]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    if (name === "email") setEmail(value);
    else if (name === "password") setPassword(value);
    if (error) {
      setError("");
      setShowResendOption(false);
    }
  };
  const handleLogin = async (e?: React.FormEvent) => {
    e?.preventDefault();

    if (!email || !password) {
      setError("Please fill in all fields");
      return;
    }

    setIsLoading(true);
    setShowSpinner(true);
    setError("");
    setShowResendOption(false);

    try {
      await login(email, password);
      navigate("/dashboard");
    } catch (err: any) {
      const errorMessage = err?.message || "Login failed. Please check your credentials.";
      setError(errorMessage);
      
      if (errorMessage.toLowerCase().includes('verify') || 
          errorMessage.toLowerCase().includes('confirm') ||
          errorMessage.toLowerCase().includes('not verified')) {
        setShowResendOption(true);
      }
    } finally {
      setIsLoading(false);
      setShowSpinner(false);
    }
  };

  const handleResendConfirmation = async () => {
    if (!email) {
      setError("Please enter your email address first");
      return;
    }

    try {
      const response = await fetch(`${API}/auth/resend-confirmation`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email }),
      });

      if (response.ok) {
        setError("Confirmation email sent! Please check your inbox.");
        setShowResendOption(false);
      } else {
        const data = await response.json();
        setError(data.detail || "Failed to resend confirmation email");
      }
    } catch (err) {
      setError("Failed to resend confirmation email");
    }
  };


  return (
    <>
      {/* Full screen spinner overlay */}
      <AuthSpinner 
        isVisible={showSpinner} 
        message="Signing you in... Verifying your credentials and preparing your dashboard!"
      />

      <div className="flex flex-col items-center justify-center mt-12 gap-4 px-6">
        <h1 className="text-4xl font-semibold text-[var(--color-primary)]">Welcome back</h1>
        {/* Confirmation success message */}
        {isConfirmed && status === "success" && (
          <div className="bg-[color:rgb(20_184_166_/_10%)] border border-[color:rgb(20_184_166_/_26%)] text-[var(--color-primary)] px-4 py-3 rounded w-full max-w-md text-center" role="status" aria-live="polite">
            Your email has been confirmed! Please log in.
          </div>
        )}

        {error && (
          <div className="bg-[var(--bg-soft)] border border-gray-200 text-[var(--color-primary)] px-4 py-3 rounded w-full max-w-md" role="alert" aria-live="assertive">
            {error}
            {showResendOption && (
              <div className="mt-2">
                <button
                  onClick={handleResendConfirmation}
                  className="link-accent text-sm transition-colors">
                  Resend confirmation email
                </button>
              </div>
            )}
          </div>
        )}

        <Form
          fields={fields}
          onChange={handleInputChange}
          onSubmit={handleLogin}
          submitButton={
            <Button
              type="submit"
              label={isLoading ? "Signing in..." : "Login"}
              isLoading={isLoading}
              disabled={!email || !password || isLoading}
              otherStyles="btn btn-primary w-[300px] mx-11 lg:mx-0"
            />
          }
        />

        <div className="w-full max-w-md mr-6 text-right">
          <Link 
            to="/reset-password" 
            className="text-sm md:text-base link-accent transition-colors"
          >
            Forgot password?
          </Link>
        </div>

        <p className="text-[var(--color-secondary)] mt-8 text-center">
          Don&apos;t have an account?{" "}
          <Link to="/signup" className="link-accent transition-colors mb-3">
            Sign up
          </Link>
        </p>
      </div>
    </>
  );
};

export default Login;
