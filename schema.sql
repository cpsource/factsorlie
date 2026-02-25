CREATE TABLE querys (
    idx BIGSERIAL PRIMARY KEY,
    row_src VARCHAR(10) NOT NULL CHECK (row_src IN ('submit','query')),
    question_gz BYTEA NOT NULL,
    response_gz BYTEA NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE errors (
    idx BIGSERIAL PRIMARY KEY,
    row_src VARCHAR(10) NOT NULL,
    question_gz BYTEA NOT NULL,
    error JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
