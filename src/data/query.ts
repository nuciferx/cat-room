/** อ่าน query string : ?clip= ?face= ?view=25d ?q=low ?grid=0 ?lang=en */
import { DEFAULT_LANG, GRID_OFF, LANGS, QUALITY_LOW, QUERY, type Lang } from '../constants/app';
import { isClipName, type ClipName } from '../constants/clips';
import { isFaceName, type FaceName } from '../constants/faces';
import { isViewName, type ViewName } from '../constants/views';

export interface PageQuery {
  clip: ClipName | null;
  face: FaceName | null;
  view: ViewName | null;
  low: boolean;
  grid: boolean;
  lang: Lang;
}

export function parseQuery(search: string): PageQuery {
  const q = new URLSearchParams(search);
  const clip = q.get(QUERY.clip);
  const face = q.get(QUERY.face);
  const view = q.get(QUERY.view);
  const lang = q.get(QUERY.lang);
  return {
    clip: isClipName(clip) ? clip : null,
    face: isFaceName(face) ? face : null,
    view: isViewName(view) ? view : null,
    low: q.get(QUERY.quality) === QUALITY_LOW,
    grid: q.get(QUERY.grid) !== GRID_OFF,
    lang: (LANGS as readonly string[]).includes(lang ?? '') ? (lang as Lang) : DEFAULT_LANG,
  };
}
