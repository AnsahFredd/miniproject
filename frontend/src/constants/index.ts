import { NavItems } from "../types/customTypes";
import type { Field } from "../types/customTypes";

export const navItems: NavItems[] = [
  {
    id: 2,
    label: "Dashboard",
    path: "/dashboard",
  },
  {
    id: 3,
    label: "Documents",
    path: "/document",
  },
  {
    id: 4,
    label: "Search & QA",
    path: "/search",
  },
  {
    id: 5,
    label: "Settings",
    path: "/settings",
  },
];

// Define form fields (organization optional)
export const fields: Field[] = [
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
    placeholder: "Enter your password",
    required: true,
  },
  {
    label: "Confrim Password",
    name: "confirmPassword",
    type: "password",
    placeholder: "Confirm Password",
    required: true,
  },
  {
    label: "Organization (optional)",
    name: "organization",
    type: "text",
    placeholder: "Enter your organization",
    required: false,
  },
];
