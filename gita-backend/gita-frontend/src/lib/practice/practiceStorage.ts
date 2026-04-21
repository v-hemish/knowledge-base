"use client";

const STORAGE_KEY = "gita-practice-v1";

export type LearnedEntry = { citationKey: string; learnedAt: string };

export type PracticePersist = {
  savedKeys: string[];
  learned: LearnedEntry[];
  /** YYYY-MM-DD local days marked "completed" for Verse of the Day */
  completedDays: string[];
  /** Last verse the user was studying in Learn (restores position when reopening). */
  lastLearnCitationKey: string | null;
  /** User dismissed the short Learn tips strip. */
  learnTipsDismissed: boolean;
};

function empty(): PracticePersist {
  return {
    savedKeys: [],
    learned: [],
    completedDays: [],
    lastLearnCitationKey: null,
    learnTipsDismissed: false,
  };
}

function read(): PracticePersist {
  if (typeof window === "undefined") return empty();
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return empty();
    const o = JSON.parse(raw) as Partial<PracticePersist>;
    return {
      savedKeys: Array.isArray(o.savedKeys) ? o.savedKeys.filter((x) => typeof x === "string") : [],
      learned: Array.isArray(o.learned)
        ? o.learned.filter((e) => e && typeof e.citationKey === "string" && typeof e.learnedAt === "string")
        : [],
      completedDays: Array.isArray(o.completedDays)
        ? o.completedDays.filter((x) => typeof x === "string")
        : [],
      lastLearnCitationKey: typeof o.lastLearnCitationKey === "string" ? o.lastLearnCitationKey : null,
      learnTipsDismissed: o.learnTipsDismissed === true,
    };
  } catch {
    return empty();
  }
}

function write(data: PracticePersist) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
}

function localDayKey(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

export function getPracticePersist(): PracticePersist {
  return read();
}

export function toggleSaved(citationKey: string): boolean {
  const data = read();
  const has = data.savedKeys.includes(citationKey);
  data.savedKeys = has ? data.savedKeys.filter((k) => k !== citationKey) : [...data.savedKeys, citationKey];
  write(data);
  return !has;
}

export function isSaved(citationKey: string): boolean {
  return read().savedKeys.includes(citationKey);
}

export function markLearned(citationKey: string, at: Date = new Date()) {
  const data = read();
  if (data.learned.some((e) => e.citationKey === citationKey)) return;
  data.learned = [{ citationKey, learnedAt: at.toISOString() }, ...data.learned].slice(0, 200);
  write(data);
}

export function isLearned(citationKey: string): boolean {
  return read().learned.some((e) => e.citationKey === citationKey);
}

export function markVerseOfDayComplete(d: Date = new Date()) {
  const day = localDayKey(d);
  const data = read();
  if (data.completedDays.includes(day)) return;
  data.completedDays = [day, ...data.completedDays].slice(0, 400);
  write(data);
}

export function unmarkVerseOfDayComplete(d: Date = new Date()) {
  const day = localDayKey(d);
  const data = read();
  if (!data.completedDays.includes(day)) return;
  data.completedDays = data.completedDays.filter((x) => x !== day);
  write(data);
}

export function isVerseOfDayComplete(d: Date = new Date()): boolean {
  return read().completedDays.includes(localDayKey(d));
}

/** Consecutive days ending on `end` (local calendar). */
export function streakCountEndingOn(end: Date = new Date()): number {
  const days = new Set(read().completedDays);
  let n = 0;
  const cur = new Date(end.getFullYear(), end.getMonth(), end.getDate());
  while (days.has(localDayKey(cur))) {
    n += 1;
    cur.setDate(cur.getDate() - 1);
  }
  return n;
}

export function setLastLearnCitationKey(citationKey: string) {
  const data = read();
  data.lastLearnCitationKey = citationKey;
  write(data);
}

export function dismissLearnTips() {
  const data = read();
  data.learnTipsDismissed = true;
  write(data);
}

export function hasLearnTipsDismissed(): boolean {
  return read().learnTipsDismissed;
}
