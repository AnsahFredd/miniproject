import React from "react";
import { useSearchParams } from "react-router-dom";

const CheckEmail = () => {
  const [searchParams] = useSearchParams();
  const type = searchParams.get("type"); 

  const title = "Check your inbox";
  const message =
    type === "confirm"
      ? "We've sent a confirmation link to your email. Please check your inbox and click the link to verify your account."
      : "We've sent a password reset link to your email. Please click the link to reset your password.";

  return (
    <div className="flex flex-col items-center justify-center mt-20 gap-4">
      <h1 className="text-3xl font-semibold text-[var(--color-primary)]">{title}</h1>
      <p className="text-[var(--color-secondary)] text-md max-w-md text-center">{message}</p>
    </div>
  );
};

export default CheckEmail;
