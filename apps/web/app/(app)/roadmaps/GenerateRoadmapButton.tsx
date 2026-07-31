"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { Loader2, Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";
import { api } from "@/lib/api/client";

export default function GenerateRoadmapButton() {
  const router = useRouter();

  const [loading, setLoading] =
    useState(false);

  async function generateRoadmap() {
    try {
      setLoading(true);

      const response =
        await api.post("/roadmaps/generate");

      router.push(
        `/roadmaps/${response.data.id}`
      );

      router.refresh();
    } finally {
      setLoading(false);
    }
  }

  return (
    <Button
      onClick={generateRoadmap}
      disabled={loading}
    >
      {loading ? (
        <>
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          Generating...
        </>
      ) : (
        <>
          <Sparkles className="mr-2 h-4 w-4" />
          Generate Roadmap
        </>
      )}
    </Button>
  );
}