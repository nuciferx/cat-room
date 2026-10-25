/** ของที่ router ต้องใช้ทั้งหมด ผูกไว้ก้อนเดียว (state เดียว ส่งผ่าน parameter ไม่ใช้ global) */
import type { CatConfig } from '../data/config';
import type { Locale } from '../data/locale';
import type { ShowroomState } from '../logic/showroomState';
import type { CameraRig } from '../render/cameraRig';
import type { DualActor } from '../render/dualActor';
import type { Stage } from '../render/stage';
import type { Banner } from '../ui/banner';
import type { ClipBar } from '../ui/clipBar';
import type { FaceBar } from '../ui/faceBar';
import type { ViewBar } from '../ui/viewBar';
import type { HelpPanel } from '../ui/helpPanel';
import type { TunePanel } from '../ui/tunePanel';

export interface ShowroomCtx {
  cfg: CatConfig;
  state: ShowroomState;
  locale: Locale;
  rig: CameraRig;
  actor: DualActor;
  stage: Stage;
  clipBar: ClipBar;
  faceBar: FaceBar;
  viewBar: ViewBar;
  help: HelpPanel;
  tune: TunePanel;
  banner: Banner;
  /** เวลาต่อเฟรมล่าสุด (วินาที) ให้อินพุตแบบต่อเนื่อง (ไม้/ไกจอย) ใช้ */
  frame: { dtS: number };
}
