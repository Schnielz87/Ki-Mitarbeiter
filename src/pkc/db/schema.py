"""Schemadefinitionen als versionierte Migrationsskripte.

Die SQL-Skripte sind absichtlich im Python-Modul eingebettet: so gibt es beim
EXE-Packaging keine zusaetzlichen Datendateien, die verloren gehen koennen.

Trennung nach Masterprompt Abschnitt 14:
* ``knowledge.db`` - allgemeines Fachwissen (Gesetze, Erlasse, Rechtsprechung)
* ``company.db``   - Unternehmenswissen, Gespraeche, Belege, Audit, Freigaben
"""

from __future__ import annotations

# ---------------------------------------------------------------- knowledge
KNOWLEDGE_V1 = """
CREATE TABLE sources (
    id              INTEGER PRIMARY KEY,
    source_id       TEXT NOT NULL UNIQUE,      -- z.B. Q01_GESETZE_IM_INTERNET
    name            TEXT NOT NULL,
    publisher       TEXT,
    priority        INTEGER NOT NULL DEFAULT 5,-- 1 = Primaerquelle (Gesetz)
    kind            TEXT NOT NULL,             -- law | admin | case_law | authority | secondary
    base_url        TEXT,
    licence         TEXT,
    enabled         INTEGER NOT NULL DEFAULT 1,
    last_checked    TEXT,
    last_success    TEXT,
    last_error      TEXT,
    meta_json       TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE documents (
    id              INTEGER PRIMARY KEY,
    doc_uid         TEXT NOT NULL UNIQUE,      -- stabile fachliche ID
    source_id       TEXT NOT NULL REFERENCES sources(source_id) ON DELETE CASCADE,
    collection      TEXT NOT NULL DEFAULT 'knowledge',
    title           TEXT NOT NULL,
    short_title     TEXT,
    url             TEXT,
    kind            TEXT,                      -- law | admin | case_law | article
    citation        TEXT,                      -- z.B. "§ 14 UStG"
    lang            TEXT NOT NULL DEFAULT 'de',
    path_raw        TEXT,                      -- relativ zur Wurzel
    path_normalized TEXT,
    sha256          TEXT,
    bytes           INTEGER,
    etag            TEXT,
    last_modified   TEXT,
    published_at    TEXT,
    fetched_at      TEXT,
    valid_from      TEXT,
    valid_to        TEXT,
    version         INTEGER NOT NULL DEFAULT 1,
    licence         TEXT,
    status          TEXT NOT NULL DEFAULT 'active', -- active | superseded | withdrawn
    priority        INTEGER NOT NULL DEFAULT 5,
    meta_json       TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX idx_documents_source ON documents(source_id);
CREATE INDEX idx_documents_status ON documents(status);
CREATE INDEX idx_documents_valid ON documents(valid_from, valid_to);

CREATE TABLE chunks (
    id              INTEGER PRIMARY KEY,
    doc_id          INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    ord             INTEGER NOT NULL,
    heading         TEXT,
    citation        TEXT,
    text            TEXT NOT NULL,
    tokens          INTEGER NOT NULL DEFAULT 0,
    sha256          TEXT,
    UNIQUE(doc_id, ord)
);
CREATE INDEX idx_chunks_doc ON chunks(doc_id);

CREATE VIRTUAL TABLE chunks_fts USING fts5(
    text,
    heading,
    citation,
    content='chunks',
    content_rowid='id',
    tokenize='unicode61 remove_diacritics 2'
);

CREATE TRIGGER chunks_ai AFTER INSERT ON chunks BEGIN
    INSERT INTO chunks_fts(rowid, text, heading, citation)
    VALUES (new.id, new.text, new.heading, new.citation);
END;
CREATE TRIGGER chunks_ad AFTER DELETE ON chunks BEGIN
    INSERT INTO chunks_fts(chunks_fts, rowid, text, heading, citation)
    VALUES ('delete', old.id, old.text, old.heading, old.citation);
END;
CREATE TRIGGER chunks_au AFTER UPDATE ON chunks BEGIN
    INSERT INTO chunks_fts(chunks_fts, rowid, text, heading, citation)
    VALUES ('delete', old.id, old.text, old.heading, old.citation);
    INSERT INTO chunks_fts(rowid, text, heading, citation)
    VALUES (new.id, new.text, new.heading, new.citation);
END;

CREATE TABLE embeddings (
    chunk_id    INTEGER PRIMARY KEY REFERENCES chunks(id) ON DELETE CASCADE,
    model       TEXT NOT NULL,
    dim         INTEGER NOT NULL,
    norm        REAL NOT NULL DEFAULT 1.0,
    vector      BLOB NOT NULL
);

CREATE TABLE update_runs (
    id              INTEGER PRIMARY KEY,
    started_at      TEXT NOT NULL,
    finished_at     TEXT,
    status          TEXT NOT NULL,             -- running | success | partial | failed | rolled_back
    trigger         TEXT NOT NULL DEFAULT 'manual',
    checked         INTEGER NOT NULL DEFAULT 0,
    downloaded      INTEGER NOT NULL DEFAULT 0,
    updated         INTEGER NOT NULL DEFAULT 0,
    unchanged       INTEGER NOT NULL DEFAULT 0,
    failed          INTEGER NOT NULL DEFAULT 0,
    report_path     TEXT,
    detail_json     TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE knowledge_state (
    key     TEXT PRIMARY KEY,
    value   TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""

KNOWLEDGE_MIGRATIONS = [(1, KNOWLEDGE_V1)]

# ------------------------------------------------------------------ company
COMPANY_V1 = """
CREATE TABLE memory (
    id              INTEGER PRIMARY KEY,
    mem_key         TEXT NOT NULL,             -- stabiler fachlicher Schluessel
    category        TEXT NOT NULL,             -- profile|accounting|process|rule|...
    title           TEXT NOT NULL,
    content         TEXT NOT NULL,
    value_json      TEXT,                      -- optional strukturiert
    status          TEXT NOT NULL DEFAULT 'active', -- active|archived|superseded
    version         INTEGER NOT NULL DEFAULT 1,
    confidence      REAL NOT NULL DEFAULT 1.0,
    source          TEXT,                      -- z.B. "Chat 2026-09-04"
    origin          TEXT NOT NULL DEFAULT 'user', -- user|onboarding|import|agent
    valid_from      TEXT,
    valid_to        TEXT,
    review_at       TEXT,
    tags            TEXT NOT NULL DEFAULT '',
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL,
    created_by      TEXT NOT NULL DEFAULT 'user',
    UNIQUE(mem_key, version)
);
CREATE INDEX idx_memory_status ON memory(status);
CREATE INDEX idx_memory_category ON memory(category);
CREATE INDEX idx_memory_key ON memory(mem_key);

CREATE TABLE memory_history (
    id              INTEGER PRIMARY KEY,
    mem_key         TEXT NOT NULL,
    version         INTEGER NOT NULL,
    change_type     TEXT NOT NULL,             -- create|update|archive|delete|restore
    changed_at      TEXT NOT NULL,
    changed_by      TEXT NOT NULL DEFAULT 'user',
    reason          TEXT,
    snapshot_json   TEXT NOT NULL
);
CREATE INDEX idx_memhist_key ON memory_history(mem_key);

CREATE VIRTUAL TABLE memory_fts USING fts5(
    title, content, tags,
    content='memory',
    content_rowid='id',
    tokenize='unicode61 remove_diacritics 2'
);
CREATE TRIGGER memory_ai AFTER INSERT ON memory BEGIN
    INSERT INTO memory_fts(rowid, title, content, tags)
    VALUES (new.id, new.title, new.content, new.tags);
END;
CREATE TRIGGER memory_ad AFTER DELETE ON memory BEGIN
    INSERT INTO memory_fts(memory_fts, rowid, title, content, tags)
    VALUES ('delete', old.id, old.title, old.content, old.tags);
END;
CREATE TRIGGER memory_au AFTER UPDATE ON memory BEGIN
    INSERT INTO memory_fts(memory_fts, rowid, title, content, tags)
    VALUES ('delete', old.id, old.title, old.content, old.tags);
    INSERT INTO memory_fts(rowid, title, content, tags)
    VALUES (new.id, new.title, new.content, new.tags);
END;

CREATE TABLE conversations (
    id              INTEGER PRIMARY KEY,
    uid             TEXT NOT NULL UNIQUE,
    title           TEXT NOT NULL,
    profile         TEXT NOT NULL DEFAULT 'buchhalter',
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL,
    archived        INTEGER NOT NULL DEFAULT 0,
    meta_json       TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE messages (
    id              INTEGER PRIMARY KEY,
    conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role            TEXT NOT NULL,             -- user|assistant|system|note
    content         TEXT NOT NULL,
    created_at      TEXT NOT NULL,
    mode            TEXT,                      -- OFFLINE|HYBRID zum Zeitpunkt
    model           TEXT,
    meta_json       TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX idx_messages_conv ON messages(conversation_id, id);

CREATE TABLE message_sources (
    id              INTEGER PRIMARY KEY,
    message_id      INTEGER NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    rank            INTEGER NOT NULL,
    origin          TEXT NOT NULL,             -- knowledge|company|document
    ref_id          TEXT,
    citation        TEXT,
    title           TEXT,
    url             TEXT,
    score           REAL,
    excerpt         TEXT
);
CREATE INDEX idx_msgsrc_msg ON message_sources(message_id);

CREATE TABLE user_documents (
    id              INTEGER PRIMARY KEY,
    doc_uid         TEXT NOT NULL UNIQUE,
    title           TEXT NOT NULL,
    path            TEXT NOT NULL,
    kind            TEXT,
    sha256          TEXT,
    bytes           INTEGER,
    added_at        TEXT NOT NULL,
    pages           INTEGER,
    status          TEXT NOT NULL DEFAULT 'active',
    meta_json       TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE user_chunks (
    id              INTEGER PRIMARY KEY,
    doc_id          INTEGER NOT NULL REFERENCES user_documents(id) ON DELETE CASCADE,
    ord             INTEGER NOT NULL,
    heading         TEXT,
    text            TEXT NOT NULL,
    tokens          INTEGER NOT NULL DEFAULT 0,
    UNIQUE(doc_id, ord)
);
CREATE VIRTUAL TABLE user_chunks_fts USING fts5(
    text, heading,
    content='user_chunks',
    content_rowid='id',
    tokenize='unicode61 remove_diacritics 2'
);
CREATE TRIGGER uchunks_ai AFTER INSERT ON user_chunks BEGIN
    INSERT INTO user_chunks_fts(rowid, text, heading) VALUES (new.id, new.text, new.heading);
END;
CREATE TRIGGER uchunks_ad AFTER DELETE ON user_chunks BEGIN
    INSERT INTO user_chunks_fts(user_chunks_fts, rowid, text, heading)
    VALUES ('delete', old.id, old.text, old.heading);
END;

CREATE TABLE audit_log (
    id              INTEGER PRIMARY KEY,
    ts              TEXT NOT NULL,
    actor           TEXT NOT NULL,
    action          TEXT NOT NULL,
    object_type     TEXT,
    object_id       TEXT,
    status          TEXT NOT NULL DEFAULT 'ok',
    detail_json     TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX idx_audit_ts ON audit_log(ts);

CREATE TABLE approvals (
    id              INTEGER PRIMARY KEY,
    uid             TEXT NOT NULL UNIQUE,
    object_type     TEXT NOT NULL,             -- booking|export|erp_write|payment
    title           TEXT NOT NULL,
    state           TEXT NOT NULL,             -- ENTWURF|GEPRUEFT|FREIGEGEBEN|AUSGEFUEHRT|ABGELEHNT
    payload_json    TEXT NOT NULL DEFAULT '{}',
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL,
    requested_by    TEXT,
    decided_by      TEXT,
    decided_at      TEXT,
    note            TEXT
);

CREATE TABLE app_state (
    key         TEXT PRIMARY KEY,
    value       TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);
"""

COMPANY_MIGRATIONS = [(1, COMPANY_V1)]
