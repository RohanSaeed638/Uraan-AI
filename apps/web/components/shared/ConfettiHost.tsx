"use client";

import { useEffect, useRef } from "react";

const EVENT = "uraan:confetti";
const COLORS = ["#7C3AED", "#F59E0B", "#10B981", "#3B82F6", "#EC4899", "#F97316"];
const DURATION_MS = 2400;
const PIECES = 110;

/** Fires a short burst of confetti. Does nothing for people who asked their
 * system for less motion. */
export function fireConfetti() {
  if (typeof window === "undefined") return;
  if (window.matchMedia?.("(prefers-reduced-motion: reduce)").matches) return;

  window.dispatchEvent(new Event(EVENT));
}

interface Piece {
  x: number;
  y: number;
  vx: number;
  vy: number;
  size: number;
  spin: number;
  angle: number;
  color: string;
}

/** Mount once in the app layout. Draws on a canvas that ignores clicks, only
 * while a burst is running. */
export default function ConfettiHost() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const frame = useRef<number | null>(null);

  useEffect(() => {
    function burst() {
      const canvas = canvasRef.current;
      const ctx = canvas?.getContext("2d");

      if (!canvas || !ctx) return;

      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;

      const pieces: Piece[] = Array.from({ length: PIECES }, () => ({
        x: canvas.width / 2 + (Math.random() - 0.5) * 120,
        y: canvas.height * 0.35,
        vx: (Math.random() - 0.5) * 14,
        vy: -Math.random() * 12 - 4,
        size: 6 + Math.random() * 6,
        spin: (Math.random() - 0.5) * 0.4,
        angle: Math.random() * Math.PI,
        color: COLORS[Math.floor(Math.random() * COLORS.length)],
      }));

      const started = performance.now();

      if (frame.current) cancelAnimationFrame(frame.current);

      function step(now: number) {
        const elapsed = now - started;

        ctx!.clearRect(0, 0, canvas!.width, canvas!.height);

        if (elapsed > DURATION_MS) {
          frame.current = null;
          return;
        }

        const fade = Math.min(1, (DURATION_MS - elapsed) / 600);

        for (const p of pieces) {
          p.vy += 0.35;
          p.vx *= 0.99;
          p.x += p.vx;
          p.y += p.vy;
          p.angle += p.spin;

          ctx!.save();
          ctx!.globalAlpha = fade;
          ctx!.translate(p.x, p.y);
          ctx!.rotate(p.angle);
          ctx!.fillStyle = p.color;
          ctx!.fillRect(-p.size / 2, -p.size / 4, p.size, p.size / 2);
          ctx!.restore();
        }

        frame.current = requestAnimationFrame(step);
      }

      frame.current = requestAnimationFrame(step);
    }

    window.addEventListener(EVENT, burst);

    return () => {
      window.removeEventListener(EVENT, burst);
      if (frame.current) cancelAnimationFrame(frame.current);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      aria-hidden
      className="pointer-events-none fixed inset-0 z-[100] size-full"
    />
  );
}
