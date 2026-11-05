"use client";

import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { Zap } from "lucide-react";
import { useEffect, useState } from "react";

const EVENT = "uraan:xp";
const SHOW_MS = 1700;

/** XP earned for finishing a lesson and a task; the same numbers the server awards. */
export const XP_LESSON = 10;
export const XP_TASK = 25;

/** Shows a short "+10 XP" chip. Call it right after the server accepted the completion. */
export function fireXp(amount: number) {
  if (typeof window === "undefined") return;

  window.dispatchEvent(new CustomEvent<number>(EVENT, { detail: amount }));
}

/** Mount once in the app layout. The chip rises and fades; with reduced motion it just appears and goes. */
export default function XpBurst() {
  const reduced = useReducedMotion();
  const [chips, setChips] = useState<{ id: number; amount: number }[]>([]);

  useEffect(() => {
    let counter = 0;

    function show(event: Event) {
      const amount = (event as CustomEvent<number>).detail;
      const id = ++counter;

      setChips((current) => [...current, { id, amount }]);
      setTimeout(() => setChips((current) => current.filter((chip) => chip.id !== id)), SHOW_MS);
    }

    window.addEventListener(EVENT, show);

    return () => window.removeEventListener(EVENT, show);
  }, []);

  return (
    <div
      role="status"
      aria-live="polite"
      className="pointer-events-none fixed inset-x-0 bottom-24 z-50 flex flex-col items-center gap-2 lg:bottom-10"
    >
      <AnimatePresence>
        {chips.map((chip) => (
          <motion.div
            key={chip.id}
            initial={reduced ? { opacity: 0 } : { opacity: 0, y: 18, scale: 0.85 }}
            animate={reduced ? { opacity: 1 } : { opacity: 1, y: -14, scale: 1 }}
            exit={reduced ? { opacity: 0 } : { opacity: 0, y: -52, scale: 0.95 }}
            transition={{ duration: reduced ? 0.1 : 0.45, ease: "easeOut" }}
            className="flex items-center gap-2 rounded-full bg-gradient-to-r from-violet-600 to-indigo-600 px-5 py-2.5 text-sm font-semibold text-white shadow-xl shadow-violet-600/35"
          >
            <Zap size={15} className="text-amber-300" aria-hidden />
            <span className="num">+{chip.amount} XP</span>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}
