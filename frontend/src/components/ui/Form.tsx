import React from "react";
import { FormProps } from "../../types/customTypes";

const Form = ({ fields, onChange, onSubmit, submitButton }: FormProps) => {
  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        if (onSubmit) onSubmit(e);
      }}
      className="flex flex-col gap-5 p-5 w-full md:max-w-md mx-4 md:mx-0 card animate-slide-up"
    >
      {fields.map((field, index) => {
        const id = `field-${field.name || index}`;
        return (
          <div key={index} className="flex flex-col gap-2">
            <label className="text-sm font-semibold text-[var(--color-primary)]" htmlFor={id}>
              {field.label}
            </label>
            <input
              id={id}
              placeholder={field.placeholder}
              name={field.name}
              type={field.type}
              onChange={onChange}
              aria-required={field.required ? "true" : "false"}
              required={field.required}
              className="input"
              autoComplete={field.type === "password" ? "new-password" : "on"}
            />
          </div>
        );
      })}
      {submitButton && <div>{submitButton}</div>}
    </form>
  );
};

export default Form;
