// Soscitea logo — geometry for the cup + steam mark.
// viewBox is 0 0 80 80; all marks share it.

export const LOGO_VIEWBOX = "0 0 80 80";

/** Saucer line beneath the cup */
export const SAUCER = "M23 70 Q40 75 57 70";

/** Cup bowl (open U) */
export const CUP_BODY = "M23 53 C23 66 30 71 40 71 C50 71 57 66 57 53";

/** Handle on the right */
export const HANDLE = "M57 55 C64 54 65 63 57 65";

/** Cup mouth — rendered as an <ellipse> */
export const MOUTH = { cx: 40, cy: 53, rx: 17, ry: 4.6 } as const;

/** Tea surface, just under the rim */
export const TEA = "M27 52.5 Q40 56 53 52.5";

/** Three steam wisps, outer → center. Center rises highest. */
export const STEAM_LEFT = "M36.8 45 C34.2 41.6 33.5 36.9 35.4 32.4";
export const STEAM_CENTER =
  "M40.4 45 C41.9 40.6 38.3 36.8 40.9 32.3 C42.6 28.3 39.1 25.3 41.1 22";
export const STEAM_RIGHT =
  "M43.6 45 C46.3 42 45.1 37.5 46.9 33.8 C48.1 31 46.6 28.5 47.3 26";
