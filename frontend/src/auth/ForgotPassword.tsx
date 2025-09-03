import React, { useState } from "react";
import Form from "../components/ui/Form";
import Button from "../components/ui/Button";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "./AuthContext";

const ForgotPassword = () => {
const [isloading, setIsLoading] = useState(false);
const [email, setEmail] = useState("");
const { requestPasswordReset } = useAuth();
const navigate = useNavigate();

const fields = [
  {
    label: "Email",
    name: "email",
    type: "email",
    placeholder: "Enter your email",
    required: true,
  },
];

const handleInputChnage = (e: React.ChangeEvent<HTMLInputElement>) => {
  const { name, value } = e.target;

  if (name === "email") {
    setEmail(value);
  }
};

const handlePasswordReset = async () => {
  setIsLoading(true);
  try {
    await requestPasswordReset(email);
    navigate("/check-email?type=reset");
  } catch (error) {
    console.log("Error", error);
  } finally {
    setIsLoading(false);
  }
};

return (
  <>
    <div className="flex flex-col items-center justify-center mt-24 gap-4 px-6">
      <h1 className="text-4xl font-semibold text-[var(--color-primary)]">
        Forgot password?
      </h1>
      <p className="text-[var(--color-secondary)] text-sm md:text-lg">
        Enter the email address associated with your account to a link to
        reset your password
      </p>
      <Form fields={fields} onChange={handleInputChnage} />
      <Button
        onClick={handlePasswordReset}
        label="Send reset link"
        isLoading={isloading}
        otherStyles="btn btn-primary"
      />

        <p className="text-[var(--color-secondary)] text-sm md:text-lg flex items-center whitespace-nowrap">
      Remember your password?&nbsp;
      <Link to="/login" className="link-accent">
        Log in
      </Link>
    </p>

    </div>
  </>
);
};

export default ForgotPassword;
