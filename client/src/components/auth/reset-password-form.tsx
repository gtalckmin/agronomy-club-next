"use client";

import { sendPasswordResetEmail } from "firebase/auth";
import Link from "next/link";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { getFirebaseAuth } from "@/lib/firebase";

export default function ResetPasswordForm() {
  const [email, setEmail] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [message, setMessage] = useState("");
  const submit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsSubmitting(true);
    try {
      await sendPasswordResetEmail(getFirebaseAuth(), email.trim(), {
        url: `${window.location.origin}/sign-in`,
      });
      setMessage(
        "If this address has an account, a password reset email has been sent.",
      );
    } catch {
      setMessage(
        "We could not start a password reset. Please try again shortly.",
      );
    } finally {
      setIsSubmitting(false);
    }
  };
  return (
    <form onSubmit={submit}>
      <label htmlFor="email" className="block font-medium text-brand-text-dark">
        Email
      </label>
      <input
        id="email"
        type="email"
        required
        value={email}
        onChange={(event) => setEmail(event.target.value)}
        className="mt-1 block w-full rounded-lg border border-brand-green-light px-4 py-3 text-sm text-brand-text-dark focus:border-brand-green focus:outline-none"
      />
      {message ? (
        <p className="mt-5 text-center text-sm text-brand-text-light">
          {message}
        </p>
      ) : null}
      <Button
        type="submit"
        disabled={isSubmitting}
        className="mt-8 w-full bg-brand-green text-brand-surface hover:bg-brand-yellow hover:text-brand-brown disabled:opacity-60"
      >
        {isSubmitting ? "Sending reset email..." : "Send reset email"}
      </Button>
      <p className="mt-5 text-center text-sm">
        <Link
          href="/sign-in"
          className="font-semibold text-brand-green underline hover:text-brand-yellow"
        >
          Return to sign in
        </Link>
      </p>
    </form>
  );
}
