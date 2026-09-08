export function ParallaxCurves() {
  return (
    <svg
      className="pointer-events-none absolute inset-0 h-full w-full opacity-25"
      viewBox="0 0 1600 5200"
      preserveAspectRatio="xMidYMin slice"
      fill="none"
      aria-hidden="true"
    >
      {/* hero */}
      <path
        d="M-100 120 C 250 -80, 350 320, 700 200 C 1000 100, 1050 380, 1400 260"
        stroke="#8a9a5b"
        strokeWidth="2.5"
      />
      <path
        d="M420 -80 C 700 150, 250 500, 550 850 C 800 1080, 1200 900, 1350 650"
        stroke="#8a9a5b"
        strokeWidth="2.5"
      />
      {/* problem / how it works */}
      <path
        d="M-150 1300 C 300 1150, 400 1500, 750 1600 C 1050 1680, 1250 1450, 1700 1500"
        stroke="#8a9a5b"
        strokeWidth="2.5"
      />
      <path
        d="M1700 1900 C 1400 2100, 1550 2350, 1300 2350 C 1100 2350, 1150 2050, 900 1950"
        stroke="#8a9a5b"
        strokeWidth="2.5"
      />
      {/* features / pricing */}
      <path
        d="M-100 2700 C 300 2550, 250 2950, 650 2900 C 950 2860, 1000 3150, 1400 3050"
        stroke="#8a9a5b"
        strokeWidth="2.5"
      />
      <path
        d="M950 3300 C 650 3600, 1450 3750, 1150 4100 C 950 4350, 500 4350, 150 4180"
        stroke="#8a9a5b"
        strokeWidth="2.5"
      />
      {/* faq / footer */}
      <path
        d="M1700 4400 C 1400 4600, 1550 4850, 1300 4850 C 1100 4850, 1150 4550, 900 4450"
        stroke="#8a9a5b"
        strokeWidth="2.5"
      />
      <path
        d="M-150 4900 C 300 4750, 400 5100, 750 5200"
        stroke="#8a9a5b"
        strokeWidth="2.5"
      />
    </svg>
  );
}
