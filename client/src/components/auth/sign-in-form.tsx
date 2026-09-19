"use client";

import { signInWithEmailAndPassword, signOut } from "firebase/auth";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { getFirebaseAuth } from "@/lib/firebase";

export default function SignInForm() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [message, setMessage] = useState("");

  const submit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsSubmitting(true);
    setMessage("");
    try {
      const auth = getFirebaseAuth();
      const credential = await signInWithEmailAndPassword(
        auth,
        email.trim(),
        password,
      );
      await credential.user.reload();
      if (!auth.currentUser?.emailVerified) {
        await signOut(auth);
        setMessage("Verify your email before signing in to the member area.");
        return;
      }
      router.replace("/member");
    } catch {
      setMessage(
        "We could not sign you in. Check your email and password, then try again.",
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
        className={inputClass}
      />
      <label
        htmlFor="password"
        className="mt-5 block font-medium text-brand-text-dark"
      >
        Password
      </label>
      <input
        id="password"
        type="password"
        required
        value={password}
        onChange={(event) => setPassword(event.target.value)}
        className={inputClass}
      />
      <p className="mt-4 text-right text-sm">
        <Link
          href="/reset-password"
          className="underline hover:text-brand-green"
        >
          Forgot password?
        </Link>
      </p>
      {message ? (
        <p className="mt-5 text-center text-sm text-red-700">{message}</p>
      ) : null}
      <Button
        type="submit"
        disabled={isSubmitting}
        className="mt-8 w-full bg-brand-green text-brand-surface hover:bg-brand-yellow hover:text-brand-brown disabled:opacity-60"
      >
        {isSubmitting ? "Signing in..." : "Sign in"}
      </Button>
    </form>
  );
}

const inputClass =
  "mt-1 block w-full rounded-lg border border-brand-green-light px-4 py-3 text-sm text-brand-text-dark focus:border-brand-green focus:outline-none";
