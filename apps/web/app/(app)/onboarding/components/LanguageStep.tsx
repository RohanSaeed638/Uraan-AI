// "use client";

// import { useOnboardingStore } from "@/store/onboarding";

// export default function LanguageStep() {
//   const { language, update } = useOnboardingStore();

//   const options = [
//     { value: "en", label: "English" },
//     { value: "ur", label: "اردو" },
//   ];

//   return (
//     <div className="space-y-4">
//       <h2 className="text-2xl font-bold">
//         Choose Your Language
//       </h2>

//       <div className="grid gap-4">
//         {options.map((option) => (
//           <button
//             key={option.value}
//             type="button"
//             onClick={() =>
//               update({
//                 language: option.value,
//               })
//             }
//             className={`rounded-lg border p-4 text-left transition ${
//               language === option.value
//                 ? "border-violet-600 bg-violet-50"
//                 : "border-gray-200"
//             }`}
//           >
//             {option.label}
//           </button>
//         ))}
//       </div>
//     </div>
//   );
// }

"use client";

import { LANGUAGES } from "../constants";

import OptionCard from "@/components/onboarding/OptionCard";
import NavigationButtons from "@/components/onboarding/NavigationButtons";
import OnboardingCard from "@/components/onboarding/OnboardingCard";

import { StepProps } from "../types";

export default function LanguageStep({
  data,
  updateData,
  next,
  previous,
}: StepProps) {
  return (
    <OnboardingCard
      title="Choose Language"
      subtitle="You can change it later."
    >
      <div className="grid gap-4">

        {LANGUAGES.map((lang) => (
          <OptionCard
            key={lang.value}
            title={lang.label}
            selected={
              data.language === lang.value
            }
            onClick={() =>
              updateData({
                language: lang.value,
              })
            }
          />
        ))}

      </div>

      <NavigationButtons
        showBack
        onBack={previous}
        onNext={next}
      />
    </OnboardingCard>
  );
}