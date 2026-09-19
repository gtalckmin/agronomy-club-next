import { ArrowUpRight, BookOpen, CalendarDays, Users } from "lucide-react";
import Image from "next/image";
import Link from "next/link";

import { Button } from "@/components/ui/button";

const pathways = [
  {
    icon: BookOpen,
    title: "Learn together",
    text: "Practical resources and shared knowledge for every growing season.",
  },
  {
    icon: CalendarDays,
    title: "Show up",
    text: "Field days, conversations, and events that connect people to place.",
  },
  {
    icon: Users,
    title: "Grow a network",
    text: "A welcoming community for students, alumni, and industry.",
  },
];

export default function Home() {
  return (
    <main className="overflow-hidden bg-brand-surface">
      <section className="relative isolate border-b border-brand-green/15 px-6 py-16 sm:px-12 lg:min-h-[calc(100vh-4rem)] lg:px-16 lg:py-24">
        <div className="absolute inset-y-0 right-0 -z-10 hidden w-[52%] bg-brand-green-dark lg:block" />
        <div className="absolute right-[18%] top-0 -z-10 hidden h-32 w-32 rounded-b-full bg-brand-yellow lg:block" />
        <div className="mx-auto grid max-w-7xl items-center gap-12 lg:grid-cols-[1.05fr_.95fr] lg:gap-20">
          <div className="max-w-2xl">
            <p className="font-plex-mono text-xs font-bold uppercase tracking-[.22em] text-brand-green">
              Agriculture for a changing world
            </p>
            <h1 className="mt-7 font-serif text-5xl font-bold leading-[.98] tracking-tight text-brand-green-dark sm:text-7xl xl:text-8xl">
              Rooted in knowledge.
              <br />
              <span className="text-brand-yellow">Growing</span> together.
            </h1>
            <p className="mt-8 max-w-xl text-lg leading-8 text-brand-brown sm:text-xl">
              Agronomy Club brings together the people shaping resilient food
              systems, from first-year students to experienced practitioners.
            </p>
            <div className="mt-10 flex flex-wrap gap-4">
              <Button
                asChild
                className="h-12 rounded-full bg-brand-green px-7 text-base hover:bg-brand-green-dark"
              >
                <Link href="/sign-up">
                  Become a member <ArrowUpRight className="size-4" />
                </Link>
              </Button>
              <Button
                asChild
                variant="outline"
                className="h-12 rounded-full border-2 border-brand-green bg-transparent px-7 text-base text-brand-green hover:bg-brand-green/10"
              >
                <Link href="/events">Find an event</Link>
              </Button>
            </div>
          </div>
          <div className="relative mx-auto w-full max-w-md lg:max-w-none">
            <div className="relative aspect-[4/5] overflow-hidden rounded-[2rem] border-8 border-brand-surface shadow-2xl shadow-black/20">
              <Image
                src="/PlantPhotoAgronomy.jpeg"
                alt="A thriving crop in an Agronomy Club field"
                fill
                priority
                sizes="(max-width: 1024px) 90vw, 42vw"
                className="object-cover"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-brand-green-dark/65 via-transparent to-transparent" />
              <p className="absolute bottom-7 left-7 max-w-[14rem] font-serif text-3xl leading-tight text-white">
                Start close to the soil.
              </p>
            </div>
            <div className="absolute -bottom-6 -left-5 rounded-2xl bg-brand-yellow px-6 py-5 text-brand-brown shadow-xl">
              <p className="font-plex-mono text-xs font-bold uppercase tracking-wider">
                Open to everyone
              </p>
              <p className="mt-1 text-sm font-semibold">Learn. Share. Grow.</p>
            </div>
          </div>
        </div>
      </section>
      <section className="mx-auto max-w-7xl px-6 py-20 sm:px-12 lg:px-16">
        <div className="grid gap-10 lg:grid-cols-[.8fr_1.2fr]">
          <div>
            <p className="font-plex-mono text-xs font-bold uppercase tracking-[.2em] text-brand-green">
              Find your place
            </p>
            <h2 className="mt-5 font-serif text-4xl leading-tight text-brand-green-dark sm:text-5xl">
              The club for curious growers.
            </h2>
          </div>
          <div className="grid gap-px overflow-hidden rounded-3xl border border-brand-green/20 bg-brand-green/20 sm:grid-cols-3">
            {pathways.map(({ icon: Icon, title, text }) => (
              <article key={title} className="bg-brand-surface p-7">
                <Icon className="size-6 text-brand-yellow" />
                <h3 className="mt-12 text-xl font-bold text-brand-green-dark">
                  {title}
                </h3>
                <p className="mt-3 text-sm leading-6 text-brand-brown">
                  {text}
                </p>
              </article>
            ))}
          </div>
        </div>
      </section>
    </main>
  );
}
