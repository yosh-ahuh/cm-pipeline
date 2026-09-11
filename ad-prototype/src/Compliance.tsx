import React, {createContext, useContext} from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';

/**
 * 法務・配信仕様のオーバーレイ（cm-pipeline/cm/delivery.py の render_props と同形の props）。
 *  - DisclosureCaption: AI利用の開示テロップを末尾 N 秒に表示（JIAA 自主開示ガイドライン 2026-04）
 *  - SafeZone: 媒体 UI と重なる上下帯（リール上14% / 下35% 等）。Telop / Watermark が useSafeInsets で避ける
 *  - SafeZoneGuides: debugSafeZone=true のとき帯を可視化（Studio での確認用）
 */
export type Disclosure = {
  text: string;
  seconds?: number;
  position?: 'bottom-right' | 'bottom-left' | 'top-right' | 'top-left';
  minHeightPct?: number;
};
export type SafeZone = {topPct?: number; bottomPct?: number};
export type Compliance = {
  disclosure?: Disclosure | null;
  safeZone?: SafeZone;
  captions?: 'burn_in' | 'optional' | 'none';
  debugSafeZone?: boolean;
};

const ComplianceContext = createContext<Compliance>({});

export const ComplianceProvider: React.FC<{value?: Compliance; children: React.ReactNode}> = ({
  value,
  children,
}) => <ComplianceContext.Provider value={value ?? {}}>{children}</ComplianceContext.Provider>;

export const useCompliance = (): Compliance => useContext(ComplianceContext);

/** 媒体セーフゾーンを px で返す（未指定なら 0）。 */
export const useSafeInsets = (): {top: number; bottom: number} => {
  const {height} = useVideoConfig();
  const {safeZone} = useCompliance();
  return {
    top: (height * (safeZone?.topPct ?? 0)) / 100,
    bottom: (height * (safeZone?.bottomPct ?? 0)) / 100,
  };
};

const FONT = '"Hiragino Sans", "Hiragino Kaku Gothic ProN", "Noto Sans JP", sans-serif';

export const DisclosureCaption: React.FC = () => {
  const {disclosure} = useCompliance();
  const frame = useCurrentFrame();
  const {fps, durationInFrames, height} = useVideoConfig();
  const insets = useSafeInsets();
  if (!disclosure || !disclosure.text) return null;
  const seconds = disclosure.seconds ?? 2;
  const start = Math.max(0, durationInFrames - Math.round(seconds * fps));
  if (frame < start) return null;
  const opacity = interpolate(frame, [start, start + 8], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  // 可読性の下限: 画面高の minHeightPct（既定 3%）をキャプション行高に
  const lineH = (height * (disclosure.minHeightPct ?? 3)) / 100;
  const fontSize = Math.max(18, lineH * 0.62);
  const pos = disclosure.position ?? 'bottom-right';
  const style: React.CSSProperties = {
    position: 'absolute',
    padding: `${lineH * 0.18}px ${lineH * 0.45}px`,
    borderRadius: lineH * 0.25,
    background: 'rgba(0,0,0,0.55)',
    color: '#FFFFFF',
    fontFamily: FONT,
    fontSize,
    fontWeight: 500,
    letterSpacing: '0.02em',
    lineHeight: 1.3,
    opacity,
    whiteSpace: 'nowrap',
  };
  const edge = Math.round(lineH * 0.8);
  if (pos.startsWith('bottom')) style.bottom = insets.bottom + edge;
  else style.top = insets.top + edge;
  if (pos.endsWith('right')) style.right = edge;
  else style.left = edge;
  return (
    <AbsoluteFill style={{pointerEvents: 'none'}}>
      <div style={style}>{disclosure.text}</div>
    </AbsoluteFill>
  );
};

export const SafeZoneGuides: React.FC = () => {
  const {debugSafeZone} = useCompliance();
  const insets = useSafeInsets();
  if (!debugSafeZone) return null;
  const band: React.CSSProperties = {
    position: 'absolute',
    left: 0,
    right: 0,
    background: 'rgba(255,40,40,0.18)',
    borderColor: 'rgba(255,40,40,0.7)',
    borderStyle: 'dashed',
    borderWidth: 0,
  };
  return (
    <AbsoluteFill style={{pointerEvents: 'none'}}>
      <div style={{...band, top: 0, height: insets.top, borderBottomWidth: 2}} />
      <div style={{...band, bottom: 0, height: insets.bottom, borderTopWidth: 2}} />
    </AbsoluteFill>
  );
};
