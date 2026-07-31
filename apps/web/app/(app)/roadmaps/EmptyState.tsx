import { Button } from "@/components/ui/button";

export default function EmptyState() {
  return (
    <div className="rounded-xl border p-12 text-center">

      <h2 className="text-2xl font-bold">
        No Roadmaps Yet
      </h2>

      <p className="mt-3 text-muted-foreground">
        Generate your first AI career roadmap.
      </p>

      <Button className="mt-8">
        Generate Roadmap
      </Button>

    </div>
  );
}