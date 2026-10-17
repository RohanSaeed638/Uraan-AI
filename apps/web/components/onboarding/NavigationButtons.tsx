import { ArrowLeft, ArrowRight, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";

interface Props {
  showBack?: boolean;
  loading?: boolean;
  onNext: () => void;
  onBack?: () => void;
  nextLabel?: string;
}

export default function NavigationButtons({
  showBack,
  loading,
  onNext,
  onBack,
  nextLabel = "Continue",
}: Props) {
  return (
    <div className="mt-10 flex justify-between">
      {showBack ? (
        <Button variant="outline" onClick={onBack} className="gap-1.5">
          <ArrowLeft size={15} /> Back
        </Button>
      ) : (
        <div />
      )}

      <Button disabled={loading} onClick={onNext} className="gap-1.5">
        {loading ? (
          <Loader2 size={15} className="animate-spin" />
        ) : (
          <>
            {nextLabel} <ArrowRight size={15} />
          </>
        )}
      </Button>
    </div>
  );
}
