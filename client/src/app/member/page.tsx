import type { Metadata } from "next";

import MemberProfile from "@/components/auth/member-profile";

export const metadata: Metadata = {
  title: "My Membership | Agronomy Club",
  description: "View and complete your Agronomy Club member profile.",
};

export default function MemberPage() {
  return (
    <section className="mx-auto max-w-3xl px-4 py-12 sm:px-6 lg:px-8">
      <MemberProfile />
    </section>
  );
}
