create table if not exists public.protocols (
  id text primary key,
  title text not null,
  domain text,
  keywords jsonb not null default '[]'::jsonb,
  hazards jsonb not null default '[]'::jsonb,
  read_aloud_summary text,
  body_markdown text not null,
  source_path text not null,
  source_hash text not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.safety_sheets (
  id text primary key,
  name text not null,
  synonyms jsonb not null default '[]'::jsonb,
  hazards jsonb not null default '[]'::jsonb,
  ppe jsonb not null default '[]'::jsonb,
  first_aid jsonb not null default '{}'::jsonb,
  disclaimer text not null,
  source_path text not null,
  source_hash text not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.hardware_guides (
  id text primary key,
  device text not null,
  symptom text not null,
  keywords jsonb not null default '[]'::jsonb,
  steps jsonb not null default '[]'::jsonb,
  escalate_if text,
  source_path text not null,
  source_hash text not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.sensor_profiles (
  id text primary key,
  name text not null,
  measures text not null,
  accuracy jsonb not null default '{}'::jsonb,
  error_sources jsonb not null default '[]'::jsonb,
  availability text,
  calibration text,
  voice_guidance text,
  source_path text not null,
  source_hash text not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.call_receipts (
  id text primary key,
  call_id_hash text not null,
  tool_name text not null,
  source_ids jsonb not null default '[]'::jsonb,
  redacted_summary text,
  created_at timestamptz not null default now()
);

alter table public.protocols enable row level security;
alter table public.safety_sheets enable row level security;
alter table public.hardware_guides enable row level security;
alter table public.sensor_profiles enable row level security;
alter table public.call_receipts enable row level security;

-- Reference content is public, read-only to runtime roles. RLS denies writes
-- (no write policy); the edge function reads via the anon key. Seeding happens
-- with the admin API key, which bypasses RLS.
create policy "phonebio_read_protocols" on public.protocols for select using (true);
create policy "phonebio_read_safety_sheets" on public.safety_sheets for select using (true);
create policy "phonebio_read_hardware_guides" on public.hardware_guides for select using (true);
create policy "phonebio_read_sensor_profiles" on public.sensor_profiles for select using (true);
-- call_receipts: no runtime policy on purpose -> only the admin/service key writes.
