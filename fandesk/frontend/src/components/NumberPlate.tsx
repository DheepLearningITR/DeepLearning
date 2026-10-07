interface Props {
  value: string | null;
  /** Number of slots on the plate; the value is right-aligned like a scoreboard. */
  slots: number;
  label: string;
  /** md plates live on the route board and shrink when the board is narrow. */
  size?: "md" | "lg";
  className?: string;
}

const CELL = {
  md: "h-8 w-[0.9rem] text-[1rem] @[45rem]:h-9 @[45rem]:w-[1.2rem] @[45rem]:text-[1.2rem]",
  lg: "h-11 w-[1.65rem] text-[1.6rem]",
};

/**
 * A row of enamel number plates. Each character is keyed by its slot and
 * value, so only the characters that change remount and drop in: the board
 * updates cell by cell instead of redrawing.
 */
export function NumberPlate({ value, slots, label, size = "md", className = "" }: Props) {
  const chars = (value ?? "").slice(-slots).padStart(slots, " ").split("");

  return (
    <span className={`inline-flex gap-[3px] ${className}`} role="img" aria-label={`${label}: ${value ?? "blank"}`}>
      {chars.map((c, i) => (
        <span
          key={i}
          aria-hidden
          className={`${CELL[size]} grid place-items-center overflow-hidden font-board font-semibold tabular-nums leading-none ${
            c === " " ? "bg-board-deep" : "bg-plate text-plate-ink shadow-[0_1px_2px_rgb(0_0_0/0.35)]"
          }`}
        >
          {c !== " " && (
            <span key={`${i}-${c}`} className="plate-cell-new">
              {c}
            </span>
          )}
        </span>
      ))}
    </span>
  );
}
