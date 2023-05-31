CREATE TABLE issues (
    id SERIAL PRIMARY KEY,
    repository_owner TEXT NOT NULL,
    repository TEXT NOT NULL,
    title TEXT NOT NULL,
    stars INTEGER NOT NULL DEFAULT 0,
    primary_language TEXT,
    url TEXT NOT NULL UNIQUE,
    labels TEXT NOT NULL,
    state VARCHAR(10) NOT NULL,
    comments INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL
);