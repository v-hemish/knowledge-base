"""SQLite DDL: canonical `verses` table + FTS5 external content + triggers."""

# Bump when FTS or verse columns change; `migrate.apply_migrations` uses this.
SCHEMA_VERSION = 2

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS verses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chapter INTEGER NOT NULL,
    verse INTEGER NOT NULL,
    citation_key TEXT NOT NULL,
    sanskrit TEXT,
    transliteration TEXT,
    translation TEXT NOT NULL,
    theme_tags TEXT NOT NULL DEFAULT '[]',
    situation_tags TEXT NOT NULL DEFAULT '[]',
    use_with_care_tags TEXT NOT NULL DEFAULT '[]',
    translation_source TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(chapter, verse)
);

-- FUTURE: normalized tag tables + join indices; FTS UNINDEXED metadata columns.

CREATE VIRTUAL TABLE IF NOT EXISTS verses_fts USING fts5(
    translation,
    sanskrit,
    transliteration,
    theme_tags,
    situation_tags,
    use_with_care_tags,
    content='verses',
    content_rowid='id',
    tokenize='unicode61 remove_diacritics 1'
);

CREATE TRIGGER IF NOT EXISTS verses_ai AFTER INSERT ON verses BEGIN
    INSERT INTO verses_fts(
        rowid, translation, sanskrit, transliteration,
        theme_tags, situation_tags, use_with_care_tags
    )
    VALUES (
        new.id, new.translation, new.sanskrit, new.transliteration,
        new.theme_tags, new.situation_tags, new.use_with_care_tags
    );
END;

CREATE TRIGGER IF NOT EXISTS verses_ad AFTER DELETE ON verses BEGIN
    INSERT INTO verses_fts(
        verses_fts, rowid, translation, sanskrit, transliteration,
        theme_tags, situation_tags, use_with_care_tags
    )
    VALUES(
        'delete', old.id, old.translation, old.sanskrit, old.transliteration,
        old.theme_tags, old.situation_tags, old.use_with_care_tags
    );
END;

CREATE TRIGGER IF NOT EXISTS verses_au AFTER UPDATE ON verses BEGIN
    INSERT INTO verses_fts(
        verses_fts, rowid, translation, sanskrit, transliteration,
        theme_tags, situation_tags, use_with_care_tags
    )
    VALUES(
        'delete', old.id, old.translation, old.sanskrit, old.transliteration,
        old.theme_tags, old.situation_tags, old.use_with_care_tags
    );
    INSERT INTO verses_fts(
        rowid, translation, sanskrit, transliteration,
        theme_tags, situation_tags, use_with_care_tags
    )
    VALUES (
        new.id, new.translation, new.sanskrit, new.transliteration,
        new.theme_tags, new.situation_tags, new.use_with_care_tags
    );
END;
"""

DROP_FTS_SQL = """
DROP TRIGGER IF EXISTS verses_ai;
DROP TRIGGER IF EXISTS verses_ad;
DROP TRIGGER IF EXISTS verses_au;
DROP TABLE IF EXISTS verses_fts;
"""

CREATE_FTS_ONLY_SQL = """
CREATE VIRTUAL TABLE verses_fts USING fts5(
    translation,
    sanskrit,
    transliteration,
    theme_tags,
    situation_tags,
    use_with_care_tags,
    content='verses',
    content_rowid='id',
    tokenize='unicode61 remove_diacritics 1'
);

CREATE TRIGGER verses_ai AFTER INSERT ON verses BEGIN
    INSERT INTO verses_fts(
        rowid, translation, sanskrit, transliteration,
        theme_tags, situation_tags, use_with_care_tags
    )
    VALUES (
        new.id, new.translation, new.sanskrit, new.transliteration,
        new.theme_tags, new.situation_tags, new.use_with_care_tags
    );
END;

CREATE TRIGGER verses_ad AFTER DELETE ON verses BEGIN
    INSERT INTO verses_fts(
        verses_fts, rowid, translation, sanskrit, transliteration,
        theme_tags, situation_tags, use_with_care_tags
    )
    VALUES(
        'delete', old.id, old.translation, old.sanskrit, old.transliteration,
        old.theme_tags, old.situation_tags, old.use_with_care_tags
    );
END;

CREATE TRIGGER verses_au AFTER UPDATE ON verses BEGIN
    INSERT INTO verses_fts(
        verses_fts, rowid, translation, sanskrit, transliteration,
        theme_tags, situation_tags, use_with_care_tags
    )
    VALUES(
        'delete', old.id, old.translation, old.sanskrit, old.transliteration,
        old.theme_tags, old.situation_tags, old.use_with_care_tags
    );
    INSERT INTO verses_fts(
        rowid, translation, sanskrit, transliteration,
        theme_tags, situation_tags, use_with_care_tags
    )
    VALUES (
        new.id, new.translation, new.sanskrit, new.transliteration,
        new.theme_tags, new.situation_tags, new.use_with_care_tags
    );
END;
"""
