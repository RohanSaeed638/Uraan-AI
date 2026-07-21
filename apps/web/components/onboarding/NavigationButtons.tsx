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

        <Button
          variant="outline"
          onClick={onBack}
        >
          Back
        </Button>

      ) : (

        <div />

      )}

      <Button
        disabled={loading}
        onClick={onNext}
      >
        {nextLabel}
      </Button>

    </div>

  );

}