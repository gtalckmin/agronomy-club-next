"use client";

import axios from "axios";
import {
  onAuthStateChanged,
  signOut,
  type User as FirebaseUser,
} from "firebase/auth";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { getFirebaseAuth } from "@/lib/firebase";
import {
  createMemberProfile,
  getMemberProfile,
  type MemberProfile,
  type MemberProfileInput,
} from "@/lib/member-profile";

type ViewState = "error" | "loading" | "missing" | "ready";
const years = Array.from({ length: 20 }, (_, index) => 2020 + index);

export default function MemberProfile() {
  const router = useRouter();
  const [state, setState] = useState<ViewState>("loading");
  const [profile, setProfile] = useState<MemberProfile | null>(null);
  const [user, setUser] = useState<FirebaseUser | null>(null);
  const [message, setMessage] = useState("");

  useEffect(() => {
    let active = true;
    const load = async (currentUser: FirebaseUser | null) => {
      if (!currentUser) {
        router.replace("/sign-in");
        return;
      }
      if (!currentUser.emailVerified) {
        await signOut(getFirebaseAuth());
        router.replace("/sign-in");
        return;
      }
      setUser(currentUser);
      try {
        const member = await getMemberProfile(await currentUser.getIdToken());
        if (active) {
          setProfile(member);
          setState("ready");
        }
      } catch (error) {
        if (!active) return;
        if (axios.isAxiosError(error) && error.response?.status === 404) {
          setState("missing");
          return;
        }
        setMessage(
          "We could not load your member profile. Please try again shortly.",
        );
        setState("error");
      }
    };
    const unsubscribe = onAuthStateChanged(getFirebaseAuth(), load);
    return () => {
      active = false;
      unsubscribe();
    };
  }, [router]);

  if (state === "loading")
    return (
      <p className="text-center text-brand-text-light">
        Loading your member profile...
      </p>
    );
  if (state === "error")
    return <p className="text-center text-red-700">{message}</p>;
  if (state === "missing" && user)
    return (
      <ProfileCompletion
        user={user}
        onComplete={(member) => {
          setProfile(member);
          setState("ready");
        }}
      />
    );
  if (!profile) return null;

  return (
    <div className="rounded-xl bg-white p-7 shadow-md shadow-brand-shadow">
      <p className="text-sm font-semibold uppercase tracking-widest text-brand-green">
        Member profile
      </p>
      <h1 className="mt-2 text-3xl font-bold text-brand-text-dark">
        {profile.full_name}
      </h1>
      <dl className="mt-6 grid gap-5 text-brand-text-light sm:grid-cols-2">
        <Detail label="Email" value={profile.email} />
        <Detail label="Graduation year" value={String(profile.grad_yr)} />
        <Detail label="Discipline" value={profile.discipline} />
        <Detail label="Membership" value={profile.global_role} />
      </dl>
      <Button
        type="button"
        onClick={async () => {
          await signOut(getFirebaseAuth());
          router.replace("/");
        }}
        className="mt-8 bg-brand-green text-brand-surface hover:bg-brand-yellow hover:text-brand-brown"
      >
        Sign out
      </Button>
    </div>
  );
}

function ProfileCompletion({
  user,
  onComplete,
}: {
  user: FirebaseUser;
  onComplete: (profile: MemberProfile) => void;
}) {
  const [values, setValues] = useState<MemberProfileInput>({
    fullName: "",
    graduationYear: "",
    discipline: "",
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [message, setMessage] = useState("");
  const update = (name: keyof MemberProfileInput, value: string) =>
    setValues((current) => ({ ...current, [name]: value }));
  const submit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (
      !values.fullName.trim() ||
      !values.graduationYear ||
      !values.discipline.trim()
    ) {
      setMessage("Complete each member profile field.");
      return;
    }
    setIsSubmitting(true);
    setMessage("");
    try {
      onComplete(await createMemberProfile(await user.getIdToken(), values));
    } catch {
      setMessage(
        "We could not save your member profile. Please try again shortly.",
      );
    } finally {
      setIsSubmitting(false);
    }
  };
  return (
    <div className="rounded-xl bg-white p-7 shadow-md shadow-brand-shadow">
      <p className="text-sm font-semibold uppercase tracking-widest text-brand-green">
        One last step
      </p>
      <h1 className="mt-2 text-3xl font-bold text-brand-text-dark">
        Complete your member profile.
      </h1>
      <p className="mt-3 text-brand-text-light">Signed in as {user.email}</p>
      <form onSubmit={submit} className="mt-7 grid gap-5 sm:grid-cols-2">
        <ProfileField
          label="Full Name"
          value={values.fullName}
          onChange={(value) => update("fullName", value)}
        />
        <div>
          <label
            htmlFor="year"
            className="block font-medium text-brand-text-dark"
          >
            Graduation Year
          </label>
          <select
            id="year"
            value={values.graduationYear}
            onChange={(event) => update("graduationYear", event.target.value)}
            className="mt-1 block w-full rounded-lg border border-brand-green-light bg-white px-4 py-3 text-sm text-brand-text-dark"
          >
            <option value="">Year</option>
            {years.map((year) => (
              <option key={year} value={year}>
                {year}
              </option>
            ))}
          </select>
        </div>
        <ProfileField
          label="Discipline"
          value={values.discipline}
          onChange={(value) => update("discipline", value)}
        />
        <Button
          type="submit"
          disabled={isSubmitting}
          className="self-end bg-brand-green text-brand-surface hover:bg-brand-yellow hover:text-brand-brown disabled:opacity-60"
        >
          {isSubmitting ? "Saving profile..." : "Save profile"}
        </Button>
      </form>
      {message ? <p className="mt-4 text-sm text-red-700">{message}</p> : null}
    </div>
  );
}

function ProfileField({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
}) {
  const id = label.toLowerCase().replace(" ", "-");
  return (
    <div>
      <label htmlFor={id} className="block font-medium text-brand-text-dark">
        {label}
      </label>
      <input
        id={id}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="mt-1 block w-full rounded-lg border border-brand-green-light px-4 py-3 text-sm text-brand-text-dark"
      />
    </div>
  );
}

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-sm font-semibold uppercase tracking-wide text-brand-green">
        {label}
      </dt>
      <dd className="mt-1 capitalize">{value}</dd>
    </div>
  );
}
