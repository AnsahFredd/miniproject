import React from "react";
import { ButtonProps } from "../../types/customTypes";

const Button = ({ label, isLoading, onClick, otherStyles, animationStyles }: ButtonProps) => {
  return (
    <div className="w-full md:max-w-md flex items-center justify-center">
      <button
        onClick={onClick}
        disabled={isLoading}
        className={`w-full h-[44px] rounded-xl font-semibold tracking-wide shadow-md
          transition-all duration-300 ease-in-out
          disabled:opacity-50 disabled:cursor-not-allowed
          ${otherStyles} ${animationStyles || ""}
        `}
      >
        {isLoading ? (
          <span className="animate-pulse">Loading...</span>
        ) : (
          <span>{label}</span>
        )}
      </button>
    </div>
  );
};

export default Button;
