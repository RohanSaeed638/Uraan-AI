// "use client";

// interface Props {
//   current: number;
//   total: number;
// }

// export default function StepIndicator({
//   current,
//   total,
// }: Props) {
//   const progress = (current / total) * 100;

//   return (
//     <div className="mb-10">
//       <div className="flex justify-between text-sm mb-2">
//         <span>
//           Step {current} of {total}
//         </span>

//         <span>{Math.round(progress)}%</span>
//       </div>

//       <div className="h-2 rounded-full bg-gray-200 overflow-hidden">
//         <div
//           className="h-full bg-violet-600 transition-all duration-300"
//           style={{
//             width: `${progress}%`,
//           }}
//         />
//       </div>
//     </div>
//   );
// }


interface Props {

  current: number;

  total: number;

}

export default function StepIndicator({

  current,

  total,

}: Props) {

  return (

    <div className="mb-10 flex gap-2">

      {Array.from({

        length: total,

      }).map((_, index) => (

        <div

          key={index}

          className={`h-2 flex-1 rounded-full transition-all

          ${
            index <= current
              ? "bg-purple-600"
              : "bg-gray-200"
          }`}

        />

      ))}

    </div>

  );

}