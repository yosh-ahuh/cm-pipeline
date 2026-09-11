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

const FONT =
  '"Hiragino Sans", "Hiragino Kaku Gothic ProN", "Noto Sans JP", sans-serif';
const RED = '#D7000F';
const DARK = '#1A1A1A';

// timeline (30fps / 900 frames)
// ナレーションはシーンとは独立したトラックに置く(シーン境界で切れないように)
const S1 = {from: 0, dur: 125};
const S2 = {from: 125, dur: 130};
const S2B = {from: 255, dur: 65}; // 「月40時間」数字カット
const S3A = {from: 320, dur: 90};
const S3A_FROM = 320;
const S3B = {from: 410, dur: 110};
const S4 = {from: 520, dur: 110};
const S5 = {from: 630, dur: 85}; // 送信して笑顔
const S5B = {from: 715, dur: 80}; // 客先リアクション(通知の余韻を確保)
const S6 = {from: 795, dur: 105};

// 各ナレーションの実尺(30fps換算 + 余白10f)
const NA_DUR = [109, 162, 155, 95, 122, 105];

// ---------------------------------------------------------------- aspect

// コンポジションのサイズからアスペクトを自動判定(マルチフォーマット対応の中枢)
type Aspect = 'wide' | 'square' | 'vertical';
const useAspect = (): Aspect => {
  const {width, height} = useVideoConfig();
  const r = width / height;
  return r > 1.2 ? 'wide' : r >= 0.9 ? 'square' : 'vertical';
};

// ---------------------------------------------------------------- telop

// ボード仕様のCMテロップ文字: シルバーグラデーション + 黒縁取り
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
        background:
          'linear-gradient(180deg, #FFFFFF 25%, #DDE1E7 48%, #A8AEB9 62%, #F2F4F7 100%)',
        WebkitBackgroundClip: 'text',
        backgroundClip: 'text',
        WebkitTextFillColor: 'transparent',
      }}
    >
      {text}
    </span>
  </div>
);

const Telop: React.FC<{lines: string[]; accent?: string}> = ({lines}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const aspect = useAspect();
  const s = spring({frame: frame - 6, fps, config: {damping: 200}});
  // 縦・正方形は幅1080に収まるサイズへ(セーフゾーンも広めに)
  const size = aspect === 'wide' ? 78 : 56;
  const insets = useSafeInsets();   // 媒体セーフゾーン（リール下35% 等）を避ける
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

const LiveCut: React.FC<{
  src: string;
  srcVertical?: string; // 縦型ネイティブ素材(スマートクロップで破綻するカット用)
  portraitForSquare?: boolean; // 正方形でも縦ネイティブ素材を使う(重要要素が横に外れるカット)
  rate?: number;
  telop: string[];
  fadeOutAt?: number;
  fadeInFrames?: number;
  anchorX?: number; // 被写体の横位置(%)。縦・正方形クロップの基準
}> = ({src, srcVertical, portraitForSquare = false, rate = 1, telop, fadeOutAt, fadeInFrames = 8, anchorX = 50}) => {
  const frame = useCurrentFrame();
  const aspect = useAspect();
  const usePortrait =
    srcVertical && (aspect === 'vertical' || (aspect === 'square' && portraitForSquare));
  const activeSrc = usePortrait ? srcVertical! : src;
  const fadeIn =
    fadeInFrames > 0
      ? interpolate(frame, [0, fadeInFrames], [0, 1], {
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
        })
      : 1;
  const fadeOut = fadeOutAt
    ? interpolate(frame, [fadeOutAt, fadeOutAt + 7], [1, 0], {
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp',
      })
    : 1;
  // 手持ちカメラ風の微細ドリフト(「完全静止のAI画」を崩す)
  const driftX = Math.sin(frame / 46) * 4 + Math.sin(frame / 13) * 0.8;
  const driftY = Math.cos(frame / 61) * 3 + Math.cos(frame / 17) * 0.6;
  return (
    <AbsoluteFill style={{background: '#000', opacity: fadeIn * fadeOut}}>
      <AbsoluteFill style={{transform: `translate(${driftX}px, ${driftY}px) scale(1.015)`}}>
        <OffthreadVideo
          src={staticFile(activeSrc)}
          playbackRate={rate}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            // 縦・正方形では被写体アンカー基準でクロップ(スマートクロップ)
            objectPosition: aspect === 'wide' ? 'center' : `${anchorX}% 50%`,
            // 全実写カット共通のグレーディング(色調統一)
            filter: 'url(#gradeB) saturate(0.86) contrast(1.04)',
          }}
          muted
        />
      </AbsoluteFill>
      {/* 周辺減光(カメラレンズの癖) */}
      <AbsoluteFill
        style={{
          background:
            'radial-gradient(ellipse 75% 70% at 50% 48%, rgba(0,0,0,0) 55%, rgba(8,10,14,0.24) 100%)',
          pointerEvents: 'none',
        }}
      />
      {/* 動的フィルムグレイン */}
      <AbsoluteFill
        style={{
          backgroundImage: `url(${staticFile('mirai/grain.png')})`,
          backgroundPosition: `${(frame * 97) % 512}px ${(frame * 53) % 512}px`,
          opacity: 0.07,
          mixBlendMode: 'overlay',
          pointerEvents: 'none',
        }}
      />
      <Telop lines={telop} />
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------- カバー(0フレーム目のみ・完全静止)

const CoverFrame: React.FC = () => {
  const aspect = useAspect();

  if (aspect !== 'wide') {
    // 縦・正方形: 上にコピー、下にスマホ2台の縦積みレイアウト
    const isV = aspect === 'vertical';
    return (
      <AbsoluteFill
        style={{
          background: RED,
          overflow: 'hidden',
          alignItems: 'center',
          justifyContent: 'center',
          gap: isV ? 70 : 36,
        }}
      >
        <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
          <div style={{background: '#fff', borderRadius: 14, padding: 5}}>
            <Img
              src={staticFile('mirai/app_icon.png')}
              style={{height: 52, borderRadius: 12, display: 'block'}}
            />
          </div>
          <span
            style={{
              fontFamily: '"Hiragino Maru Gothic ProN", "Hiragino Sans", sans-serif',
              fontWeight: 800,
              fontSize: 44,
              color: '#fff',
              letterSpacing: '0.04em',
            }}
          >
            ミライ工事
          </span>
        </div>

        <div
          style={{
            fontFamily: FONT,
            fontWeight: 900,
            fontSize: isV ? 100 : 82,
            lineHeight: 1.3,
            color: '#fff',
            letterSpacing: '0.02em',
            textAlign: 'center',
          }}
        >
          <div>現場で完結。</div>
          <div>作業時間を</div>
          <div>
            <span style={{color: '#FFC933'}}>40時間</span>短縮!
          </div>
        </div>

        <div style={{display: 'flex', gap: 40, alignItems: 'flex-start'}}>
          <DeviceFrame height={isV ? 640 : 470}>
            <Img
              src={staticFile('mirai/ui2_camera.png')}
              style={{width: '100%', display: 'block'}}
            />
          </DeviceFrame>
          <div style={{marginTop: 22}}>
            <DeviceFrame height={isV ? 640 : 470}>
              <Img
                src={staticFile('mirai/ui2_list_filled.png')}
                style={{width: '100%', display: 'block'}}
              />
            </DeviceFrame>
          </div>
        </div>
      </AbsoluteFill>
    );
  }

  return (
    <AbsoluteFill style={{background: RED, overflow: 'hidden'}}>
      {/* ロゴ(左上・白タイル+白文字ロックアップ) */}
      <div
        style={{
          position: 'absolute',
          top: 44,
          left: 52,
          display: 'flex',
          alignItems: 'center',
          gap: 20,
        }}
      >
        <div
          style={{
            background: '#fff',
            borderRadius: 18,
            padding: 6,
          }}
        >
          <Img
            src={staticFile('mirai/app_icon.png')}
            style={{height: 64, borderRadius: 14, display: 'block'}}
          />
        </div>
        <span
          style={{
            fontFamily: '"Hiragino Maru Gothic ProN", "Hiragino Sans", sans-serif',
            fontWeight: 800,
            fontSize: 52,
            color: '#fff',
            letterSpacing: '0.04em',
          }}
        >
          ミライ工事
        </span>
      </div>

      {/* キャッチコピー(左側) */}
      <div
        style={{
          position: 'absolute',
          left: 90,
          top: 300,
          fontFamily: FONT,
          fontWeight: 900,
          fontSize: 130,
          lineHeight: 1.34,
          color: '#fff',
          letterSpacing: '0.02em',
        }}
      >
        <div>現場で完結。</div>
        <div>作業時間を</div>
        <div>
          <span style={{color: '#FFC933'}}>40時間</span>短縮!
        </div>
      </div>

      {/* スマホ2台(右側) */}
      <div
        style={{
          position: 'absolute',
          right: 70,
          top: 150,
          display: 'flex',
          gap: 52,
          alignItems: 'flex-start',
        }}
      >
        <DeviceFrame height={780}>
          <Img
            src={staticFile('mirai/ui2_camera.png')}
            style={{width: '100%', display: 'block'}}
          />
        </DeviceFrame>
        <div style={{marginTop: 26}}>
          <DeviceFrame height={780}>
            <Img
              src={staticFile('mirai/ui2_list_filled.png')}
              style={{width: '100%', display: 'block'}}
            />
          </DeviceFrame>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------- スプラッシュ(サウンドロゴ用・冒頭2秒)

const Splash: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const aspect = useAspect();
  const splashIconH = aspect === 'wide' ? 200 : 148;
  const splashFontSize = aspect === 'wide' ? 130 : 92;
  // 1打目: アイコンがポンと登場
  const iconS = spring({frame: frame - 4, fps, config: {damping: 12, mass: 0.6, stiffness: 160}});
  // 2打目(「ミライコウジ」のタイミング): テキストが入る
  const textS = spring({frame: frame - 24, fps, config: {damping: 15, mass: 0.7, stiffness: 130}});
  // 赤いリングが広がる
  const ring = interpolate(frame, [4, 40], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });
  const fadeOut = interpolate(frame, [56, 66], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill
      style={{
        background: '#fff',
        justifyContent: 'center',
        alignItems: 'center',
        opacity: fadeOut,
      }}
    >
      {/* 広がる赤リング */}
      <div
        style={{
          position: 'absolute',
          width: 200 + ring * 1500,
          height: 200 + ring * 1500,
          borderRadius: '50%',
          border: `${Math.max(2, 30 * (1 - ring))}px solid rgba(215,0,15,${0.35 * (1 - ring)})`,
        }}
      />
      <div style={{display: 'flex', alignItems: 'center', gap: 36}}>
        <div
          style={{
            opacity: Math.min(1, iconS),
            transform: `scale(${0.4 + Math.min(1, iconS) * 0.6}) rotate(${(1 - Math.min(1, iconS)) * -12}deg)`,
          }}
        >
          <Img
            src={staticFile('mirai/app_icon.png')}
            style={{height: splashIconH, borderRadius: splashIconH * 0.22, display: 'block', boxShadow: '0 24px 60px rgba(215,0,15,0.25)'}}
          />
        </div>
        <div
          style={{
            overflow: 'hidden',
          }}
        >
          <span
            style={{
              display: 'inline-block',
              fontFamily: '"Hiragino Maru Gothic ProN", "Hiragino Sans", sans-serif',
              fontWeight: 800,
              fontSize: splashFontSize,
              color: DARK,
              letterSpacing: '0.05em',
              opacity: Math.min(1, textS),
              transform: `translateX(${(1 - Math.min(1, textS)) * -80}px)`,
            }}
          >
            ミライ工事
          </span>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------- スプラッシュB: コンフェッティ+文字ポップ(ポップ)

const CONFETTI_COLORS = ['#D7000F', '#FFC933', '#22B573', '#3B82F6', '#FF8DA1'];

const SplashB: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const aspect = useAspect();
  const splashIconH = aspect === 'wide' ? 200 : 148;
  const splashFontSize = aspect === 'wide' ? 130 : 92;
  const iconS = spring({frame: frame - 4, fps, config: {damping: 9, mass: 0.7, stiffness: 180}});
  const fadeOut = interpolate(frame, [56, 66], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const chars = 'ミライ工事'.split('');

  return (
    <AbsoluteFill style={{background: '#FFF8F0', justifyContent: 'center', alignItems: 'center', opacity: fadeOut}}>
      {/* コンフェッティ */}
      {[...Array(24)].map((_, i) => {
        const burst = interpolate(frame, [6, 46], [0, 1], {
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
          easing: Easing.out(Easing.cubic),
        });
        const ang = (i / 24) * Math.PI * 2 + (i % 3) * 0.4;
        const dist = burst * (420 + (i % 5) * 160);
        const size = 14 + (i % 4) * 8;
        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: '50%',
              top: '46%',
              width: size,
              height: size * (i % 2 ? 1 : 0.55),
              borderRadius: i % 2 ? '50%' : 3,
              background: CONFETTI_COLORS[i % CONFETTI_COLORS.length],
              opacity: (1 - burst) * 0.9 + 0.1,
              transform: `translate(${Math.cos(ang) * dist}px, ${Math.sin(ang) * dist + burst * burst * 200}px) rotate(${burst * (i % 2 ? 540 : -420)}deg)`,
            }}
          />
        );
      })}
      <div style={{display: 'flex', alignItems: 'center', gap: 36}}>
        <div
          style={{
            opacity: Math.min(1, iconS),
            transform: `scale(${0.3 + Math.min(1.15, iconS) * 0.7}) rotate(${(1 - Math.min(1, iconS)) * 20}deg)`,
          }}
        >
          <Img
            src={staticFile('mirai/app_icon.png')}
            style={{height: splashIconH, borderRadius: splashIconH * 0.22, display: 'block', boxShadow: '0 24px 60px rgba(215,0,15,0.3)'}}
          />
        </div>
        <div style={{display: 'flex'}}>
          {chars.map((c, i) => {
            const s = spring({
              frame: frame - 22 - i * 4,
              fps,
              config: {damping: 8, mass: 0.5, stiffness: 220},
            });
            return (
              <span
                key={i}
                style={{
                  display: 'inline-block',
                  fontFamily: '"Hiragino Maru Gothic ProN", "Hiragino Sans", sans-serif',
                  fontWeight: 800,
                  fontSize: splashFontSize,
                  color: DARK,
                  opacity: Math.min(1, s),
                  transform: `translateY(${(1 - Math.min(1, s)) * 90}px) rotate(${(1 - Math.min(1, s)) * (i % 2 ? 14 : -14)}deg)`,
                }}
              >
                {c}
              </span>
            );
          })}
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------- スプラッシュC: 赤バブル+ワブル(エレクトロポップ)

const SplashC: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const aspect = useAspect();
  const splashIconH = aspect === 'wide' ? 200 : 148;
  const splashFontSize = aspect === 'wide' ? 130 : 92;
  // 白い円が中央からバブルのように膨らむ
  const bubble = spring({frame: frame - 2, fps, config: {damping: 13, mass: 0.9, stiffness: 90}});
  const iconS = spring({frame: frame - 8, fps, config: {damping: 7, mass: 0.6, stiffness: 200}});
  const wobble = frame > 8 ? Math.sin(frame / 2.4) * Math.max(0, 8 - (frame - 8) * 0.35) : 0;
  const fadeOut = interpolate(frame, [56, 66], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const chars = 'ミライ工事'.split('');

  return (
    <AbsoluteFill style={{background: RED, justifyContent: 'center', alignItems: 'center', opacity: fadeOut}}>
      <div
        style={{
          position: 'absolute',
          width: 1400 * Math.min(1.06, bubble),
          height: 1400 * Math.min(1.06, bubble),
          borderRadius: '50%',
          background: '#fff',
        }}
      />
      <div style={{position: 'relative', display: 'flex', alignItems: 'center', gap: 36}}>
        <div
          style={{
            opacity: Math.min(1, iconS),
            transform: `scale(${0.3 + Math.min(1.2, iconS) * 0.7}) rotate(${wobble}deg)`,
          }}
        >
          <Img
            src={staticFile('mirai/app_icon.png')}
            style={{height: splashIconH, borderRadius: splashIconH * 0.22, display: 'block', boxShadow: '0 24px 60px rgba(215,0,15,0.35)'}}
          />
        </div>
        <div style={{display: 'flex'}}>
          {chars.map((c, i) => {
            const s = spring({
              frame: frame - 20 - i * 3,
              fps,
              config: {damping: 9, mass: 0.5, stiffness: 240},
            });
            return (
              <span
                key={i}
                style={{
                  display: 'inline-block',
                  fontFamily: '"Hiragino Maru Gothic ProN", "Hiragino Sans", sans-serif',
                  fontWeight: 800,
                  fontSize: splashFontSize,
                  color: RED,
                  opacity: Math.min(1, s),
                  transform: `scale(${0.2 + Math.min(1.1, s) * 0.8})`,
                }}
              >
                {c}
              </span>
            );
          })}
        </div>
      </div>
    </AbsoluteFill>
  );
};

// イントロ試作プレビュー(サウンドロゴ+スプラッシュのみ)
export const IntroPreview: React.FC<{variant: string}> = ({variant}) => {
  const S = variant === 'B' ? SplashB : SplashC;
  return (
    <AbsoluteFill style={{background: '#000', fontFamily: FONT}}>
      <S />
      <Sequence from={0} durationInFrames={90}>
        <Audio src={staticFile(`mirai/soundlogo_${variant}.wav`)} volume={0.9} />
      </Sequence>
      <Sequence from={24} durationInFrames={35}>
        <Audio src={staticFile('mirai/mirai_call.wav')} volume={1} />
      </Sequence>
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------- ウォーターマーク(アスペクト別セーフゾーン対応)

const WatermarkLogo: React.FC = () => {
  const aspect = useAspect();
  // 縦型: リール/ショートの上部UI(0〜約130px)を避ける
  const insets = useSafeInsets();
  const top = Math.max(aspect === 'vertical' ? 150 : 36, insets.top + 16);
  const iconH = aspect === 'wide' ? 58 : 48;
  const fontSize = aspect === 'wide' ? 46 : 38;
  return (
    <div
      style={{
        position: 'absolute',
        top,
        left: aspect === 'wide' ? 44 : 40,
        display: 'flex',
        alignItems: 'center',
        gap: 14,
        filter: 'drop-shadow(0 3px 10px rgba(0,0,0,0.55))',
      }}
    >
      <Img
        src={staticFile('mirai/app_icon.png')}
        style={{height: iconH, borderRadius: iconH * 0.24, display: 'block'}}
      />
      <span
        style={{
          fontFamily: '"Hiragino Maru Gothic ProN", "Hiragino Sans", sans-serif',
          fontWeight: 800,
          fontSize,
          color: '#fff',
          letterSpacing: '0.04em',
        }}
      >
        ミライ工事
      </span>
    </div>
  );
};

// ---------------------------------------------------------------- 台帳ミニチュア(送信・受信で共用)

const MiniLedgerDoc: React.FC = () => (
  <div
    style={{
      width: 168,
      height: 224,
      background: '#fff',
      borderRadius: 6,
      padding: 14,
    }}
  >
    <div
      style={{
        fontFamily: FONT,
        fontSize: 15,
        fontWeight: 800,
        color: DARK,
        borderBottom: `2px solid ${DARK}`,
        paddingBottom: 5,
        marginBottom: 9,
        letterSpacing: '0.06em',
      }}
    >
      工事写真台帳
    </div>
    <Img
      src={staticFile('mirai/site_photo1.jpg')}
      style={{width: '100%', height: 62, objectFit: 'cover', marginBottom: 8}}
    />
    {[0, 1, 2].map((i) => (
      <div
        key={i}
        style={{width: `${92 - i * 16}%`, height: 5, background: '#C2C7CF', marginBottom: 5}}
      />
    ))}
    <Img
      src={staticFile('mirai/site_photo2.jpg')}
      style={{width: '100%', height: 52, objectFit: 'cover', marginTop: 4}}
    />
  </div>
);

// ---------------------------------------------------------------- S5: 送信アニメーション

const SendFx: React.FC = () => {
  const frame = useCurrentFrame();
  const aspect = useAspect();
  // クロップ後のスマホの画面内位置に合わせた発射位置
  // (16:9でスマホは素材の49%地点 → 縦クロップ(anchor40)では画面の約76%、正方形では約66%)
  const startX = aspect === 'wide' ? 49 : aspect === 'vertical' ? 76 : 66;
  // 届く側(DeliveryFx)と同じスタイル: ふわっとした非対称アーチ + ゆらゆら + 残像トレイル
  const flight = (f: number) =>
    interpolate(f, [40, 72], [0, 1], {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
      easing: Easing.inOut(Easing.sin),
    });
  const pose = (tt: number) => {
    const x = interpolate(tt, [0, 1], [startX, 112]);
    // スマホからふわっと浮き上がり、漂いながら右上へ抜けていく
    const arc = Math.pow(Math.sin(tt * Math.PI), 0.7);
    const y = 54 - tt * 62 - arc * 10;
    const rot = -4 + tt * 14 + Math.sin(tt * Math.PI * 2.4) * 6;
    const scale = 0.5 - tt * 0.08;
    return {x, y, rot, scale};
  };
  const t = flight(frame);
  if (frame < 40 || t >= 1) return null;
  const main = pose(t);
  return (
    <AbsoluteFill style={{pointerEvents: 'none'}}>
      {/* 残像トレイル */}
      {[10, 5].map((d, i) => {
        const tt = flight(frame - d);
        if (frame - d < 40 || tt >= 1) return null;
        const g = pose(tt);
        return (
          <div
            key={d}
            style={{
              position: 'absolute',
              left: `${g.x}%`,
              top: `${g.y}%`,
              transform: `scale(${g.scale})`,
              opacity: i === 0 ? 0.1 : 0.22,
              filter: 'blur(3px)',
            }}
          >
            <MiniLedgerDoc />
          </div>
        );
      })}
      <div
        style={{
          position: 'absolute',
          left: `${main.x}%`,
          top: `${main.y}%`,
          transform: `scale(${main.scale}) rotate(${main.rot}deg)`,
          opacity: interpolate(t, [0, 0.12, 1], [0, 1, 1]),
          filter: 'drop-shadow(0 18px 34px rgba(0,0,0,0.45))',
        }}
      >
        <MiniLedgerDoc />
      </div>
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------- S5B: 届いたアニメーション

const DELIVERY_LAND = 34;

const DeliveryFx: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const aspect = useAspect();
  const isV = aspect === 'vertical';
  // 通知は書類の着地点(モニターの真上)に出す。顔には被せない
  const popLeft = aspect === 'wide' ? '46%' : isV ? '42%' : '52%';
  const popTop = aspect === 'wide' ? '21%' : isV ? '26%' : '12%';
  const popFs = aspect === 'wide' ? 34 : 28;
  const popIcon = aspect === 'wide' ? 46 : 40;
  // 縦ネイティブ素材ではモニターが右側・やや下に来る
  const targetX = isV ? 72 : 68;
  const sparkleCX = isV ? 74 : 70;
  const sparkleCY = isV ? 40 : 30;

  // ふわっとした非対称アーチ: 高めに舞い上がり、紙が漂うようにゆっくり降りてくる
  const flight = (f: number) =>
    interpolate(f, [2, DELIVERY_LAND], [0, 1], {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
      easing: Easing.inOut(Easing.sin),
    });
  const pose = (tt: number) => {
    const x = interpolate(tt, [0, 1], [112, targetX]);
    // 前半で大きく上がり、後半はゆっくり沈む(sinの累乗で非対称に)
    const arc = Math.pow(Math.sin(tt * Math.PI), 0.7);
    const y = (isV ? 48 : 44) - arc * (isV ? 26 : 32) - tt * (isV ? 6 : 8);
    // 紙が風に揺れるような首振り
    const rot = 10 - tt * 16 + Math.sin(tt * Math.PI * 2.4) * 6;
    const scale = 1.02 - tt * 0.56;
    return {x, y, rot, scale};
  };

  const t = flight(frame);
  const docVisible = frame >= 2 && t < 1;
  // 着地: モニターが淡く光る + スパークル
  const glow = spring({frame: frame - DELIVERY_LAND, fps, config: {damping: 14, mass: 0.7, stiffness: 100}});
  const glowOpacity =
    frame >= DELIVERY_LAND
      ? Math.min(1, glow) *
        interpolate(frame, [DELIVERY_LAND, DELIVERY_LAND + 14, 80], [0.55, 0.3, 0.18], {
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
        })
      : 0;
  const sparkle = spring({frame: frame - DELIVERY_LAND, fps, config: {damping: 16, mass: 0.6, stiffness: 120}});
  // 通知ポップ
  const pop = spring({frame: frame - (DELIVERY_LAND + 3), fps, config: {damping: 13, mass: 0.6, stiffness: 150}});
  const popVisible = frame >= DELIVERY_LAND + 3;

  const main = pose(t);

  return (
    <AbsoluteFill style={{pointerEvents: 'none'}}>
      {/* 残像トレイル(軌跡をふわっと見せる) */}
      {[10, 5].map((d, i) => {
        const tt = flight(frame - d);
        if (frame - d < 2 || tt >= 1 || !docVisible) return null;
        const g = pose(tt);
        return (
          <div
            key={d}
            style={{
              position: 'absolute',
              left: `${g.x}%`,
              top: `${g.y}%`,
              transform: `scale(${g.scale})`,
              opacity: i === 0 ? 0.1 : 0.22,
              filter: 'blur(3px)',
            }}
          >
            <MiniLedgerDoc />
          </div>
        );
      })}

      {docVisible && (
        <div
          style={{
            position: 'absolute',
            left: `${main.x}%`,
            top: `${main.y}%`,
            transform: `scale(${main.scale}) rotate(${main.rot}deg)`,
            filter: 'drop-shadow(0 18px 34px rgba(0,0,0,0.45))',
          }}
        >
          {/* 工事写真台帳のミニチュア(送信シーンと同一の紙面) */}
          <MiniLedgerDoc />
        </div>
      )}

      {/* 着地スパークル(モニターに吸い込まれた合図) */}
      {frame >= DELIVERY_LAND &&
        [...Array(6)].map((_, i) => {
          const s = Math.min(1, sparkle);
          const ang = (i / 6) * Math.PI * 2 - 0.5;
          return (
            <div
              key={i}
              style={{
                position: 'absolute',
                left: `calc(${sparkleCX}% + ${Math.cos(ang) * s * 110}px)`,
                top: `calc(${sparkleCY}% + ${Math.sin(ang) * s * 90}px)`,
                width: i % 2 ? 10 : 14,
                height: i % 2 ? 10 : 14,
                borderRadius: '50%',
                background: i % 3 === 0 ? '#FFD75E' : '#fff',
                opacity: Math.max(0, 1 - s) * 0.9,
                boxShadow: '0 0 12px rgba(255,255,255,0.8)',
              }}
            />
          );
        })}

      {/* モニターの受信グロー */}
      <div
        style={{
          position: 'absolute',
          left: isV ? '50%' : '52%',
          top: isV ? '25%' : '0%',
          width: isV ? '55%' : '48%',
          height: isV ? '55%' : '75%',
          background:
            'radial-gradient(ellipse 55% 45% at 55% 45%, rgba(190,215,255,0.9), rgba(190,215,255,0) 70%)',
          opacity: glowOpacity,
          mixBlendMode: 'screen',
        }}
      />

      {popVisible && (
        <div
          style={{
            position: 'absolute',
            left: popLeft,
            top: popTop,
            opacity: Math.min(1, pop),
            transform: `translateY(${(1 - Math.min(1, pop)) * 30}px) scale(${0.8 + Math.min(1, pop) * 0.2})`,
            background: 'rgba(255,255,255,0.97)',
            borderRadius: 18,
            padding: `${popFs * 0.55}px ${popFs * 0.9}px`,
            display: 'flex',
            alignItems: 'center',
            gap: 16,
            boxShadow: '0 20px 50px rgba(0,0,0,0.35)',
          }}
        >
          <div
            style={{
              width: popIcon,
              height: popIcon,
              borderRadius: '50%',
              background: '#22B573',
              color: '#fff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: popIcon * 0.62,
              fontWeight: 800,
              fontFamily: FONT,
            }}
          >
            ✓
          </div>
          <div style={{fontFamily: FONT, fontSize: popFs, fontWeight: 800, color: DARK}}>
            工事台帳が届きました
          </div>
        </div>
      )}
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------- S2B: 月40時間

// 舞う書類(白い帳票シート)
const FlyingPaper: React.FC<{seed: number}> = ({seed}) => {
  const frame = useCurrentFrame();
  const t = (frame + seed * 13) / 65;
  const x = interpolate(t, [0, 1.6], [110, -30]) + Math.sin(seed * 7) * 12;
  const y = 20 + ((seed * 37) % 55) + Math.sin(t * 5 + seed) * 6;
  const rot = -18 + ((seed * 53) % 40) + Math.sin(t * 4 + seed * 2) * 8;
  const size = 150 + ((seed * 31) % 110);
  return (
    <div
      style={{
        position: 'absolute',
        left: `${x}%`,
        top: `${y}%`,
        width: size,
        height: size * 1.35,
        background: '#F2F3F5',
        borderRadius: 4,
        transform: `rotate(${rot}deg)`,
        opacity: 0.85,
        boxShadow: '0 16px 34px rgba(0,0,0,0.5)',
        padding: size * 0.09,
      }}
    >
      {/* 帳票らしい罫線と写真枠 */}
      <div style={{width: '60%', height: 8, background: '#B9BEC7', marginBottom: 8}} />
      <div style={{width: '100%', height: size * 0.5, background: '#CDD2D9', marginBottom: 8}} />
      {[0, 1, 2].map((i) => (
        <div key={i} style={{width: `${90 - i * 15}%`, height: 6, background: '#C6CBD3', marginBottom: 6}} />
      ))}
    </div>
  );
};

const StatCut: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const enter = spring({frame: frame - 8, fps, config: {damping: 12, mass: 0.6, stiffness: 150}});
  const capS = spring({frame: frame - 2, fps, config: {damping: 200}});
  // カウントアップ: 0 → 40
  const countT = interpolate(frame, [10, 44], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });
  const num = Math.round(40 * countT);
  // カウント完了の瞬間に数字がパンチ+赤グロー
  const landS = spring({frame: frame - 44, fps, config: {damping: 10, mass: 0.5, stiffness: 200}});
  const landPunch = frame >= 44 ? Math.sin(Math.min(1, landS) * Math.PI) : 0;
  const landGlow = frame >= 44 ? Math.max(0, 1 - (frame - 44) / 20) : 0;
  const noteS = spring({frame: frame - 40, fps, config: {damping: 200}});
  const fadeIn = interpolate(frame, [0, 8], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const fadeOut = interpolate(frame, [57, 65], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{background: '#000', opacity: fadeIn * fadeOut}}>
      {/* 実写背景: 夜のオフィスを舞い落ちる帳票(AI生成映像) */}
      <OffthreadVideo
        src={staticFile('mirai/papers_veo.mp4')}
        playbackRate={0.77}
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          filter: 'url(#gradeB) saturate(0.86) contrast(1.04)',
        }}
        muted
      />
      {/* テキストの視認性のための軽いビネット */}
      <AbsoluteFill
        style={{
          background:
            'radial-gradient(ellipse 65% 55% at 50% 50%, rgba(0,0,0,0.35), rgba(0,0,0,0) 75%)',
        }}
      />

      {/* テロップ(ボード文言・メタリック) */}
      <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center'}}>
        <div style={{textAlign: 'center', opacity: Math.min(1, capS)}}>
          <div style={{transform: `translateY(${(1 - capS) * 30}px)`}}>
            <MetalText text="その作業に、" size={84} />
          </div>
          <div
            style={{
              marginTop: 6,
              opacity: Math.min(1, enter),
              transform: `scale(${0.7 + Math.min(1, enter) * 0.3 + landPunch * 0.14})`,
              display: 'flex',
              alignItems: 'baseline',
              justifyContent: 'center',
              gap: 8,
              filter: landGlow > 0 ? `drop-shadow(0 0 ${40 * landGlow}px rgba(215,0,15,${0.85 * landGlow}))` : undefined,
            }}
          >
            <MetalText text="月" size={120} />
            <MetalText text={`${num}`} size={260} />
            <MetalText text="時間。" size={120} />
          </div>
          <div
            style={{
              marginTop: 18,
              fontFamily: FONT,
              fontSize: 26,
              fontWeight: 600,
              color: 'rgba(255,255,255,0.55)',
              letterSpacing: '0.1em',
              opacity: Math.min(1, noteS),
            }}
          >
            ※ 自社調べ
          </div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------- S3B: auto ledger

// 透過形状に追従する影(矩形boxShadowだと白フチ/四角い影が出る)
const PhoneImg: React.FC<{src: string; height: number}> = ({src, height}) => (
  <Img
    src={staticFile(src)}
    style={{height, display: 'block', filter: 'drop-shadow(0 40px 60px rgba(0,0,0,0.35))'}}
  />
);

// カメラ画面から台帳へ写真が飛んで整理されていくカード
const FLY_DELAYS = [26, 40, 54];
const FLY_DUR = 24;

const FlyingPhoto: React.FC<{src: string; delay: number}> = ({src, delay}) => {
  const frame = useCurrentFrame();
  const aspect = useAspect();
  const range = aspect === 'wide' ? 330 : 170;
  const t = interpolate(frame, [delay, delay + FLY_DUR], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.inOut(Easing.cubic),
  });
  if (frame < delay || t >= 1) return null;
  // 左のスマホから右のスマホへ、放物線を描いて飛ぶ
  const x = interpolate(t, [0, 1], [-range, range]);
  const y = -Math.sin(t * Math.PI) * 240;
  const rot = interpolate(t, [0, 1], [-14, 10]);
  const scale = 0.85 + 0.25 * Math.sin(t * Math.PI);
  return (
    <div
      style={{
        position: 'absolute',
        left: '50%',
        top: '42%',
        transform: `translate(-50%, -50%) translate(${x}px, ${y}px) rotate(${rot}deg) scale(${scale})`,
        padding: 10,
        background: '#fff',
        boxShadow: '0 20px 40px rgba(0,0,0,0.3)',
        opacity: interpolate(t, [0, 0.08, 0.9, 1], [0, 1, 1, 0]),
      }}
    >
      <Img src={staticFile(src)} style={{width: 220, display: 'block'}} />
    </div>
  );
};

// 台帳の行の位置(スクリーンショット内の割合・実測値)
const LEDGER_ROWS = [
  {src: 'mirai/row2_1.png', top: 18.68, h: 19.7},
  {src: 'mirai/row2_2.png', top: 41.05, h: 19.29},
  {src: 'mirai/row2_3.png', top: 63.01, h: 18.68},
];

// コード描画のスマホデバイス枠(ベゼルなしUIスクショを中に入れる)
const SCREEN_AR = 1125 / 2436;

const DeviceFrame: React.FC<{height: number; children: React.ReactNode}> = ({
  height,
  children,
}) => {
  const pad = Math.round(height * 0.017);
  const btn = (side: 'left' | 'right', top: string, h: number) => (
    <div
      style={{
        position: 'absolute',
        [side]: -4,
        top,
        width: 5,
        height: h,
        borderRadius: 3,
        background: '#2b2d32',
      }}
    />
  );
  return (
    <div
      style={{
        position: 'relative',
        padding: pad,
        background: 'linear-gradient(145deg, #43464d, #131418)',
        borderRadius: height * 0.088,
        boxShadow:
          '0 40px 70px rgba(0,0,0,0.4), inset 0 0 0 2px rgba(255,255,255,0.09)',
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

const AutoLedger: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const aspect = useAspect();
  const ledgerPhoneH = aspect === 'wide' ? 690 : aspect === 'square' ? 470 : 560;
  const ledgerGap = aspect === 'wide' ? 240 : 70;

  // 遠近感のある登場(スライドではなく、奥からの起き上がり)
  const enter1 = spring({frame, fps, config: {damping: 15, mass: 0.9, stiffness: 90}});
  const enter2 = spring({frame: frame - 8, fps, config: {damping: 15, mass: 0.9, stiffness: 90}});
  // シャッター: 画面全体のフラッシュ + 画面が一瞬パンチズーム
  const flash = interpolate(frame, [22, 26, 36], [0, 0.95, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const punch = 1 + interpolate(frame, [22, 25, 38], [0, 0.045, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  // 写真カードの着地タイミング(FlyingPhotoと同期)
  const lands = FLY_DELAYS.map((d) => d + FLY_DUR);
  const landBounce = lands.reduce((acc, land) => {
    const b = spring({frame: frame - land, fps, config: {damping: 9, mass: 0.4, stiffness: 220}});
    return acc + (frame >= land ? Math.sin(Math.min(1, b) * Math.PI) * 0.03 : 0);
  }, 0);
  // 全行そろった瞬間: 台帳の後ろに赤いグローがふわっと広がる
  const doneGlow = interpolate(frame, [lands[2], lands[2] + 14], [0, 0.35], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const float = Math.sin(frame / 22) * 5;

  return (
    <AbsoluteFill style={{background: '#F1F2F5', justifyContent: 'center', alignItems: 'center'}}>
      {/* 奥行きを出す淡いグラデーション */}
      <AbsoluteFill
        style={{
          background:
            'radial-gradient(ellipse 70% 55% at 50% 42%, rgba(215,0,15,0.06), rgba(215,0,15,0) 70%)',
        }}
      />
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: ledgerGap,
          marginBottom: aspect === 'wide' ? 80 : 40,
          transform: `scale(${punch})`,
          perspective: 1600,
        }}
      >
        <div
          style={{
            opacity: Math.min(1, enter1),
            transform: `perspective(1600px) rotateY(${(1 - enter1) * -35 + 6}deg) scale(${0.8 + enter1 * 0.2}) translateY(${float}px)`,
          }}
        >
          <DeviceFrame height={ledgerPhoneH}>
            <Img
              src={staticFile('mirai/ui2_camera.png')}
              style={{width: '100%', display: 'block'}}
            />
            {/* シャッターフラッシュ: 画面内のみ(枠はコード描画なので正確) */}
            <div
              style={{
                position: 'absolute',
                inset: 0,
                background: '#fff',
                opacity: flash,
                pointerEvents: 'none',
              }}
            />
          </DeviceFrame>
        </div>

        <div
          style={{
            position: 'relative',
            opacity: Math.min(1, enter2),
            transform: `perspective(1600px) rotateY(${(1 - enter2) * 35 - 6}deg) scale(${0.8 + enter2 * 0.2 + landBounce}) translateY(${-float}px)`,
          }}
        >
          {/* 完成グロー */}
          <div
            style={{
              position: 'absolute',
              inset: -60,
              background: `radial-gradient(ellipse, rgba(215,0,15,${doneGlow}), rgba(215,0,15,0) 70%)`,
            }}
          />
          <DeviceFrame height={ledgerPhoneH}>
            {/* 空状態の一覧UI(実素材)が待機 */}
            <Img
              src={staticFile('mirai/ui2_list_empty.png')}
              style={{width: '100%', display: 'block'}}
            />
            {/* 写真の着地と同時に、行が実UIパーツのままふわっと入る */}
            {LEDGER_ROWS.map((row, i) => {
              const pop = spring({
                frame: frame - lands[i],
                fps,
                config: {damping: 14, mass: 0.7, stiffness: 120},
              });
              const visible = frame >= lands[i];
              if (!visible) return null;
              return (
                <div
                  key={row.src}
                  style={{
                    position: 'absolute',
                    left: 0,
                    top: `${row.top}%`,
                    width: '100%',
                    transform: `scale(${0.75 + Math.min(1, pop) * 0.25})`,
                    opacity: Math.min(1, pop * 1.4),
                  }}
                >
                  <Img src={staticFile(row.src)} style={{width: '100%', display: 'block'}} />
                </div>
              );
            })}
            {/* 全行そろったら、実物の完成スクショへクロスフェード(最終状態を実UIと一致させる) */}
            <Img
              src={staticFile('mirai/ui2_list_filled.png')}
              style={{
                position: 'absolute',
                inset: 0,
                width: '100%',
                display: 'block',
                opacity: interpolate(frame, [lands[2] + 6, lands[2] + 18], [0, 1], {
                  extrapolateLeft: 'clamp',
                  extrapolateRight: 'clamp',
                }),
              }}
            />
          </DeviceFrame>
        </div>
      </div>

      {/* 撮った写真が台帳へ飛んで自動整理される */}
      <FlyingPhoto src="mirai/fly_photo1.jpg" delay={FLY_DELAYS[0]} />
      <FlyingPhoto src="mirai/fly_photo2.jpg" delay={FLY_DELAYS[1]} />
      <FlyingPhoto src="mirai/fly_photo3.jpg" delay={FLY_DELAYS[2]} />

      <Telop lines={['スマホで撮るだけ。台帳が自動作成']} />
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------- S4: PDF

// k: A4シートの幅に対する縮尺(基準幅660px = k1.0)
const PdfRow: React.FC<{photo: string; fields: string[][]; delay: number; k: number}> = ({
  photo,
  fields,
  delay,
  k,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const s = spring({frame: frame - delay, fps, config: {damping: 17, mass: 0.7, stiffness: 110}});
  const blur = interpolate(frame, [delay, delay + 14], [10, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  return (
    <div
      style={{
        display: 'flex',
        gap: 22 * k,
        opacity: Math.min(1, s),
        transform: `translateY(${(1 - s) * 60}px) scale(${0.96 + Math.min(1, s) * 0.04})`,
        filter: `blur(${blur}px)`,
      }}
    >
      <Img
        src={staticFile(photo)}
        style={{width: 236 * k, height: 168 * k, objectFit: 'cover', border: '2px solid #8b8b8b'}}
      />
      <table
        style={{
          borderCollapse: 'collapse',
          fontFamily: FONT,
          fontSize: 17.5 * k,
          color: DARK,
          height: 168 * k,
        }}
      >
        <tbody>
          {fields.map(([kk, v]) => (
            <tr key={kk}>
              <td
                style={{
                  border: '2px solid #8b8b8b',
                  background: '#EFEFEF',
                  padding: `${4 * k}px ${12 * k}px`,
                  fontWeight: 700,
                  width: 96 * k,
                }}
              >
                {kk}
              </td>
              <td style={{border: '2px solid #8b8b8b', padding: `${4 * k}px ${12 * k}px`, width: 220 * k}}>
                {v}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

const PdfScene: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const aspect = useAspect();
  const sheet = spring({frame, fps, config: {damping: 18, mass: 0.9, stiffness: 90}});
  // スタンプ: 静かに「とん」と押される(柔らかいばね)
  const stamp = spring({frame: frame - 60, fps, config: {damping: 16, mass: 0.7, stiffness: 110}});

  // A4縦比率(1:√2)のシート。フォーマットごとに画面に収まる幅を選ぶ
  const sheetW = aspect === 'wide' ? 660 : aspect === 'vertical' ? 810 : 620;
  const sheetH = Math.round(sheetW * 1.414);
  const k = sheetW / 660;

  const commonFields = (kind: string, point: string): string[][] => [
    ['工事名', '未来駅前広場改修工事'],
    ['工種', kind],
    ['測点', point],
    ['撮影日', '2026年8月17日'],
  ];

  return (
    <AbsoluteFill style={{background: '#E8EAED', justifyContent: 'center', alignItems: 'center'}}>
      <div
        style={{
          position: 'relative',
          width: sheetW,
          height: sheetH,
          background: '#fff',
          boxShadow: '0 50px 100px rgba(0,0,0,0.25)',
          padding: `${36 * k}px ${44 * k}px`,
          opacity: Math.min(1, sheet),
          transform: `translateY(${(1 - sheet) * 150}px) rotate(${(1 - sheet) * -2}deg)`,
        }}
      >
        <div
          style={{
            fontFamily: FONT,
            fontSize: 30 * k,
            fontWeight: 800,
            color: DARK,
            borderBottom: `3px solid ${DARK}`,
            paddingBottom: 12 * k,
            marginBottom: 26 * k,
            letterSpacing: '0.1em',
          }}
        >
          工事写真台帳
          <span style={{fontSize: 18 * k, fontWeight: 600, float: 'right', marginTop: 10 * k}}>
            未来駅前広場改修工事
          </span>
        </div>
        <div style={{display: 'flex', flexDirection: 'column', gap: 26 * k}}>
          <PdfRow photo="mirai/site_photo1.jpg" fields={commonFields('鉄筋工事', 'RG 1')} delay={14} k={k} />
          <PdfRow photo="mirai/site_photo2.jpg" fields={commonFields('外壁工', '2F A')} delay={26} k={k} />
          <PdfRow photo="mirai/site_photo3.jpg" fields={commonFields('外壁工', '3F A')} delay={38} k={k} />
        </div>

        <div
          style={{
            position: 'absolute',
            right: 44 * k,
            bottom: 150 * k,
            opacity: Math.min(1, stamp),
            transform: `scale(${1.45 - Math.min(1, stamp) * 0.45}) rotate(${-13 + Math.min(1, stamp) * 5}deg)`,
            border: `${6 * k}px solid ${RED}`,
            borderRadius: 16 * k,
            padding: `${10 * k}px ${26 * k}px`,
            fontFamily: FONT,
            fontSize: 42 * k,
            fontWeight: 800,
            color: RED,
            background: 'rgba(255,255,255,0.9)',
          }}
        >
          PDF完成!
        </div>
      </div>
      <Telop lines={['その場で、PDF完成。']} />
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------- S6: CTA

const Cta: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const s = (d: number) =>
    spring({frame: frame - d, fps, config: {damping: 16, mass: 0.7, stiffness: 110}});
  const logoS = s(0);
  const searchS = s(14);
  const btnS = s(26);
  const glow = 18 + 10 * Math.sin(frame / 5);
  // 媒体セーフゾーン（リール 上14%/下35% 等）の内側に CTA を配置し、開示テロップとも重ねない
  const insets = useSafeInsets();

  return (
    <AbsoluteFill
      style={{
        background: '#fff',
        justifyContent: 'center',
        alignItems: 'center',
        paddingTop: insets.top,
        paddingBottom: insets.bottom + 60,
      }}
    >
      <div
        style={{
          position: 'relative',
          opacity: Math.min(1, logoS),
          transform: `scale(${0.85 + Math.min(1, logoS) * 0.15})`,
        }}
      >
        <Img src={staticFile('mirai/logo.png')} style={{height: 170}} />
        {/* 実績バッジ: 累計DL数(円形・ロゴ右上) */}
        <div
          style={{
            position: 'absolute',
            right: -210,
            top: -60,
            width: 190,
            height: 190,
            borderRadius: '50%',
            background: RED,
            color: '#fff',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            fontFamily: FONT,
            fontWeight: 800,
            transform: `rotate(8deg) scale(${0.9 + 0.1 * Math.sin(frame / 9)})`,
            boxShadow: '0 12px 30px rgba(215,0,15,0.35)',
          }}
        >
          <div style={{fontSize: 26, letterSpacing: '0.05em'}}>累計</div>
          <div style={{fontSize: 44, lineHeight: 1.1}}>50万DL</div>
          <div style={{fontSize: 30}}>突破!</div>
        </div>
      </div>

      <div
        style={{
          marginTop: 70,
          opacity: Math.min(1, searchS),
          transform: `translateY(${(1 - searchS) * 30}px)`,
          display: 'flex',
          alignItems: 'center',
          gap: 24,
          border: `4px solid ${DARK}`,
          borderRadius: 60,
          padding: '26px 50px',
          fontFamily: FONT,
          fontSize: 48,
          fontWeight: 700,
          color: DARK,
        }}
      >
        <span style={{fontSize: 44}}>🔍</span>
        <span style={{minWidth: 380, display: 'inline-block'}}>
          {'ミライ工事写真'.slice(0, Math.max(0, Math.floor((frame - 20) / 3)))}
          {frame >= 20 && frame < 45 && Math.floor(frame / 4) % 2 === 0 && (
            <span style={{color: RED}}>|</span>
          )}
        </span>
        <span
          style={{
            background: DARK,
            color: '#fff',
            borderRadius: 40,
            padding: '10px 34px',
            fontSize: 36,
          }}
        >
          検索
        </span>
      </div>

      {/* 実績バッジ: プロジェクト件数(ピル型) */}
      <div
        style={{
          marginTop: 44,
          opacity: Math.min(1, searchS),
          transform: `translateY(${(1 - searchS) * 24}px)`,
          border: `3px solid ${RED}`,
          color: RED,
          borderRadius: 40,
          padding: '14px 44px',
          fontFamily: FONT,
          fontSize: 34,
          fontWeight: 800,
          letterSpacing: '0.06em',
          background: 'rgba(215,0,15,0.05)',
        }}
      >
        プロジェクト300万件突破
      </div>

      <div
        style={{
          position: 'relative',
          overflow: 'hidden',
          marginTop: 44,
          opacity: Math.min(1, btnS),
          transform: `scale(${0.9 + Math.min(1, btnS) * 0.1})`,
          background: RED,
          color: '#fff',
          fontFamily: FONT,
          fontSize: 46,
          fontWeight: 800,
          borderRadius: 24,
          padding: '30px 80px',
          letterSpacing: '0.08em',
          boxShadow: `0 0 ${glow}px rgba(215,0,15,0.55)`,
        }}
      >
        今すぐ 無料ダウンロード
        {/* 光沢スイープ */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            bottom: 0,
            width: 140,
            left: `${interpolate(frame % 75, [40, 70], [-25, 115], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            })}%`,
            background:
              'linear-gradient(105deg, rgba(255,255,255,0) 0%, rgba(255,255,255,0.45) 50%, rgba(255,255,255,0) 100%)',
            transform: 'skewX(-18deg)',
          }}
        />
      </div>

      <div
        style={{
          marginTop: 44,
          opacity: Math.min(1, btnS) * 0.75,
          fontFamily: FONT,
          fontSize: 28,
          color: '#666',
          letterSpacing: '0.08em',
        }}
      >
        App Store / Google Play 対応 ・ 現場から、そのまま提出。
      </div>
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------- root

// 前半: 悩みパート(沈んだピアノ)。「ミライ工事写真。」の瞬間(S3A頭)で消える
const bgmProblemVolume = (f: number) =>
  interpolate(f, [0, 20, S3A_FROM - 20, S3A_FROM], [0, 0.26, 0.26, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

// 後半: 解決パート(明るいコーポレートポップ)。転換点から立ち上がる
const bgmSolutionVolume = (f: number) =>
  interpolate(f, [0, 25, 900 - S3A_FROM - 50, 900 - S3A_FROM], [0, 0.32, 0.32, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

const MiraiCMInner: React.FC<{splashVariant?: 'A' | 'B' | 'C'}> = ({
  splashVariant = 'A',
}) => {
  const SplashComp = splashVariant === 'B' ? SplashB : splashVariant === 'C' ? SplashC : Splash;
  const soundlogoSrc =
    splashVariant === 'A' ? 'mirai/soundlogo_gen.wav' : `mirai/soundlogo_${splashVariant}.wav`;
  // NA6は客先シーン後半から先行再生(音先行のJカット)
  const naStarts = [S1.from, S2.from, S3A.from, S4.from, S5.from, 765];
  return (
    <AbsoluteFill style={{background: '#000', fontFamily: FONT}}>
      {/* グレードB(放送用クール)のトーンカーブ: 影が青緑に浮き、ハイライトが緩やかに落ちる */}
      <svg width="0" height="0" style={{position: 'absolute'}}>
        <defs>
          <filter id="gradeB" colorInterpolationFilters="sRGB">
            <feComponentTransfer>
              <feFuncR type="table" tableValues="0.024 0.227 0.494 0.755 0.980" />
              <feFuncG type="table" tableValues="0.039 0.243 0.502 0.759 0.984" />
              <feFuncB type="table" tableValues="0.063 0.267 0.510 0.750 0.965" />
            </feComponentTransfer>
          </filter>
        </defs>
      </svg>
      {/* カバー画像: 0フレーム目のみ(プレイヤーのポスターフレーム用) */}
      <Sequence from={0} durationInFrames={1}>
        <CoverFrame />
      </Sequence>
      <Sequence from={61}>
        <AbsoluteFill>
      {/* 映像トラック */}
      <Sequence from={S1.from} durationInFrames={S1.dur}>
        <LiveCut
          src="mirai/cut01_veo.mp4"
          srcVertical="mirai/cut01_v_veo.mp4"
          portraitForSquare
          anchorX={55}
          telop={['写真整理は、会社に帰ってから…?']}
          fadeInFrames={0}
        />
      </Sequence>
      <Sequence from={S2.from} durationInFrames={S2.dur}>
        <LiveCut
          src="mirai/cut02_cu_veo.mp4"
          srcVertical="mirai/cut02_v_veo.mp4"
          portraitForSquare
          anchorX={50}
          rate={1}
          telop={['取り込んで、仕分けて、貼り付けて。']}
          fadeOutAt={S2.dur - 7}
        />
      </Sequence>
      <Sequence from={S2B.from} durationInFrames={S2B.dur}>
        <StatCut />
      </Sequence>
      <Sequence from={S3A.from} durationInFrames={S3A.dur}>
        <LiveCut src="mirai/cut03_veo.mp4" telop={['スマホで、撮るだけ。']} anchorX={55} />
      </Sequence>
      <Sequence from={S3B.from} durationInFrames={S3B.dur}>
        <AutoLedger />
      </Sequence>
      <Sequence from={S4.from} durationInFrames={S4.dur}>
        <PdfScene />
      </Sequence>
      <Sequence from={S5.from} durationInFrames={S5.dur}>
        <LiveCut
          src="mirai/cut05_veo.mp4"
          anchorX={40}
          telop={['お客様へ、その場で送信。']}
          fadeOutAt={S5.dur - 7}
        />
        <SendFx />
      </Sequence>
      <Sequence from={S5B.from} durationInFrames={S5B.dur}>
        <LiveCut
          src="mirai/cut05b_veo.mp4"
          srcVertical="mirai/cut05b_v_veo.mp4"
          telop={['持ち帰りゼロへ。']}
          anchorX={48}
        />
        <DeliveryFx />
      </Sequence>
      <Sequence from={S6.from} durationInFrames={S6.dur}>
        <Cta />
      </Sequence>

      {/* ナレーショントラック(シーンから独立 — 境界で切れない) */}
      {naStarts.map((from, i) => (
        <Sequence key={`na${i}`} from={from} durationInFrames={NA_DUR[i]}>
          <Audio src={staticFile(`mirai/na${i + 1}_pro.mp3`)} />
        </Sequence>
      ))}

      {/* SE: シャッター音(フラッシュのピークに同期)+ 行が入るポップ音×3 */}
      <Sequence from={S3B.from + 24} durationInFrames={30}>
        <Audio src={staticFile('mirai/shutter.wav')} volume={1} />
      </Sequence>
      {FLY_DELAYS.map((d) => (
        <Sequence key={`pop${d}`} from={S3B.from + d + FLY_DUR} durationInFrames={40}>
          <Audio src={staticFile('mirai/pop.wav')} volume={0.7} />
        </Sequence>
      ))}
      {/* PDF完成スタンプの効果音 */}
      <Sequence from={S4.from + 62} durationInFrames={30}>
        <Audio src={staticFile('mirai/stamp.wav')} volume={0.85} />
      </Sequence>
      {/* 環境音ベッド: 実在感のための薄敷き(意識に上らない音量) */}
      <Sequence from={S1.from} durationInFrames={S1.dur}>
        <Audio src={staticFile('mirai/cut01_sfx.mp4')} volume={0.22} />
      </Sequence>
      <Sequence from={S2.from} durationInFrames={S2.dur}>
        <Audio src={staticFile('mirai/cut02_sfx.mp4')} volume={0.18} />
      </Sequence>
      <Sequence from={S3A.from} durationInFrames={S3A.dur}>
        <Audio src={staticFile('mirai/cut03_sfx.mp4')} volume={0.22} />
      </Sequence>
      <Sequence from={S5.from} durationInFrames={S5.dur}>
        <Audio src={staticFile('mirai/cut05_sfx.mp4')} volume={0.18} />
      </Sequence>

      {/* 送信のヒュッという音 */}
      <Sequence from={S5.from + 42} durationInFrames={30}>
        <Audio src={staticFile('mirai/whoosh.wav')} volume={0.6} />
      </Sequence>
      {/* 客先の「届いた」通知音 */}
      <Sequence from={S5B.from + DELIVERY_LAND + 3} durationInFrames={40}>
        <Audio src={staticFile('mirai/pop.wav')} volume={0.75} />
      </Sequence>

      {/* BGM 2トラック構成: 悩み(前半) → 転換点で解決(後半) */}
      <Sequence from={0} durationInFrames={S3A_FROM}>
        <Audio src={staticFile('mirai/bgm_problem.wav')} volume={bgmProblemVolume} />
      </Sequence>
      <Sequence from={S3A_FROM} durationInFrames={900 - S3A_FROM}>
        <Audio src={staticFile('mirai/bgm_solution.wav')} volume={bgmSolutionVolume} />
      </Sequence>

      {/* 全画面固定のロゴウォーターマーク(左上・白文字ロックアップ+ソフトシャドウ)
          縦型はリールUI(上部のカメラ/音源表示など)を避けてセーフゾーン内に配置 */}
      <WatermarkLogo />
        </AbsoluteFill>
      </Sequence>

      {/* スプラッシュ(本編の頭にクロスフェードで重なる) */}
      <Sequence from={1} durationInFrames={66}>
        <SplashComp />
      </Sequence>

      {/* サウンドロゴ(自社生成)+ ブランドコール「ミライコウジ」 */}
      <Sequence from={1} durationInFrames={95}>
        <Audio src={staticFile(soundlogoSrc)} volume={0.9} />
      </Sequence>
      <Sequence from={25} durationInFrames={35}>
        <Audio src={staticFile('mirai/mirai_call.wav')} volume={1} />
      </Sequence>
    </AbsoluteFill>
  );
};

/**
 * 公開コンポジション。`compliance` は cm-pipeline build が --props で渡す
 * （AI利用開示テロップ・セーフゾーン・字幕方針）。未指定なら従来どおり。
 */
export const MiraiCM: React.FC<{splashVariant?: 'A' | 'B' | 'C'; compliance?: Compliance}> = ({
  splashVariant = 'A',
  compliance,
}) => (
  <ComplianceProvider value={compliance}>
    <AbsoluteFill>
      <MiraiCMInner splashVariant={splashVariant} />
      <DisclosureCaption />
      <SafeZoneGuides />
    </AbsoluteFill>
  </ComplianceProvider>
);
