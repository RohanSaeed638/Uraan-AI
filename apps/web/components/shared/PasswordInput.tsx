// "use client";

// import { Eye, EyeOff } from "lucide-react";
// import { useState } from "react";

// import { Input } from "@/components/ui/input";

// export default function PasswordInput(
//   props: React.ComponentProps<typeof Input>
// ) {
//   const [show, setShow] = useState(false);

//   return (
//     <div className="relative">
//       <Input
//         {...props}
//         type={show ? "text" : "password"}
//       />

//       <button
//         type="button"
//         onClick={() => setShow(!show)}
//         className="absolute right-3 top-3"
//       >
//         {show ? <EyeOff size={18} /> : <Eye size={18} />}
//       </button>
//     </div>
//   );
// }


"use client";

import * as React from "react";
import { Eye, EyeOff } from "lucide-react";

import { Input } from "@/components/ui/input";

const PasswordInput = React.forwardRef<
  HTMLInputElement,
  React.ComponentProps<typeof Input>
>((props, ref) => {
  const [show, setShow] = React.useState(false);

  return (
    <div className="relative">
      <Input
        ref={ref}
        {...props}
        type={show ? "text" : "password"}
      />

      <button
        type="button"
        onClick={() => setShow(!show)}
        className="absolute right-3 top-1/2 -translate-y-1/2"
      >
        {show ? (
          <EyeOff className="h-4 w-4" size={18}/>
        ) : (
          <Eye className="h-4 w-4" size={18}/>
        )}
      </button>
    </div>
  );
});

PasswordInput.displayName = "PasswordInput";

export default PasswordInput;