// "use client";

// import { useForm } from "react-hook-form";

// import {
//     Form,
//     FormControl,
//     FormField,
//     FormItem,
//     FormLabel,
//     FormMessage,
// } from "@/components/ui/form";

// import {
//     Select,
//     SelectContent,
//     SelectItem,
//     SelectTrigger,
//     SelectValue,
// } from "@/components/ui/select";

// import { Textarea } from "@/components/ui/textarea";
// import { Button } from "@/components/ui/button";

// export interface GenerateRoadmapValues {
//     career_stage: string;
//     learning_goal: string;
// }

// interface GenerateRoadmapFormProps {
//     loading?: boolean;
//     onSubmit: (
//         values: GenerateRoadmapValues
//     ) => void;
// }

// export default function GenerateRoadmapForm({
//     loading = false,
//     onSubmit,
// }: GenerateRoadmapFormProps) {

//     const form =
//         useForm<GenerateRoadmapValues>({
//             defaultValues: {
//                 career_stage: "",
//                 learning_goal: "",
//             },
//         });

//     return (
//         <Form {...form}>

//             <form
//                 className="space-y-6"
//                 onSubmit={form.handleSubmit(onSubmit)}
//             >

//                 <FormField
//                     control={form.control}
//                     name="career_stage"
//                     rules={{
//                         required:
//                             "Please select your current stage",
//                     }}
//                     render={({ field }) => (

//                         <FormItem>

//                             <FormLabel>
//                                 Where are you currently?
//                             </FormLabel>

//                             <Select
//                                 value={field.value}
//                                 onValueChange={
//                                     field.onChange
//                                 }
//                             >

//                                 <FormControl>

//                                     <SelectTrigger>

//                                         <SelectValue placeholder="Select your current stage" />

//                                     </SelectTrigger>

//                                 </FormControl>

//                                 <SelectContent>

//                                     <SelectItem value="beginner">
//                                         Beginner
//                                     </SelectItem>

//                                     <SelectItem value="student">
//                                         Student
//                                     </SelectItem>

//                                     <SelectItem value="job_ready">
//                                         Studied but not Job Ready
//                                     </SelectItem>

//                                     <SelectItem value="professional">
//                                         Working Professional
//                                     </SelectItem>

//                                     <SelectItem value="career_switcher">
//                                         Career Switcher
//                                     </SelectItem>

//                                 </SelectContent>

//                             </Select>

//                             <FormMessage />

//                         </FormItem>

//                     )}
//                 />

//                 <FormField
//                     control={form.control}
//                     name="learning_goal"
//                     rules={{
//                         required:
//                             "Tell us your goal",
//                     }}
//                     render={({ field }) => (

//                         <FormItem>

//                             <FormLabel>
//                                 What is your goal?
//                             </FormLabel>

//                             <FormControl>

//                                 <Textarea
//                                     rows={5}
//                                     placeholder="Example: I want to become a Backend Engineer and get my first job in 6 months."
//                                     {...field}
//                                 />

//                             </FormControl>

//                             <FormMessage />

//                         </FormItem>

//                     )}
//                 />

//                 <Button
//                     className="w-full"
//                     disabled={loading}
//                     type="submit"
//                 >
//                     {loading
//                         ? "Generating..."
//                         : "Generate Roadmap"}
//                 </Button>

//             </form>

//         </Form>
//     );
// }

"use client";

import { useForm } from "react-hook-form";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

import {
  CareerStage,
  LearningStyle,
  SkillLevel,
  GenerateRoadmapFormValues,
} from "@/types/roadmap";

interface GenerateRoadmapFormProps {
  loading?: boolean;
  onSubmit: (values: GenerateRoadmapFormValues) => void;
}

export default function GenerateRoadmapForm({
  loading = false,
  onSubmit,
}: GenerateRoadmapFormProps) {
  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<GenerateRoadmapFormValues>({
    defaultValues: {
      career_slug: "",
      career_stage: undefined,
      skill_level: undefined,
      learning_goal: "",
      daily_hours: 2,
      target_duration: 6,
      learning_style: undefined,
    },
  });

  const careerStage = watch("career_stage");
  const skillLevel = watch("skill_level");
  const learningStyle = watch("learning_style");

  return (
    <form
      onSubmit={handleSubmit(onSubmit)}
      className="space-y-6"
    >
      {/* Career */}
      <div className="space-y-2">
        <label
          htmlFor="career_slug"
          className="text-sm font-medium"
        >
          What career do you want to pursue?
        </label>

        <Input
          id="career_slug"
          placeholder="e.g. Backend Engineer"
          {...register("career_slug", {
            required: "Please enter a career.",
          })}
        />

        {errors.career_slug && (
          <p className="text-sm text-destructive">
            {errors.career_slug.message}
          </p>
        )}
      </div>

      {/* Career Stage */}
      <div className="space-y-2">
        <label className="text-sm font-medium">
          Where are you in your career journey?
        </label>

        <Select
          value={careerStage}
          onValueChange={(value) =>
            setValue(
              "career_stage",
              value as CareerStage,
              {
                shouldValidate: true,
              }
            )
          }
        >
          <SelectTrigger>
            <SelectValue placeholder="Select your current stage" />
          </SelectTrigger>

          <SelectContent>
            <SelectItem value={CareerStage.BEGINNER}>
              Starting from scratch
            </SelectItem>

            <SelectItem value={CareerStage.STUDENT}>
              Currently studying
            </SelectItem>

            <SelectItem value={CareerStage.JOB_READY}>
              Studied but not job ready
            </SelectItem>

            <SelectItem value={CareerStage.PROFESSIONAL}>
              Working professional
            </SelectItem>

            <SelectItem value={CareerStage.CAREER_SWITCHER}>
              Switching careers
            </SelectItem>
          </SelectContent>
        </Select>

        {errors.career_stage && (
          <p className="text-sm text-destructive">
            Please select your current stage.
          </p>
        )}
      </div>

      {/* Skill Level */}
      <div className="space-y-2">
        <label className="text-sm font-medium">
          What is your current skill level?
        </label>

        <Select
          value={skillLevel}
          onValueChange={(value) =>
            setValue(
              "skill_level",
              value as SkillLevel,
              {
                shouldValidate: true,
              }
            )
          }
        >
          <SelectTrigger>
            <SelectValue placeholder="Select your skill level" />
          </SelectTrigger>

          <SelectContent>
            <SelectItem value={SkillLevel.BEGINNER}>
              Beginner
            </SelectItem>

            <SelectItem value={SkillLevel.INTERMEDIATE}>
              Intermediate
            </SelectItem>

            <SelectItem value={SkillLevel.ADVANCED}>
              Advanced
            </SelectItem>
          </SelectContent>
        </Select>

        {errors.skill_level && (
          <p className="text-sm text-destructive">
            Please select your skill level.
          </p>
        )}
      </div>

      {/* Learning Goal */}
      <div className="space-y-2">
        <label
          htmlFor="learning_goal"
          className="text-sm font-medium"
        >
          What do you want to achieve?
        </label>

        <Textarea
          id="learning_goal"
          rows={5}
          placeholder="Example: I want to become a backend engineer and get my first job within 6 months."
          {...register("learning_goal", {
            required: "Please describe your goal.",
            minLength: {
              value: 10,
              message:
                "Please provide a little more detail about your goal.",
            },
          })}
        />

        {errors.learning_goal && (
          <p className="text-sm text-destructive">
            {errors.learning_goal.message}
          </p>
        )}
      </div>

      {/* Daily Hours */}
      <div className="space-y-2">
        <label
          htmlFor="daily_hours"
          className="text-sm font-medium"
        >
          How many hours can you study each day?
        </label>

        <Input
          id="daily_hours"
          type="number"
          min={1}
          max={12}
          {...register("daily_hours", {
            required: "Please enter your available hours.",
            valueAsNumber: true,
            min: {
              value: 1,
              message: "Minimum is 1 hour.",
            },
            max: {
              value: 12,
              message: "Maximum is 12 hours.",
            },
          })}
        />

        {errors.daily_hours && (
          <p className="text-sm text-destructive">
            {errors.daily_hours.message}
          </p>
        )}
      </div>

      {/* Target Duration */}
      <div className="space-y-2">
        <label
          htmlFor="target_duration"
          className="text-sm font-medium"
        >
          How many months do you want to work toward this?
        </label>

        <Input
          id="target_duration"
          type="number"
          min={1}
          max={36}
          {...register("target_duration", {
            required: "Please enter your target duration.",
            valueAsNumber: true,
            min: {
              value: 1,
              message: "Minimum is 1 month.",
            },
            max: {
              value: 36,
              message: "Maximum is 36 months.",
            },
          })}
        />

        {errors.target_duration && (
          <p className="text-sm text-destructive">
            {errors.target_duration.message}
          </p>
        )}
      </div>

      {/* Learning Style */}
      <div className="space-y-2">
        <label className="text-sm font-medium">
          How do you prefer to learn?
        </label>

        <Select
          value={learningStyle}
          onValueChange={(value) =>
            setValue(
              "learning_style",
              value as LearningStyle,
              {
                shouldValidate: true,
              }
            )
          }
        >
          <SelectTrigger>
            <SelectValue placeholder="Select your learning style" />
          </SelectTrigger>

          <SelectContent>
            <SelectItem value={LearningStyle.VIDEO}>
              Video-based
            </SelectItem>
            <SelectItem value={LearningStyle.READING}>
              Reading-based
            </SelectItem>
            <SelectItem value={LearningStyle.PROJECT}>
              Project-based
            </SelectItem>

            <SelectItem value={LearningStyle.MIXED}>
              Mix of theory and practice
            </SelectItem>
          </SelectContent>
        </Select>

        {errors.learning_style && (
          <p className="text-sm text-destructive">
            Please select your learning style.
          </p>
        )}
      </div>

      {/* Submit */}
      <Button
        type="submit"
        className="w-full"
        disabled={loading}
      >
        {loading
          ? "Generating roadmap..."
          : "Generate Roadmap"}
      </Button>
    </form>
  );
}