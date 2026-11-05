import { ImageResponse } from "next/og";

// The picture shown when a link to the site is shared (WhatsApp, LinkedIn, X, ...).
export const alt = "Uraan AI: your AI-powered career growth partner";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function OpenGraphImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          padding: 72,
          color: "white",
          background: "linear-gradient(135deg, #0b0a1a 0%, #2e1065 55%, #7c3aed 100%)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", fontSize: 44, fontWeight: 700 }}>
          <span>Uraan</span>
          <span style={{ color: "#f5a83c", marginLeft: 12 }}>AI</span>
        </div>

        <div style={{ display: "flex", flexDirection: "column" }}>
          <div style={{ fontSize: 76, fontWeight: 800, lineHeight: 1.1, maxWidth: 900 }}>
            Your AI-powered career growth partner
          </div>
          <div style={{ fontSize: 34, marginTop: 28, color: "#ddd6fe" }}>
            Personalised roadmaps. Practical lessons. An AI mentor. Free during beta.
          </div>
        </div>
      </div>
    ),
    size
  );
}
