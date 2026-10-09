/** Keyframes shared by the website-translator demos. Rendered once per page. */
export default function DemoKeyframes() {
  return (
    <style>{`
@keyframes wsd-blink { 0%, 49% { opacity: 1 } 50%, 100% { opacity: 0 } }
@keyframes wsd-fade-in { from { opacity: 0; transform: translateY(6px) } to { opacity: 1; transform: none } }
@keyframes wsd-pulse-kf { 0%, 100% { box-shadow: 0 0 0 0 rgba(255,255,255,0.18) } 50% { box-shadow: 0 0 0 5px rgba(255,255,255,0) } }
.wsd-caret { animation: wsd-blink 1s steps(1) infinite; }
.wsd-fade { animation: wsd-fade-in 420ms cubic-bezier(.2,.7,.2,1) both; }
.wsd-pulse { animation: wsd-pulse-kf 1.2s ease-in-out infinite; }
[data-wsd-paused] .wsd-caret, [data-wsd-paused] .wsd-pulse { animation-play-state: paused; }
@media (prefers-reduced-motion: reduce) {
  .wsd-caret, .wsd-fade, .wsd-pulse { animation: none; }
}
`}</style>
  );
}
