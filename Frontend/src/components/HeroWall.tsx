/** The hero's fluted-glass wall: the warm light ramp seen through vertical
 * glass reeds. Each reed shows the ramp at its own slight vertical offset, so
 * the bright band bends from panel to panel, and every panel darkens toward
 * its seams with a soft highlight in the middle. On load the wall is flat and
 * the reeds form after the app window has built; then they sway slowly. */

const REEDS = 28; // enough to cover very wide screens; a seam sits on the centre line

// Per-reed offsets (px) for the formed wall and the far end of the sway, a
// fixed irregular pattern so neighbours never move in step.
const OFF = [6, -10, 14, -4, 9, -13, 3, 12, -8, 5, -12, 10, -2, 13, -9, 7, -5, 11, -14, 4, 8, -7, 12, -3, 10, -11, 2, 9];
const OFF2 = [-7, 8, -5, 13, -11, 6, -9, -2, 11, -10, 7, -6, 12, -4, 9, -12, 5, -8, 10, -13, 3, 11, -6, 14, -9, 4, -10, 7];

export default function HeroWall() {
  return (
    <div className="pb-wall pointer-events-none absolute inset-0 overflow-hidden" aria-hidden>
      {Array.from({ length: REEDS }, (_, i) => {
        const k = i - REEDS / 2;
        return (
          <div
            key={i}
            className="pb-reed"
            style={{
              left: `calc(50% + ${k} * var(--pb-reed))`,
              ["--off" as string]: `${OFF[i]}px`,
              ["--off2" as string]: `${OFF2[i]}px`,
              animationDelay: `${0.5 + Math.abs(k) * 0.02}s, ${1.8 + (i % 5) * 0.7}s`,
              animationDuration: `0.9s, ${8 + (i % 4) * 1.5}s`,
            }}
          >
            <span className="pb-reed-glass" style={{ animationDelay: `${0.55 + Math.abs(k) * 0.02}s` }} />
          </div>
        );
      })}
    </div>
  );
}
