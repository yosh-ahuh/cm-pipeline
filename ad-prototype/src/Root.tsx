import React from 'react';
import {Composition} from 'remotion';
import {Ad} from './Ad';
import {IntroPreview, MiraiCM} from './MiraiCM';
import {DEMO_PROPS, SpotAd, SpotAdProps} from './SpotAd';

export const Root: React.FC = () => {
  // 汎用コンポジション（project.yaml 駆動）。尺は props.durationInFrames で決まる。
  const spotMeta = ({props}: {props: SpotAdProps}) => ({durationInFrames: props.durationInFrames});
  return (
    <>
      <Composition id="SpotAd" component={SpotAd} defaultProps={DEMO_PROPS} calculateMetadata={spotMeta} durationInFrames={961} fps={30} width={1920} height={1080} />
      <Composition id="SpotAd-V" component={SpotAd} defaultProps={DEMO_PROPS} calculateMetadata={spotMeta} durationInFrames={961} fps={30} width={1080} height={1920} />
      <Composition id="SpotAd-SQ" component={SpotAd} defaultProps={DEMO_PROPS} calculateMetadata={spotMeta} durationInFrames={961} fps={30} width={1080} height={1080} />
      <Composition
        id="SaaSAd"
        component={Ad}
        durationInFrames={450}
        fps={30}
        width={1080}
        height={1920}
      />
      <Composition
        id="IntroB"
        component={IntroPreview}
        defaultProps={{variant: 'B'}}
        durationInFrames={90}
        fps={30}
        width={1920}
        height={1080}
      />
      <Composition
        id="IntroC"
        component={IntroPreview}
        defaultProps={{variant: 'C'}}
        durationInFrames={90}
        fps={30}
        width={1920}
        height={1080}
      />
      <Composition
        id="MiraiCM"
        component={MiraiCM}
        defaultProps={{splashVariant: 'A' as const}}
        durationInFrames={961}
        fps={30}
        width={1920}
        height={1080}
      />
      <Composition
        id="MiraiCM-V"
        component={MiraiCM}
        defaultProps={{splashVariant: 'A' as const}}
        durationInFrames={961}
        fps={30}
        width={1080}
        height={1920}
      />
      <Composition
        id="MiraiCM-SQ"
        component={MiraiCM}
        defaultProps={{splashVariant: 'A' as const}}
        durationInFrames={961}
        fps={30}
        width={1080}
        height={1080}
      />
      <Composition
        id="MiraiCM-B-V"
        component={MiraiCM}
        defaultProps={{splashVariant: 'B' as const}}
        durationInFrames={961}
        fps={30}
        width={1080}
        height={1920}
      />
      <Composition
        id="MiraiCM-B-SQ"
        component={MiraiCM}
        defaultProps={{splashVariant: 'B' as const}}
        durationInFrames={961}
        fps={30}
        width={1080}
        height={1080}
      />
      <Composition
        id="MiraiCM-C-V"
        component={MiraiCM}
        defaultProps={{splashVariant: 'C' as const}}
        durationInFrames={961}
        fps={30}
        width={1080}
        height={1920}
      />
      <Composition
        id="MiraiCM-C-SQ"
        component={MiraiCM}
        defaultProps={{splashVariant: 'C' as const}}
        durationInFrames={961}
        fps={30}
        width={1080}
        height={1080}
      />
      <Composition
        id="MiraiCM-B"
        component={MiraiCM}
        defaultProps={{splashVariant: 'B' as const}}
        durationInFrames={961}
        fps={30}
        width={1920}
        height={1080}
      />
      <Composition
        id="MiraiCM-C"
        component={MiraiCM}
        defaultProps={{splashVariant: 'C' as const}}
        durationInFrames={961}
        fps={30}
        width={1920}
        height={1080}
      />
    </>
  );
};
