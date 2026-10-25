/** ข้อความบนจอ : เลือกไฟล์ภาษาแล้วดึงด้วย path เช่น `clip.idle` · แทนค่า {ชื่อ} ในข้อความด้วย vars */
import th from '../../locales/th.json';
import en from '../../locales/en.json';
import { DEFAULT_LANG, type Lang } from '../constants/app';

const TABLES: Record<Lang, unknown> = { th, en };

export type Translate = (path: string, vars?: Record<string, string>) => string;

export interface Locale {
  t: Translate;
  /** ดึงโครงข้อมูลดิบ (เช่น แถวป้ายช่วยเหลือ) */
  raw: <T>(path: string) => T;
}

function dig(table: unknown, path: string): unknown {
  let cur: unknown = table;
  for (const part of path.split('.')) {
    if (typeof cur !== 'object' || cur === null) return undefined;
    cur = (cur as Record<string, unknown>)[part];
  }
  return cur;
}

export function createLocale(lang: Lang): Locale {
  const table = TABLES[lang] ?? TABLES[DEFAULT_LANG];
  const raw = <T>(path: string): T => dig(table, path) as T;
  const t: Translate = (path, vars) => {
    const found = dig(table, path);
    // ไม่พบคีย์ → แสดงคีย์เอง ให้เห็นว่าตกหล่นตรงไหน
    const text = typeof found === 'string' ? found : path;
    if (!vars) return text;
    return text.replace(/\{(\w+)\}/g, (m, k: string) => vars[k] ?? m);
  };
  return { t, raw };
}
