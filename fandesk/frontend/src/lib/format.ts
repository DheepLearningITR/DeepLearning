export const fmtTokens = (n: number) => n.toLocaleString("en-US");

export const fmtCost = (usd: number, digits = 4) => usd.toFixed(digits);

export const fmtSeconds = (ms: number) => (ms / 1000).toFixed(1);

export const fmtTime = (iso: string) =>
  new Date(iso).toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" });
