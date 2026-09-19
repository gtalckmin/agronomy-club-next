import type { Metadata } from "next";
import Link from "next/link";

import SignInForm from "@/components/auth/sign-in-form";

export const metadata: Metadata = {
  title: "Sign In | Agronomy Club",
  description: "Access your Agronomy Club member account.",
};

export default function SignInPage() {
  return (
    <section className="mx-auto max-w-3xl px-4 py-12 sm:px-6 lg:px-8">
      <div className="flex flex-col items-center">
        <p className="font-ui text-sm/5 font-semibold uppercase tracking-widest text-brand-green">
          Member access
        </p>
        <h1 className="mt-2 text-3xl/9 font-bold text-brand-text-dark sm:text-4xl/10">
          Welcome Back<span className="text-brand-yellow">.</span>
        </h1>
        <div className="mt-6 w-full max-w-lg rounded-xl bg-white p-6 py-8 shadow-md shadow-brand-shadow sm:px-12 sm:py-8">
          <SignInForm />
          <p className="mt-4 text-center font-ui text-sm font-medium text-brand-text-light">
            Don&apos;t have an account yet?{" "}
            <Link
              href="/sign-up"
              className="font-bold text-brand-green underline hover:text-brand-yellow"
            >
              Create one now
            </Link>
          </p>
        </div>
      </div>
    </section>
  );
}
