import React from "react";

interface SeparatorProps {
  orientation?: "horizontal" | "vertical";
  className?: string;
}

export const Separator: React.FC<SeparatorProps> = ({
  orientation = "horizontal",
  className = "",
}) => {
  const baseStyle =
    orientation === "horizontal"
      ? "w-full h-px bg-gray-200 my-4"
      : "w-px h-full bg-gray-200 mx-4";

  return <div className={`${baseStyle} ${className}`} />;
};
