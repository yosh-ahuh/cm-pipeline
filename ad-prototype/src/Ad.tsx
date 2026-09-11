import React from 'react';
import {
  AbsoluteFill,
  Easing,
  Sequence,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

const FONT =
  '"Hiragino Sans", "Hiragino Kaku Gothic ProN", "Noto Sans JP", sans-serif';
const BG = '#0B0D14';
const TEXT = '#F5F7FA';
const SUB = '#8B93A7';
const ACCENT1 = '#6366F1';
const ACCENT2 = '#A855F7';
const GREEN = '#34D399';
const CARD_BG = '#131827';
const CARD_BORDER = '1px solid rgba(255,255,255,0.09)';

const gradientText: React.CSSProperties = {
  background: `linear-gradient(92deg, ${ACCENT1}, ${ACCENT2})`,
  WebkitBackgroundClip: 'text',
  backgroundClip: 'text',
  WebkitTextFillColor: 'transparent',
};

// ---------------------------------------------------------------- backdrop

const Backdrop: React.FC<{strength?: number}> = ({strength = 1}) => {
  const frame = useCurrentFrame();
  const y = Math.sin(frame / 70) * 50;
  return (
    <AbsoluteFill style={{background: BG}}>
      <div
        style={{
          position: 'absolute',
          width: 950,
          height: 950,
          borderRadius: '50%',
          filter: 'blur(180px)',
          opacity: 0.22 * strength,
          background: ACCENT1,
          top: -260 + y,
          left: -340,
        }}
      />
      <div
        style={{
          position: 'absolute',
          width: 950,
          height: 950,
          borderRadius: '50%',
          filter: 'blur(180px)',
          opacity: 0.18 * strength,
          background: ACCENT2,
          bottom: -300 - y,
          right: -340,
        }}
      />
    </AbsoluteFill>
  );
};

const useFadeOut = (start: number, end: number) => {
  const frame = useCurrentFrame();
  return interpolate(frame, [start, end], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
};

// ---------------------------------------------------------------- scene 1: hook

const Hook: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  const s1 = spring({frame, fps, config: {damping: 200}});
  const s2 = spring({
    frame: frame - 10,
    fps,
    config: {damping: 13, mass: 0.7, stiffness: 130},
  });
  const out = useFadeOut(65, 75);

  return (
    <AbsoluteFill
      style={{
        justifyContent: 'center',
        alignItems: 'center',
        opacity: out,
        padding: 80,
      }}
    >
      <div
        style={{
          opacity: s1,
          transform: `translateY(${(1 - s1) * 40}px)`,
          color: TEXT,
          fontSize: 58,
          fontWeight: 600,
          letterSpacing: '0.04em',
        }}
      >
        毎週のレポート作成に
      </div>
      <div
        style={{
          marginTop: 36,
          opacity: Math.min(1, s2),
          transform: `scale(${0.7 + s2 * 0.3})`,
          fontWeight: 800,
          color: TEXT,
          letterSpacing: '0.02em',
          textAlign: 'center',
          lineHeight: 1.2,
        }}
      >
        <div style={{fontSize: 140}}>
          <span style={gradientText}>5時間</span>、
        </div>
        <div style={{fontSize: 100, marginTop: 10}}>溶けてない?</div>
      </div>
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------- scene 2: problem

const TASKS = ['データ集め', 'コピペ作業', 'グラフづくり'];

const Problem: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const out = useFadeOut(85, 95);

  const punch = spring({
    frame: frame - 52,
    fps,
    config: {damping: 12, mass: 0.7, stiffness: 150},
  });
  const dim = interpolate(frame, [52, 62], [1, 0.35], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill
      style={{
        justifyContent: 'center',
        alignItems: 'center',
        opacity: out,
        padding: 80,
      }}
    >
      <div style={{display: 'flex', flexDirection: 'column', gap: 34, opacity: dim}}>
        {TASKS.map((t, i) => {
          const s = spring({
            frame: frame - i * 7,
            fps,
            config: {damping: 15, mass: 0.6, stiffness: 140},
          });
          const strike = interpolate(frame, [34 + i * 5, 44 + i * 5], [0, 1], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
            easing: Easing.out(Easing.cubic),
          });
          return (
            <div
              key={t}
              style={{
                position: 'relative',
                opacity: Math.min(1, s),
                transform: `translateY(${(1 - s) * 60}px)`,
                background: CARD_BG,
                border: CARD_BORDER,
                borderRadius: 26,
                padding: '30px 60px',
                fontSize: 54,
                fontWeight: 600,
                color: TEXT,
                letterSpacing: '0.05em',
                textAlign: 'center',
              }}
            >
              {t}
              <div
                style={{
                  position: 'absolute',
                  left: 40,
                  right: 40,
                  top: '50%',
                  height: 7,
                  borderRadius: 4,
                  background: `linear-gradient(90deg, ${ACCENT1}, ${ACCENT2})`,
                  transform: `scaleX(${strike})`,
                  transformOrigin: 'left center',
                }}
              />
            </div>
          );
        })}
      </div>
      <div
        style={{
          marginTop: 80,
          opacity: Math.min(1, punch),
          transform: `scale(${0.75 + Math.min(1, punch) * 0.25})`,
          fontSize: 88,
          fontWeight: 800,
          color: TEXT,
          letterSpacing: '0.03em',
        }}
      >
        ぜんぶ、<span style={gradientText}>自動に。</span>
      </div>
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------- scene 3: demo

const KPI: React.FC<{
  label: string;
  prefix?: string;
  suffix?: string;
  from: number;
  to: number;
  delta: string;
  local: number;
}> = ({label, prefix = '', suffix = '', from, to, delta, local}) => {
  const t = interpolate(local, [22, 58], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });
  const value = Math.round(from + (to - from) * t);
  return (
    <div
      style={{
        flex: 1,
        background: 'rgba(255,255,255,0.04)',
        border: CARD_BORDER,
        borderRadius: 22,
        padding: '26px 30px',
      }}
    >
      <div style={{fontSize: 26, color: SUB, fontWeight: 600}}>{label}</div>
      <div
        style={{
          fontSize: 52,
          fontWeight: 800,
          color: TEXT,
          marginTop: 10,
          fontVariantNumeric: 'tabular-nums',
        }}
      >
        {prefix}
        {value.toLocaleString()}
        {suffix}
      </div>
      <div style={{fontSize: 26, color: GREEN, fontWeight: 700, marginTop: 6}}>
        {delta}
      </div>
    </div>
  );
};

const BARS = [46, 68, 55, 84, 100, 76, 128];

const Chart: React.FC<{local: number}> = ({local}) => {
  const {fps} = useVideoConfig();
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'flex-end',
        gap: 22,
        height: 230,
        marginTop: 36,
        padding: '0 8px',
      }}
    >
      {BARS.map((h, i) => {
        const s = spring({
          frame: local - 26 - i * 4,
          fps,
          config: {damping: 16, mass: 0.6, stiffness: 120},
        });
        return (
          <div
            key={i}
            style={{
              flex: 1,
              height: h * 1.6,
              transform: `scaleY(${Math.min(1, s)})`,
              transformOrigin: 'bottom',
              borderRadius: 12,
              background:
                i === BARS.length - 1
                  ? `linear-gradient(180deg, ${ACCENT2}, ${ACCENT1})`
                  : 'rgba(255,255,255,0.13)',
            }}
          />
        );
      })}
    </div>
  );
};

const Caption: React.FC<{text: string; local: number; start: number; end: number}> = ({
  text,
  local,
  start,
  end,
}) => {
  const {fps} = useVideoConfig();
  const s = spring({frame: local - start, fps, config: {damping: 200}});
  const out = interpolate(local, [end - 8, end], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  if (local < start - 5) return null;
  return (
    <div
      style={{
        position: 'absolute',
        top: 150,
        left: 0,
        right: 0,
        textAlign: 'center',
        fontSize: 60,
        fontWeight: 800,
        color: TEXT,
        letterSpacing: '0.04em',
        opacity: Math.min(1, s) * out,
        transform: `translateY(${(1 - s) * 30}px)`,
      }}
    >
      {text}
    </div>
  );
};

const Demo: React.FC = () => {
  const local = useCurrentFrame();
  const {fps} = useVideoConfig();
  const out = useFadeOut(188, 200);

  // card entrance
  const enter = spring({
    frame: local,
    fps,
    config: {damping: 17, mass: 0.9, stiffness: 90},
  });

  // camera: zoom to the CTA button, then pull back a little
  const zoomIn = interpolate(local, [95, 128], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.inOut(Easing.cubic),
  });
  const zoomOut = interpolate(local, [172, 198], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.inOut(Easing.cubic),
  });
  const scale = 1 + zoomIn * 0.24 - zoomOut * 0.16;
  const shiftY = zoomIn * -250 + zoomOut * 180;

  // button press + highlight ring
  const press = interpolate(local, [148, 152, 158], [1, 0.94, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const ringIn = interpolate(local, [112, 122], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const ringOut = interpolate(local, [150, 158], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const ring = ringIn * ringOut * (0.65 + 0.35 * Math.sin(local / 2.2));

  // success toast
  const toast = spring({
    frame: local - 158,
    fps,
    config: {damping: 14, mass: 0.7, stiffness: 130},
  });

  return (
    <AbsoluteFill style={{opacity: out}}>
      <Caption text="ツールをつなぐだけで" local={local} start={14} end={92} />
      <Caption text="レポートは、自動で完成" local={local} start={150} end={200} />

      <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center'}}>
        <div
          style={{
            transform: `translateY(${(1 - enter) * 500 + shiftY}px) scale(${scale})`,
            opacity: Math.min(1, enter),
          }}
        >
          <div
            style={{
              position: 'relative',
              width: 880,
              background: CARD_BG,
              border: CARD_BORDER,
              borderRadius: 36,
              padding: 44,
              boxShadow: '0 60px 120px rgba(0,0,0,0.55)',
            }}
          >
            {/* browser dots */}
            <div style={{display: 'flex', gap: 12, marginBottom: 34}}>
              {['#FF5F57', '#FEBC2E', '#28C840'].map((c) => (
                <div
                  key={c}
                  style={{width: 18, height: 18, borderRadius: '50%', background: c}}
                />
              ))}
            </div>

            {/* app header */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                marginBottom: 30,
              }}
            >
              <div style={{display: 'flex', alignItems: 'center', gap: 18}}>
                <div
                  style={{
                    width: 44,
                    height: 44,
                    borderRadius: 12,
                    background: `linear-gradient(135deg, ${ACCENT1}, ${ACCENT2})`,
                  }}
                />
                <div style={{fontSize: 36, fontWeight: 800, color: TEXT}}>
                  ReportPilot
                </div>
              </div>
              <div style={{fontSize: 26, color: SUB, fontWeight: 600}}>
                10月 ダッシュボード
              </div>
            </div>

            {/* KPI cards */}
            <div style={{display: 'flex', gap: 22}}>
              <KPI
                label="今月のCPA"
                prefix="¥"
                from={2400}
                to={1240}
                delta="↓ 18% 改善"
                local={local}
              />
              <KPI
                label="ROAS"
                suffix="%"
                from={180}
                to={412}
                delta="↑ 24% 改善"
                local={local}
              />
            </div>

            <Chart local={local} />

            {/* CTA button inside the app */}
            <div style={{position: 'relative', marginTop: 40}}>
              <div
                style={{
                  position: 'absolute',
                  inset: -14,
                  borderRadius: 30,
                  border: `4px solid ${ACCENT2}`,
                  opacity: ring,
                }}
              />
              <div
                style={{
                  transform: `scale(${press})`,
                  height: 96,
                  borderRadius: 22,
                  background: `linear-gradient(92deg, ${ACCENT1}, ${ACCENT2})`,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 36,
                  fontWeight: 800,
                  color: '#fff',
                  letterSpacing: '0.05em',
                }}
              >
                レポートを自動生成
              </div>
            </div>

            {/* success toast */}
            {local >= 155 && (
              <div
                style={{
                  position: 'absolute',
                  top: -70,
                  left: 60,
                  right: 60,
                  transform: `translateY(${(1 - Math.min(1, toast)) * -90}px)`,
                  opacity: Math.min(1, toast),
                  background: '#0F1522',
                  border: `1px solid rgba(52,211,153,0.5)`,
                  borderRadius: 22,
                  padding: '24px 34px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 20,
                  boxShadow: '0 30px 60px rgba(0,0,0,0.5)',
                }}
              >
                <div
                  style={{
                    width: 44,
                    height: 44,
                    borderRadius: '50%',
                    background: GREEN,
                    color: '#06281C',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: 30,
                    fontWeight: 800,
                  }}
                >
                  ✓
                </div>
                <div>
                  <div style={{fontSize: 30, fontWeight: 700, color: TEXT}}>
                    月次レポートが完成しました
                  </div>
                  <div style={{fontSize: 24, color: SUB, marginTop: 4}}>
                    PDFを作成し、Slackへ送信済み
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------- scene 4: CTA

const Cta: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  const s = (delay: number) =>
    spring({frame: frame - delay, fps, config: {damping: 16, mass: 0.7, stiffness: 110}});

  const glow = 30 + 18 * Math.sin(frame / 5);
  const logoS = s(0);
  const tagS = s(10);
  const btnS = s(20);
  const urlS = s(30);

  return (
    <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center', gap: 0}}>
      <div
        style={{
          opacity: Math.min(1, logoS),
          transform: `scale(${0.8 + Math.min(1, logoS) * 0.2})`,
          display: 'flex',
          alignItems: 'center',
          gap: 26,
        }}
      >
        <div
          style={{
            width: 86,
            height: 86,
            borderRadius: 24,
            background: `linear-gradient(135deg, ${ACCENT1}, ${ACCENT2})`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: 44,
            fontWeight: 800,
            color: '#fff',
          }}
        >
          R
        </div>
        <div style={{fontSize: 84, fontWeight: 800, color: TEXT, letterSpacing: '0.02em'}}>
          ReportPilot
        </div>
      </div>

      <div
        style={{
          marginTop: 40,
          opacity: Math.min(1, tagS),
          transform: `translateY(${(1 - tagS) * 30}px)`,
          fontSize: 46,
          fontWeight: 600,
          color: SUB,
          letterSpacing: '0.06em',
        }}
      >
        レポート作成を、ゼロ時間に。
      </div>

      <div
        style={{
          marginTop: 90,
          opacity: Math.min(1, btnS),
          transform: `scale(${0.85 + Math.min(1, btnS) * 0.15})`,
          padding: '38px 90px',
          borderRadius: 28,
          background: `linear-gradient(92deg, ${ACCENT1}, ${ACCENT2})`,
          fontSize: 46,
          fontWeight: 800,
          color: '#fff',
          letterSpacing: '0.06em',
          boxShadow: `0 0 ${glow}px rgba(139,92,246,0.75)`,
        }}
      >
        14日間 無料で試す
      </div>

      <div
        style={{
          marginTop: 60,
          opacity: Math.min(1, urlS) * 0.9,
          fontSize: 32,
          color: SUB,
          letterSpacing: '0.14em',
          fontWeight: 600,
        }}
      >
        reportpilot.jp
      </div>
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------- root

export const Ad: React.FC = () => {
  return (
    <AbsoluteFill style={{fontFamily: FONT}}>
      <Backdrop />
      <Sequence durationInFrames={75}>
        <Hook />
      </Sequence>
      <Sequence from={75} durationInFrames={95}>
        <Problem />
      </Sequence>
      <Sequence from={168} durationInFrames={200}>
        <Demo />
      </Sequence>
      <Sequence from={365} durationInFrames={85}>
        <Cta />
      </Sequence>
    </AbsoluteFill>
  );
};
