CREATE TABLE items (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    title text NOT NULL CHECK (length(btrim(title)) BETWEEN 1 AND 120),
    created_at timestamptz NOT NULL DEFAULT now()
);
