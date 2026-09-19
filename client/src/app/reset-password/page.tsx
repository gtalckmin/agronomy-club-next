import type { Metadata } from "next";

import ResetPasswordForm from "@/components/auth/reset-password-form";

export const metadata: Metadata = {
  title: "Reset Password | Agronomy Club",
  description: "Reset your Agronomy Club account password.",
};

export default function ResetPasswordPage() {
  return (
    <section className="mx-auto max-w-xl px-4 py-12 sm:px-6 lg:px-8">
      <div className="rounded-xl bg-white p-7 shadow-md shadow-brand-shadow">
        <p className="text-sm font-semibold uppercase tracking-widest text-brand-green">
          Member access
        </p>
        <h1 className="mt-2 text-3xl font-bold text-brand-text-dark">
          Reset your password.
        </h1>
        <p className="mt-3 text-brand-text-light">
          Enter your email and we&apos;ll send password-reset instructions.
        </p>
        <div className="mt-7">
          <ResetPasswordForm />
        </div>
      </div>
    </section>
  );
}
