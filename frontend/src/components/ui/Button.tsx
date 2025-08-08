import React from "react";
import { ButtonProps } from "../../types/customTypes";

const Button = ({ label, isLoading, onClick, otherStyles, animationStyles, ...rest }: ButtonProps) => {
  return (
    <div className="w-full md:max-w-md flex items-center justify-center">
      <button
        onClick={onClick}
        disabled={isLoading || rest.disabled}
        className={`btn ${otherStyles ? otherStyles : "btn-primary"} ${animationStyles || ""}`}
        {...rest}
      >
        {isLoading ? (
          <span className="animate-pulse" aria-live="polite">Loading...</span>
        ) : (
          <span>{label}</span>
        )}
      </button>
    </div>
  );
};

export default Button;
