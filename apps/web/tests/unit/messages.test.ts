import { describe, expect, it } from "vitest";

import en from "@/messages/en.json";
import ur from "@/messages/ur.json";
import urLatn from "@/messages/ur-Latn.json";

type Tree = { [key: string]: string | Tree };

/** Every message as a dotted path, e.g. "nav.dashboard". */
function paths(tree: Tree, prefix = ""): string[] {
  return Object.entries(tree).flatMap(([key, value]) =>
    typeof value === "string" ? [prefix + key] : paths(value, `${prefix}${key}.`)
  );
}

/** The {placeholders} a message uses, outside ICU plural/select bodies. */
const placeholders = (text: string) => [...text.matchAll(/\{(\w+)[,}]/g)].map((m) => m[1]).sort();

// The admin portal is English only on purpose.
const translatable = (tree: Tree) => paths(tree).filter((p) => !p.startsWith("admin."));

const lookup = (tree: Tree, path: string) =>
  path.split(".").reduce<string | Tree | undefined>((node, key) => (typeof node === "object" ? node[key] : undefined), tree);

describe.each([
  ["ur", ur],
  ["ur-Latn", urLatn],
])("%s messages", (_name, translated) => {
  it("has every key the English messages have", () => {
    const missing = translatable(en as Tree).filter((p) => lookup(translated as Tree, p) === undefined);
    expect(missing).toEqual([]);
  });

  it("keeps the same {placeholders} as the English text", () => {
    const wrong = translatable(en as Tree).filter((p) => {
      const t = lookup(translated as Tree, p);
      return typeof t === "string" && placeholders(t).join() !== placeholders(lookup(en as Tree, p) as string).join();
    });
    expect(wrong).toEqual([]);
  });
});
