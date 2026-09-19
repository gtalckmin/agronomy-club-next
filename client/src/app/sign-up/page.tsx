import type { Metadata } from "next";
import Link from "next/link";

import SignUpForm from "@/components/auth/sign-up-form";

export const metadata: Metadata = {
  title: "Sign Up | Agronomy Club",
  description: "Create an Agronomy Club member account.",
};

export default function SignUpPage() {
  return (
    <section className="mx-auto max-w-5xl px-4 py-12 sm:px-6 lg:px-8">
      <div className="flex flex-col items-center">
        <p className="font-ui text-sm/5 font-semibold uppercase tracking-widest text-brand-green">
          Join the club
        </p>
        <h1 className="mt-2 text-center text-2xl/7 font-bold text-brand-text-dark sm:text-3xl/9">
          Create your Agronomy Club account
          <span className="text-brand-yellow">.</span>
        </h1>
        <div className="mt-6 w-full max-w-4xl rounded-xl bg-white px-6 py-8 shadow-md shadow-brand-shadow sm:px-12">
          <SignUpForm />
          <p className="mt-4 text-center font-ui text-sm font-medium text-brand-text-light">
            Already part of the community?{" "}
            <Link
              href="/sign-in"
              className="font-ui font-bold text-brand-green underline hover:text-brand-yellow"
            >
              Sign in here
            </Link>
          </p>
        </div>
      </div>
    </section>
  );
}
