import React, { useState } from "react";
import { useAuth } from "./AuthContext";
import AuthSpinner from "../components/ui/AuthSpinner";
import Form from "../components/ui/Form";
import Button from "../components/ui/Button";
import { Link, useNavigate } from "react-router-dom";


const Signup = () => {
  const { signup } = useAuth();

  const [form, setForm] = useState({ name: "", email: "", password: "" });
  const [error, setError] = useState("");
  const [showSpinner, setShowSpinner] = useState(false);
  const [loading, setLoading] = useState(false);

  const navigate = useNavigate()

  const fields = [
    { label: "Name", name: "name", type: "text", placeholder: "Your full name", required: true },
    { label: "Email", name: "email", type: "email", placeholder: "Email address", required: true },
    { label: "Password", name: "password", type: "password", placeholder: "Choose a password", required: true },
  ];

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
    if (error) setError("");
  };

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setShowSpinner(true);
    setError("");

    try {
      await signup(form)
      navigate("/check-email?type=confirm");
    } catch (err: any) {
      setError(err?.message || "Signup failed");
    } finally {
      setLoading(false);
      setShowSpinner(false);
    }
  };

  return (
    <>
      <AuthSpinner
        isVisible={showSpinner}
        message="Creating your account... Please wait while we set up everything for you!"
      />

      <form onSubmit={handleSignup} className="flex flex-col gap-6 items-center mt-12 px-6">
        <h1 className="text-3xl font-bold text-[var(--color-primary)]">Sign up to LawLens</h1>
        {error && (
          <div className="text-[var(--color-primary)] border border-gray-200 p-2 rounded bg-[var(--bg-soft)] max-w-md w-full text-center" role="alert" aria-live="assertive">
            {error}
          </div>
        )}
          
        <Form fields={fields} onChange={handleChange} />

        <Button
          label={loading ? "Signing up..." : "Sign up"}
          isLoading={loading}
          disabled={loading || !form.email || !form.password || !form.name}
          otherStyles="btn btn-primary w-full mx-11 lg:mx-0 max-w-md"
        />
        <p className="text-[var(--color-secondary)] mt-4 text-center mb-4">
          Already have an account?{" "}
          <Link to="/login" className="link-accent transition-colors">
            Log in
          </Link>
        </p>
      </form>
    </>
  );
};

export default Signup;
