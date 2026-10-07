import type { NodeState } from "../lib/derive";

/** Indicator lamp: a flat painted disc. Always paired with a status word, never colour alone. */
export function Lamp({ state }: { state: NodeState }) {
  const lit = state === "live" || state === "done";
  return (
    <span
      aria-hidden
      className={`block size-5 rounded-full border-2 ${
        lit ? "lamp-on border-lamp-deep bg-lamp" : "border-board-deep bg-lamp-off"
      }`}
    />
  );
}
