import * as React from "react";
import { AxiosInstance } from "axios"


// Nav items props declarations
export interface NavItems {
  id: number; // Unique identifier for each navigation item
  label: string; // Text shown in the nav item
  path: string; // The route or URL it links to
}

// Props for a custom button component
export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  label: string;               // Text shown on the button
  isLoading?: boolean;         // If true, shows a loading indicator
  otherStyles?: string;        // Tailwind styling
  animationStyles?: string;    // Dynamic Tailwind animation class (optional)
  onClick?: () => void;        // Button click handler
}


// Form types declaration
// types/customTypes.ts
import { ChangeEvent, FormEvent, ReactElement } from "react";

export interface Field {
  label: string;
  name: string;
  type: string;
  placeholder: string;
  required?: boolean;
}

export interface FormProps {
  fields: Field[];
  onChange: (e: ChangeEvent<HTMLInputElement>) => void;
  onSubmit?: (e?: FormEvent) => void;
  submitButton?: ReactElement;
}


// AuthContext Types D{ecalration

// This interface defines the shape of a "User" object
export interface User {
  id: string;
  full_name: string;
  email: string;
  roles?: string[];
  permission?: string[];
}

export interface SignupPayload {
  email: string;
  password: string;
  name?: string;
}

// This interface defines what data and functions will be shared in AuthContext
export interface AuthContextType {
  user: User | null; // Not string!
  token: string | null;
  loading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<{ accessToken: string; user: User }>;
  signup: (payload: SignupPayload) => Promise<{ message: string }>;
  logout: () => void; // since you're not returning a Promise
  refreshToken: () => Promise<string | null>;
  hasRole: (role: string) => boolean;
  hasPermission: (permission: string) => boolean;

  requestPasswordReset: (email: string) => Promise<void>;
  resetPassword: (token: string, newPassword: string) => Promise<void>;
}


// Security Headers type for backend response validation
export interface SecurityHeaders {
  'Content-Security-Policy'?: string;
  'X-Frame-Options'?: string;
  'X-Content-Type-Options'?: string;
  'Strict-Transport-Security'?: string;
  'X-XSS-Protection'?: string;
}


// API Response types
export interface ApiResponse<T = any> {
  success: boolean;
  data: T;
  message?: string;
  errors?: string[];
}

export interface AuthResponse {
  accessToken: string;
  user: User;
  expiresIn?: number;
}


export interface ClauseItem {
  icon: string;
  title: string;
  subtitle: string;
  value: string;
}
