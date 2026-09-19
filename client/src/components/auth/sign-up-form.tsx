"use client";

import {
  createUserWithEmailAndPassword,
  sendEmailVerification,
} from "firebase/auth";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { getFirebaseAuth } from "@/lib/firebase";
import {
  type RegistrationErrors,
  type RegistrationValues,
  validateRegistration,
} from "@/lib/registration-validation";

const years = [2025, 2026, 2027, 2028, 2029];
const inputClass =
  "mt-1 block w-full rounded-lg border border-brand-green-light px-4 py-3 text-sm text-brand-text-dark focus:border-brand-green focus:outline-none";

type FormValues = RegistrationValues & { email: string };

const initialValues: FormValues = {
  fullName: "",
  email: "",
  graduationYear: "",
  discipline: "",
  password: "",
  confirmPassword: "",
};

export default function SignUpForm() {
  const [values, setValues] = useState(initialValues);
  const [errors, setErrors] = useState<RegistrationErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [verified, setVerified] = useState(false);
  const [message, setMessage] = useState("");

  const update = (name: keyof FormValues, value: string) => {
    setValues((current) => ({ ...current, [name]: value }));
  };

  const submit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const validationErrors = validateRegistration(values);
    if (!values.email.trim())
      validationErrors.email = "Enter your email address.";
    setErrors(validationErrors);
    setMessage("");
    if (Object.keys(validationErrors).length) return;

    setIsSubmitting(true);
    try {
      const credential = await createUserWithEmailAndPassword(
        getFirebaseAuth(),
        values.email.trim(),
        values.password,
      );
      await sendEmailVerification(credential.user, {
        url: `${window.location.origin}/sign-in`,
      });
      setVerified(true);
    } catch {
      setMessage(
        "We could not create your account. Check your details and try again.",
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  if (verified) {
    return (
      <div className="rounded-xl border border-brand-green-light bg-brand-surface p-6 text-center">
        <h2 className="text-xl font-bold text-brand-text-dark">
          Check your email.
        </h2>
        <p className="mt-3 text-brand-text-light">
          Verify the link sent to {values.email}, then sign in to complete your
          member profile.
        </p>
      </div>
    );
  }

  return (
    <form onSubmit={submit} noValidate>
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        <TextField
          label="Full Name"
          name="fullName"
          type="text"
          values={values}
          error={errors.fullName}
          update={update}
        />
        <TextField
          label="Email"
          name="email"
          type="email"
          values={values}
          error={errors.email}
          update={update}
        />
        <div>
          <label
            htmlFor="graduationYear"
            className="block font-medium text-brand-text-dark"
          >
            Graduation Year*
          </label>
          <select
            id="graduationYear"
            value={values.graduationYear}
            onChange={(event) => update("graduationYear", event.target.value)}
            className={`${inputClass} bg-white`}
          >
            <option value="">Year</option>
            {years.map((year) => (
              <option key={year} value={year}>
                {year}
              </option>
            ))}
          </select>
          <ErrorText error={errors.graduationYear} />
        </div>
        <TextField
          label="Discipline"
          name="discipline"
          type="text"
          values={values}
          error={errors.discipline}
          update={update}
        />
        <TextField
          label="Password"
          name="password"
          type="password"
          values={values}
          error={errors.password}
          update={update}
        />
        <TextField
          label="Confirm Password"
          name="confirmPassword"
          type="password"
          values={values}
          error={errors.confirmPassword}
          update={update}
        />
      </div>
      {message ? (
        <p className="mt-5 text-center text-sm text-red-700">{message}</p>
      ) : null}
      <Button
        type="submit"
        disabled={isSubmitting}
        className="mx-auto mt-8 block w-full max-w-md bg-brand-green text-brand-surface hover:bg-brand-yellow hover:text-brand-brown disabled:opacity-60"
      >
        {isSubmitting ? "Creating account..." : "Create Account"}
      </Button>
    </form>
  );
}

function TextField({
  label,
  name,
  type,
  values,
  error,
  update,
}: {
  label: string;
  name: keyof FormValues;
  type: "email" | "password" | "text";
  values: FormValues;
  error?: string;
  update: (name: keyof FormValues, value: string) => void;
}) {
  return (
    <div>
      <label htmlFor={name} className="block font-medium text-brand-text-dark">
        {label}*
      </label>
      <input
        id={name}
        type={type}
        value={values[name]}
        onChange={(event) => update(name, event.target.value)}
        className={inputClass}
        minLength={type === "password" ? 8 : undefined}
      />
      <ErrorText error={error} />
    </div>
  );
}

function ErrorText({ error }: { error?: string }) {
  return error ? <p className="mt-1 text-sm text-red-700">{error}</p> : null;
}
