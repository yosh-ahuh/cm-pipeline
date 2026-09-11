import React from 'react';
import {
  AbsoluteFill,
  Audio,
  Easing,
  Img,
  OffthreadVideo,
  Sequence,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {
  Compliance,
  ComplianceProvider,
  DisclosureCaption,
  SafeZoneGuides,
  useSafeInsets,
} from './Compliance';

/**
 * SpotAd — project.yaml 駆動の汎用コンポジション。
 * cm-pipeline/cm/remotion_props.py が組み立てた props を --props で受け取り、
 * カット表（live-action / ui / graphic / cta）・スプラッシュ・音声・ブランド・法務を描く。
 * MiraiCM.tsx（1件目の手作り）で確立した画づくり（グレードB・グレイン・手持ちドリフト・
 * メタルテロップ・コード描画の端末筐体）を、データで差し替え可能にしたもの。
 */

// ---------------------------------------------------------------- types
export type SpotBrand = {
  name: string;
  primary: string;
  accent?: string;
  dark?: string;
  appIcon?: string;
  logo?: string;
  watermark?: boolean;
  tagline?: string;
};

type CutBase = {id: string; from: number; dur: number; telop?: string[]};
export type LiveCutSpec = CutBase & {
  type: 'live-action';
  src?: string;
  srcVertical?: string;
  still?: string;
  anchorX?: number;
  subject?: string;
  rate?: number;
};
export type UiCutSpec = CutBase & {type: 'ui'; screens: string[]; caption?: string};
export type GraphicCutSpec = CutBase & {
  type: 'graphic';
  label?: string;
  number?: number;
  unit?: string;
  note?: string;
  background?: string;
};
export type CtaCutSpec = CutBase & {
  type: 'cta';
  badges?: string[];
  button?: string;
  search?: string;
  note?: string;
};
export type SpotCut = LiveCutSpec | UiCutSpec | GraphicCutSpec | CtaCutSpec;

export type SpotAudio = {
  narration?: {src: string; from: number; dur?: number}[];
  bgm?: {src: string; from: number; dur?: number; volume?: number}[];
  soundLogo?: string;
  sfx?: {src: string; from: number; volume?: number}[];
};

export type SpotAdProps = {
  durationInFrames: number;
  brand: SpotBrand;
  splash: {variant: 'A' | 'B' | 'C'; from: number; dur: number};
  cuts: SpotCut[];
  audio?: SpotAudio;
  compliance?: Compliance;
  grain?: string;
};

// ---------------------------------------------------------------- shared
const FONT = '"Hiragino Sans", "Hiragino Kaku Gothic ProN", "Noto Sans JP", sans-serif';
const ROUND = '"Hiragino Maru Gothic ProN", "Hiragino Sans", sans-serif';
const GRADE = 'url(#spotGradeB) saturate(0.86) contrast(1.04)';
const SCREEN_AR = 0.462;

type Aspect = 'wide' | 'square' | 'vertical';
const useAspect = (): Aspect => {
  const {width, height} = useVideoConfig();
  const r = width / height;
  return r > 1.2 ? 'wide' : r >= 0.9 ? 'square' : 'vertical';
};

const BrandCtx = React.createContext<SpotBrand>({name: 'SPOT', primary: '#2846D9'});
const useBrand = () => React.useContext(BrandCtx);

const clamp = (f: number, a: number, b: number, o: [number, number], easing?: (t: number) => number) =>
  interpolate(f, [a, b], o, {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing});

const MetalText: React.FC<{text: string; size: number}> = ({text, size}) => (
  <div
    style={{
      position: 'relative',
      display: 'inline-block',
      fontFamily: FONT,
      fontSize: size,
      fontWeight: 900,
      letterSpacing: '0.05em',
      lineHeight: 1.35,
      filter: 'drop-shadow(0 6px 10px rgba(0,0,0,0.55))',
    }}
  >
    <span
      style={{
        position: 'absolute',
        inset: 0,
        WebkitTextStroke: `${Math.max(8, size * 0.16)}px rgba(10,10,12,0.9)`,
        color: 'transparent',
      }}
    >
      {text}
    </span>
    <span
      style={{
        position: 'relative',
        background: 'linear-gradient(180deg, #FFFFFF 25%, #DDE1E7 48%, #A8AEB9 62%, #F2F4F7 100%)',
        WebkitBackgroundClip: 'text',
        backgroundClip: 'text',
        WebkitTextFillColor: 'transparent',
      }}
    >
      {text}
    </span>
  </div>
);

const Telop: React.FC<{lines?: string[]}> = ({lines}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const aspect = useAspect();
  const insets = useSafeInsets();
  if (!lines || !lines.length) return null;
  const s = spring({frame: frame - 6, fps, config: {damping: 200}});
  const size = aspect === 'wide' ? 78 : 56;
  const bottom = Math.max(aspect === 'vertical' ? 180 : 56, insets.bottom + 24);
  return (
    <AbsoluteFill>
      <div
        style={{
          position: 'absolute',
          left: 0,
          right: 0,
          bottom: 0,
          height: aspect === 'vertical' ? 420 : 260,
          background: 'linear-gradient(180deg, rgba(0,0,0,0) 0%, rgba(0,0,0,0.35) 75%)',
        }}
      />
      <div
        style={{
          position: 'absolute',
          left: 24,
          right: 24,
          bottom,
          textAlign: 'center',
          opacity: Math.min(1, s),
          transform: `translateY(${(1 - s) * 40}px)`,
        }}
      >
        {lines.map((l) => (
          <div key={l}>
            <MetalText text={l} size={size} />
          </div>
        ))}
      </div>
    </AbsoluteFill>
  );
};

const Grain: React.FC<{src?: string; opacity?: number}> = ({src = 'spot/grain.png', opacity = 0.07}) => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill
      style={{
        backgroundImage: `url(${staticFile(src)})`,
        backgroundPosition: `${(frame * 97) % 512}px ${(frame * 53) % 512}px`,
        opacity,
        mixBlendMode: 'overlay',
        pointerEvents: 'none',
      }}
    />
  );
};

const Vignette: React.FC = () => (
  <AbsoluteFill
    style={{
      background:
        'radial-gradient(ellipse 75% 70% at 50% 48%, rgba(0,0,0,0) 55%, rgba(8,10,14,0.24) 100%)',
      pointerEvents: 'none',
    }}
  />
);

const BrandMark: React.FC<{iconH: number; fontSize: number; color?: string; gap?: number}> = ({
  iconH,
  fontSize,
  color = '#fff',
  gap = 16,
}) => {
  const brand = useBrand();
  return (
    <div style={{display: 'flex', alignItems: 'center', gap}}>
      {brand.appIcon ? (
        <div style={{background: '#fff', borderRadius: iconH * 0.26, padding: Math.max(3, iconH * 0.08)}}>
          <Img src={staticFile(brand.appIcon)} style={{height: iconH, borderRadius: iconH * 0.22, display: 'block'}} />
        </div>
      ) : (
        <div
          style={{
            width: iconH,
            height: iconH,
            borderRadius: '50%',
            border: `${Math.max(3, iconH * 0.14)}px solid ${brand.primary}`,
            background: '#fff',
            position: 'relative',
          }}
        >
          <div
            style={{
              position: 'absolute',
              inset: '32%',
              borderRadius: '50%',
              background: brand.primary,
            }}
          />
        </div>
      )}
      <span style={{fontFamily: ROUND, fontWeight: 800, fontSize, color, letterSpacing: '0.04em'}}>
        {brand.name}
      </span>
    </div>
  );
};

const Watermark: React.FC = () => {
  const aspect = useAspect();
  const insets = useSafeInsets();
  const brand = useBrand();
  if (brand.watermark === false) return null;
  const top = Math.max(aspect === 'vertical' ? 150 : 36, insets.top + 16);
  const iconH = aspect === 'wide' ? 58 : 48;
  const fontSize = aspect === 'wide' ? 46 : 38;
  return (
    <div
      style={{
        position: 'absolute',
        top,
        left: aspect === 'wide' ? 44 : 40,
        filter: 'drop-shadow(0 2px 6px rgba(0,0,0,0.45))',
      }}
    >
      <BrandMark iconH={iconH} fontSize={fontSize} gap={12} />
    </div>
  );
};

// ---------------------------------------------------------------- cover / splash
const Cover: React.FC<{cuts: SpotCut[]}> = ({cuts}) => {
  const brand = useBrand();
  const aspect = useAspect();
  const first = cuts.find((c) => c.telop && c.telop.length);
  const line = brand.tagline || (first && first.telop ? first.telop[0] : brand.name);
  return (
    <AbsoluteFill
      style={{
        background: brand.primary,
        alignItems: 'center',
        justifyContent: 'center',
        gap: aspect === 'vertical' ? 60 : 36,
      }}
    >
      <BrandMark iconH={52} fontSize={44} />
      <div
        style={{
          fontFamily: FONT,
          fontWeight: 900,
          fontSize: aspect === 'wide' ? 96 : 68,
          color: '#fff',
          textAlign: 'center',
          padding: '0 60px',
          textShadow: '0 8px 24px rgba(0,0,0,0.25)',
        }}
      >
        {line}
      </div>
    </AbsoluteFill>
  );
};

const hexA = (hex: string, a: number) => {
  const m = /^#?([0-9a-f]{6})$/i.exec(hex.trim());
  if (!m) return `rgba(0,0,0,${a})`;
  const n = parseInt(m[1], 16);
  return `rgba(${(n >> 16) & 255},${(n >> 8) & 255},${n & 255},${a})`;
};

const Splash: React.FC<{variant: 'A' | 'B' | 'C'; dur: number}> = ({variant, dur}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const aspect = useAspect();
  const brand = useBrand();
  const iconH = aspect === 'wide' ? 200 : 148;
  const fontSize = aspect === 'wide' ? 130 : 92;
  const iconS = spring({frame: frame - 4, fps, config: {damping: 12, mass: 0.6, stiffness: 160}});
  const textS = spring({frame: frame - 24, fps, config: {damping: 15, mass: 0.7, stiffness: 130}});
  const ring = clamp(frame, 4, 40, [0, 1], Easing.out(Easing.cubic));
  const fadeOut = clamp(frame, dur - 10, dur, [1, 0]);
  const accent = brand.accent || brand.primary;
  const dark = brand.dark || '#1A1B20';
  return (
    <AbsoluteFill style={{background: '#fff', justifyContent: 'center', alignItems: 'center', opacity: fadeOut}}>
      {variant === 'A' && (
        <div
          style={{
            position: 'absolute',
            width: 200 + ring * 1500,
            height: 200 + ring * 1500,
            borderRadius: '50%',
            border: `${Math.max(2, 30 * (1 - ring))}px solid ${hexA(brand.primary, 0.35 * (1 - ring))}`,
          }}
        />
      )}
      {variant === 'B' &&
        Array.from({length: 26}).map((_, i) => {
          const t = clamp(frame, 6 + (i % 5) * 2, 60, [0, 1], Easing.out(Easing.quad));
          const ang = (i / 26) * Math.PI * 2;
          const dist = 120 + t * (700 + (i % 4) * 160);
          return (
            <div
              key={i}
              style={{
                position: 'absolute',
                left: `calc(50% + ${Math.cos(ang) * dist}px)`,
                top: `calc(50% + ${Math.sin(ang) * dist + t * t * 380}px)`,
                width: 14 + (i % 3) * 6,
                height: 22 + (i % 2) * 8,
                borderRadius: 3,
                background: i % 2 ? accent : brand.primary,
                opacity: 1 - t * 0.85,
                transform: `rotate(${t * 720 + i * 40}deg)`,
              }}
            />
          );
        })}
      {variant === 'C' && (
        <div
          style={{
            position: 'absolute',
            width: 1400 * Math.min(1.06, ring * 1.1),
            height: 1400 * Math.min(1.06, ring * 1.1),
            borderRadius: '50%',
            background: `radial-gradient(circle, ${hexA(brand.primary, 0.22)} 0%, ${hexA(brand.primary, 0)} 70%)`,
          }}
        />
      )}
      <div style={{display: 'flex', alignItems: 'center', gap: 36}}>
        <div
          style={{
            opacity: Math.min(1, iconS),
            transform: `scale(${0.4 + Math.min(1, iconS) * 0.6}) rotate(${(1 - Math.min(1, iconS)) * -12}deg)`,
          }}
        >
          {brand.appIcon ? (
            <Img
              src={staticFile(brand.appIcon)}
              style={{
                height: iconH,
                borderRadius: iconH * 0.22,
                display: 'block',
                boxShadow: `0 24px 60px ${hexA(brand.primary, 0.25)}`,
              }}
            />
          ) : (
            <BrandMark iconH={iconH * 0.7} fontSize={0} color="transparent" />
          )}
        </div>
        <div style={{overflow: 'hidden'}}>
          <span
            style={{
              display: 'inline-block',
              fontFamily: ROUND,
              fontWeight: 800,
              fontSize,
              color: dark,
              letterSpacing: '0.05em',
              opacity: Math.min(1, textS),
              transform: `translateX(${(1 - Math.min(1, textS)) * -80}px)`,
            }}
          >
            {brand.name}
          </span>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------- cuts
const LiveCut: React.FC<{cut: LiveCutSpec; grain?: string}> = ({cut, grain}) => {
  const frame = useCurrentFrame();
  const aspect = useAspect();
  const brand = useBrand();
  const fadeIn = clamp(frame, 0, 8, [0, 1]);
  const fadeOut = clamp(frame, cut.dur - 7, cut.dur, [1, 0]);
  const driftX = Math.sin(frame / 46) * 4 + Math.sin(frame / 13) * 0.8;
  const driftY = Math.cos(frame / 61) * 3 + Math.cos(frame / 17) * 0.6;
  const anchorX = cut.anchorX ?? 50;
  const usePortrait = cut.srcVertical && aspect !== 'wide';
  const src = usePortrait ? cut.srcVertical : cut.src;
  const objectPosition = aspect === 'wide' ? 'center' : `${anchorX}% 50%`;
  // Ken Burns（動画未生成でスチルだけあるとき）
  const kb = 1.02 + clamp(frame, 0, cut.dur, [0, 0.06]);
  return (
    <AbsoluteFill style={{background: '#000', opacity: fadeIn * fadeOut}}>
      <AbsoluteFill style={{transform: `translate(${driftX}px, ${driftY}px) scale(1.015)`}}>
        {src ? (
          <OffthreadVideo
            src={staticFile(src)}
            playbackRate={cut.rate ?? 1}
            style={{width: '100%', height: '100%', objectFit: 'cover', objectPosition, filter: GRADE}}
            muted
          />
        ) : cut.still ? (
          <Img
            src={staticFile(cut.still)}
            style={{
              width: '100%',
              height: '100%',
              objectFit: 'cover',
              objectPosition,
              filter: GRADE,
              transform: `scale(${kb})`,
            }}
          />
        ) : (
          // 生成待ちプレースホルダ（実写は AI 生成。偽 UI は作らない）
          <AbsoluteFill
            style={{
              background: `linear-gradient(160deg, #2f3947, #161b22)`,
              alignItems: 'center',
              justifyContent: 'center',
              padding: 80,
            }}
          >
            <div style={{fontFamily: FONT, color: '#9AA3B2', fontSize: 30, letterSpacing: '0.1em'}}>
              LIVE-ACTION · 生成待ち
            </div>
            <div
              style={{
                marginTop: 18,
                fontFamily: FONT,
                color: '#E6E9EF',
                fontSize: aspect === 'wide' ? 44 : 36,
                fontWeight: 700,
                textAlign: 'center',
                maxWidth: 900,
                lineHeight: 1.5,
              }}
            >
              {cut.subject || cut.id}
            </div>
            <div style={{marginTop: 30, width: 120, height: 6, borderRadius: 3, background: brand.primary}} />
          </AbsoluteFill>
        )}
      </AbsoluteFill>
      <Vignette />
      <Grain src={grain} />
      <Telop lines={cut.telop} />
    </AbsoluteFill>
  );
};

const DeviceFrame: React.FC<{height: number; children: React.ReactNode}> = ({height, children}) => {
  const pad = Math.round(height * 0.017);
  const btn = (side: 'left' | 'right', top: string, h: number) => (
    <div style={{position: 'absolute', [side]: -4, top, width: 5, height: h, borderRadius: 3, background: '#2b2d32'}} />
  );
  return (
    <div
      style={{
        position: 'relative',
        padding: pad,
        background: 'linear-gradient(145deg, #43464d, #131418)',
        borderRadius: height * 0.088,
        boxShadow: '0 40px 70px rgba(0,0,0,0.4), inset 0 0 0 2px rgba(255,255,255,0.09)',
      }}
    >
      {btn('left', '20%', height * 0.055)}
      {btn('left', '28%', height * 0.055)}
      {btn('right', '23%', height * 0.1)}
      <div
        style={{
          position: 'relative',
          width: height * SCREEN_AR,
          height,
          borderRadius: height * 0.062,
          overflow: 'hidden',
          background: '#000',
        }}
      >
        {children}
      </div>
    </div>
  );
};

const UiCut: React.FC<{cut: UiCutSpec}> = ({cut}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const aspect = useAspect();
  const insets = useSafeInsets();
  const brand = useBrand();
  const enter = spring({frame, fps, config: {damping: 15, mass: 0.9, stiffness: 90}});
  const fadeOut = clamp(frame, cut.dur - 7, cut.dur, [1, 0]);
  const avail = useVideoConfig().height - insets.top - insets.bottom;
  const phoneH = Math.min(aspect === 'wide' ? 690 : aspect === 'square' ? 520 : 760, avail * 0.66);
  const screens = cut.screens && cut.screens.length ? cut.screens : [];
  // 画面切替: 各スクショを均等尺でクロスフェード
  const per = Math.max(1, Math.floor(cut.dur / Math.max(1, screens.length)));
  return (
    <AbsoluteFill
      style={{
        background: `linear-gradient(180deg, ${hexA(brand.primary, 0.08)}, #F5F6F8)`,
        alignItems: 'center',
        justifyContent: 'center',
        paddingTop: insets.top,
        paddingBottom: insets.bottom,
        opacity: fadeOut,
      }}
    >
      <div
        style={{
          opacity: Math.min(1, enter),
          transform: `perspective(1400px) rotateX(${(1 - Math.min(1, enter)) * 28}deg) translateY(${(1 - Math.min(1, enter)) * 60}px)`,
        }}
      >
        <DeviceFrame height={phoneH}>
          {screens.length ? (
            screens.map((s, i) => {
              const a = clamp(frame, i * per - 6, i * per + 6, [0, 1]);
              const b = i === screens.length - 1 ? 1 : clamp(frame, (i + 1) * per - 6, (i + 1) * per + 6, [1, 0]);
              return (
                <Img
                  key={s}
                  src={staticFile(s)}
                  style={{position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover', opacity: a * b}}
                />
              );
            })
          ) : (
            // スクショ未提供: 明示的なスケルトン（実 UI のみを合成する方針。偽 UI は描かない）
            <div style={{position: 'absolute', inset: 0, background: '#EEF0F3', padding: 24}}>
              <div style={{fontFamily: FONT, fontSize: 18, color: '#7C8494', letterSpacing: '0.08em'}}>UI スクショ待ち</div>
              {[0, 1, 2, 3, 4].map((i) => (
                <div key={i} style={{marginTop: 18, height: 22, width: `${85 - i * 12}%`, borderRadius: 6, background: '#D6DAE1'}} />
              ))}
            </div>
          )}
        </DeviceFrame>
      </div>
      {cut.caption && (
        <div
          style={{
            marginTop: 34,
            fontFamily: FONT,
            fontSize: aspect === 'wide' ? 34 : 28,
            fontWeight: 700,
            color: brand.dark || '#1A1B20',
          }}
        >
          {cut.caption}
        </div>
      )}
      <Telop lines={cut.telop} />
    </AbsoluteFill>
  );
};

const GraphicCut: React.FC<{cut: GraphicCutSpec}> = ({cut}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const brand = useBrand();
  const aspect = useAspect();
  const capS = spring({frame: frame - 2, fps, config: {damping: 200}});
  const enter = spring({frame: frame - 8, fps, config: {damping: 12, mass: 0.6, stiffness: 150}});
  const landAt = Math.min(44, cut.dur - 16);
  const t = clamp(frame, 10, landAt, [0, 1], Easing.out(Easing.cubic));
  const num = cut.number != null ? Math.round(cut.number * t) : null;
  const landS = spring({frame: frame - landAt, fps, config: {damping: 10, mass: 0.5, stiffness: 200}});
  const punch = frame >= landAt ? Math.sin(Math.min(1, landS) * Math.PI) : 0;
  const glow = frame >= landAt ? Math.max(0, 1 - (frame - landAt) / 20) : 0;
  const fadeIn = clamp(frame, 0, 8, [0, 1]);
  const fadeOut = clamp(frame, cut.dur - 8, cut.dur, [1, 0]);
  const big = aspect === 'wide' ? 260 : 190;
  const mid = aspect === 'wide' ? 120 : 84;
  return (
    <AbsoluteFill style={{background: '#000', opacity: fadeIn * fadeOut}}>
      {cut.background ? (
        <OffthreadVideo
          src={staticFile(cut.background)}
          playbackRate={0.77}
          style={{width: '100%', height: '100%', objectFit: 'cover', filter: GRADE}}
          muted
        />
      ) : (
        <AbsoluteFill style={{background: `radial-gradient(ellipse at 50% 40%, ${hexA(brand.primary, 0.55)}, #0B0D14 70%)`}} />
      )}
      <AbsoluteFill style={{background: 'radial-gradient(ellipse 65% 55% at 50% 50%, rgba(0,0,0,0.35), rgba(0,0,0,0) 75%)'}} />
      <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center'}}>
        <div style={{textAlign: 'center', opacity: Math.min(1, capS)}}>
          {cut.label && (
            <div style={{transform: `translateY(${(1 - capS) * 30}px)`}}>
              <MetalText text={cut.label} size={aspect === 'wide' ? 84 : 60} />
            </div>
          )}
          {num != null && (
            <div
              style={{
                marginTop: 6,
                opacity: Math.min(1, enter),
                transform: `scale(${0.7 + Math.min(1, enter) * 0.3 + punch * 0.14})`,
                display: 'flex',
                alignItems: 'baseline',
                justifyContent: 'center',
                gap: 8,
                filter: glow > 0 ? `drop-shadow(0 0 ${40 * glow}px ${hexA(brand.primary, 0.85 * glow)})` : undefined,
              }}
            >
              <MetalText text={`${num}`} size={big} />
              {cut.unit && <MetalText text={cut.unit} size={mid} />}
            </div>
          )}
          {cut.note && (
            <div style={{marginTop: 18, fontFamily: FONT, color: 'rgba(255,255,255,0.75)', fontSize: 28}}>{cut.note}</div>
          )}
        </div>
      </AbsoluteFill>
      <Grain />
      <Telop lines={cut.telop} />
    </AbsoluteFill>
  );
};

const CtaCut: React.FC<{cut: CtaCutSpec}> = ({cut}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const brand = useBrand();
  const aspect = useAspect();
  const insets = useSafeInsets();
  const s = (d: number) => spring({frame: frame - d, fps, config: {damping: 16, mass: 0.7, stiffness: 110}});
  const logoS = s(0);
  const searchS = s(14);
  const btnS = s(26);
  const glow = 18 + 10 * Math.sin(frame / 5);
  const dark = brand.dark || '#1A1B20';
  const typed = cut.search ? cut.search.slice(0, Math.max(0, Math.floor((frame - 20) / 3))) : '';
  const badges = cut.badges || [];
  return (
    <AbsoluteFill
      style={{
        background: '#fff',
        justifyContent: 'center',
        alignItems: 'center',
        paddingTop: insets.top,
        paddingBottom: insets.bottom + 60,
        gap: aspect === 'wide' ? 44 : 34,
      }}
    >
      <div style={{position: 'relative', opacity: Math.min(1, logoS), transform: `scale(${0.85 + Math.min(1, logoS) * 0.15})`}}>
        {brand.logo ? (
          <Img src={staticFile(brand.logo)} style={{height: aspect === 'wide' ? 170 : 130}} />
        ) : (
          <BrandMark iconH={aspect === 'wide' ? 150 : 110} fontSize={aspect === 'wide' ? 110 : 80} color={dark} gap={30} />
        )}
        {badges[0] && (
          <div
            style={{
              position: 'absolute',
              right: -200,
              top: -60,
              width: 190,
              height: 190,
              borderRadius: '50%',
              background: brand.primary,
              color: '#fff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              textAlign: 'center',
              padding: 18,
              fontFamily: FONT,
              fontWeight: 800,
              fontSize: 30,
              lineHeight: 1.2,
              transform: `rotate(8deg) scale(${0.9 + 0.1 * Math.sin(frame / 9)})`,
              boxShadow: `0 12px 30px ${hexA(brand.primary, 0.35)}`,
            }}
          >
            {badges[0]}
          </div>
        )}
      </div>
      {cut.search && (
        <div
          style={{
            opacity: Math.min(1, searchS),
            transform: `translateY(${(1 - searchS) * 30}px)`,
            display: 'flex',
            alignItems: 'center',
            gap: 24,
            border: `4px solid ${dark}`,
            borderRadius: 60,
            padding: '22px 46px',
            fontFamily: FONT,
            fontSize: 48,
            fontWeight: 700,
            color: dark,
          }}
        >
          <span style={{fontSize: 44}}>🔍</span>
          <span style={{minWidth: 380, display: 'inline-block'}}>
            {typed}
            {frame >= 20 && frame < 45 && Math.floor(frame / 4) % 2 === 0 && <span style={{color: brand.primary}}>|</span>}
          </span>
          <span style={{background: dark, color: '#fff', borderRadius: 40, padding: '10px 34px', fontSize: 36}}>検索</span>
        </div>
      )}
      {badges[1] && (
        <div
          style={{
            border: `3px solid ${brand.primary}`,
            color: brand.primary,
            borderRadius: 40,
            padding: '10px 38px',
            fontFamily: FONT,
            fontWeight: 800,
            fontSize: 36,
            background: hexA(brand.primary, 0.06),
            opacity: Math.min(1, searchS),
          }}
        >
          {badges[1]}
        </div>
      )}
      {cut.button && (
        <div
          style={{
            opacity: Math.min(1, btnS),
            transform: `scale(${0.8 + Math.min(1, btnS) * 0.2})`,
            background: brand.primary,
            color: '#fff',
            borderRadius: 24,
            padding: '30px 80px',
            fontFamily: FONT,
            fontWeight: 900,
            fontSize: aspect === 'wide' ? 58 : 48,
            boxShadow: `0 ${glow}px ${glow * 2}px ${hexA(brand.primary, 0.35)}`,
          }}
        >
          {cut.button}
        </div>
      )}
      {cut.note && (
        <div style={{fontFamily: FONT, color: '#8A8F99', fontSize: 30, letterSpacing: '0.08em'}}>{cut.note}</div>
      )}
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------- composition
const Body: React.FC<SpotAdProps> = ({durationInFrames, brand, splash, cuts, audio, grain}) => {
  const sound = audio || {};
  return (
    <AbsoluteFill style={{background: '#000', fontFamily: FONT}}>
      <svg width="0" height="0" style={{position: 'absolute'}}>
        <defs>
          <filter id="spotGradeB" colorInterpolationFilters="sRGB">
            <feComponentTransfer>
              <feFuncR type="table" tableValues="0.024 0.227 0.494 0.755 0.980" />
              <feFuncG type="table" tableValues="0.039 0.243 0.502 0.759 0.984" />
              <feFuncB type="table" tableValues="0.063 0.267 0.510 0.750 0.965" />
            </feComponentTransfer>
          </filter>
        </defs>
      </svg>
      <Sequence from={0} durationInFrames={1}>
        <Cover cuts={cuts} />
      </Sequence>
      <Sequence from={splash.from} durationInFrames={splash.dur}>
        <Splash variant={splash.variant} dur={splash.dur} />
        {sound.soundLogo && <Audio src={staticFile(sound.soundLogo)} />}
      </Sequence>
      {cuts.map((cut) => (
        <Sequence key={cut.id} from={cut.from} durationInFrames={cut.dur}>
          {cut.type === 'live-action' && <LiveCut cut={cut} grain={grain} />}
          {cut.type === 'ui' && <UiCut cut={cut} />}
          {cut.type === 'graphic' && <GraphicCut cut={cut} />}
          {cut.type === 'cta' && <CtaCut cut={cut} />}
        </Sequence>
      ))}
      <Sequence from={splash.from + splash.dur} durationInFrames={Math.max(1, durationInFrames - splash.from - splash.dur)}>
        <Watermark />
      </Sequence>
      {(sound.narration || []).map((n, i) => (
        <Sequence key={`na${i}`} from={n.from} durationInFrames={n.dur ?? 150}>
          <Audio src={staticFile(n.src)} />
        </Sequence>
      ))}
      {(sound.bgm || []).map((b, i) => (
        <Sequence key={`bgm${i}`} from={b.from} durationInFrames={b.dur ?? durationInFrames - b.from}>
          <Audio src={staticFile(b.src)} volume={b.volume ?? 0.35} loop />
        </Sequence>
      ))}
      {(sound.sfx || []).map((x, i) => (
        <Sequence key={`sfx${i}`} from={x.from} durationInFrames={45}>
          <Audio src={staticFile(x.src)} volume={x.volume ?? 0.8} />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};

export const SpotAd: React.FC<SpotAdProps> = (props) => (
  <ComplianceProvider value={props.compliance}>
    <BrandCtx.Provider value={props.brand}>
      <AbsoluteFill>
        <Body {...props} />
        <DisclosureCaption />
        <SafeZoneGuides />
      </AbsoluteFill>
    </BrandCtx.Provider>
  </ComplianceProvider>
);

/** Studio 用のデモ props（cm-pipeline が実 props を渡すまでの見本）。 */
export const DEMO_PROPS: SpotAdProps = {
  durationInFrames: 961,
  brand: {name: 'SPOT', primary: '#2846D9', accent: '#6180F5', dark: '#15161C', tagline: 'Every spot, in a day.'},
  splash: {variant: 'A', from: 1, dur: 60},
  cuts: [
    {type: 'live-action', id: 'cut1', from: 61, dur: 150, subject: '疲れた現場担当が停車中の車内でため息', telop: ['まだ、持ち帰っていますか?']},
    {type: 'graphic', id: 'stat', from: 211, dur: 90, label: 'その作業に、月', number: 40, unit: '時間。', note: '※自社調べ'},
    {type: 'ui', id: 'ui', from: 301, dur: 200, screens: [], caption: '撮るだけで、台帳が自動作成', telop: ['スマホで撮るだけ。']},
    {type: 'live-action', id: 'cut2', from: 501, dur: 150, subject: '客先の担当者が受信して笑顔', telop: ['その場で、提出完了。']},
    {type: 'cta', id: 'cta', from: 651, dur: 310, badges: ['累計50万DL突破', 'プロジェクト300万件突破'], button: '今すぐ 無料ダウンロード', search: 'ミライ工事写真', note: 'App Store / Google Play 対応'},
  ],
};
