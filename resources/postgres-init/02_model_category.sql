-- Copyright 2026 by GuidoGerb Publishing, LLC
--
-- Model category hierarchy and model registry.
-- Categories form a tree via parent_id; each model maps to a category + S3 prefix.

CREATE TABLE IF NOT EXISTS public.model_category (
    id              SERIAL          PRIMARY KEY,
    name            VARCHAR(256)    NOT NULL,
    parent_id       INTEGER         REFERENCES public.model_category(id) ON DELETE CASCADE,
    description     TEXT            NOT NULL DEFAULT '',
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_model_category_unique_name_parent
    ON public.model_category (name, COALESCE(parent_id, 0));

CREATE TABLE IF NOT EXISTS public.model_registry (
    id              SERIAL          PRIMARY KEY,
    repo_id         VARCHAR(256)    NOT NULL UNIQUE,
    category_id     INTEGER         NOT NULL REFERENCES public.model_category(id),
    s3_prefix       VARCHAR(512)    NOT NULL,
    display_name    VARCHAR(256)    NOT NULL DEFAULT '',
    description     TEXT            NOT NULL DEFAULT '',
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_model_registry_category
    ON public.model_registry (category_id);

-- Seed top-level categories
INSERT INTO public.model_category (name, parent_id, description) VALUES
    ('LLM - Foundation',  NULL, 'Large language models for general-purpose text generation'),
    ('Vision - OCR',      NULL, 'Optical character recognition and document understanding models'),
    ('Image Generation',  NULL, 'Text-to-image and image-to-image generation models'),
    ('Video Generation',  NULL, 'Text-to-video and video generation models')
ON CONFLICT DO NOTHING;

-- Seed architecture sub-categories
INSERT INTO public.model_category (name, parent_id, description) VALUES
    ('Transformer', (SELECT id FROM public.model_category WHERE name = 'LLM - Foundation' AND parent_id IS NULL),
     'Transformer-based large language models'),
    ('Transformer', (SELECT id FROM public.model_category WHERE name = 'Vision - OCR' AND parent_id IS NULL),
     'Transformer-based vision and OCR models'),
    ('Diffusion',   (SELECT id FROM public.model_category WHERE name = 'Image Generation' AND parent_id IS NULL),
     'Diffusion-based image generation models'),
    ('Diffusion',   (SELECT id FROM public.model_category WHERE name = 'Video Generation' AND parent_id IS NULL),
     'Diffusion-based video generation models')
ON CONFLICT DO NOTHING;

-- Seed model registry entries
INSERT INTO public.model_registry (repo_id, category_id, s3_prefix, display_name, description) VALUES
    ('deepseek-ai/DeepSeek-V3.2',
     (SELECT id FROM public.model_category WHERE name = 'Transformer'
      AND parent_id = (SELECT id FROM public.model_category WHERE name = 'LLM - Foundation' AND parent_id IS NULL)),
     'LLM - Foundation/Transformer/Deep-Seek',
     'DeepSeek V3.2',
     'DeepSeek foundation LLM v3.2'),
    ('deepseek-ai/DeepSeek-OCR-2',
     (SELECT id FROM public.model_category WHERE name = 'Transformer'
      AND parent_id = (SELECT id FROM public.model_category WHERE name = 'Vision - OCR' AND parent_id IS NULL)),
     'Vision - OCR/Transformer/Deep-Seek',
     'DeepSeek OCR 2',
     'DeepSeek multimodal OCR and document understanding model'),
    ('XLabs-AI/flux-RealismLora',
     (SELECT id FROM public.model_category WHERE name = 'Diffusion'
      AND parent_id = (SELECT id FROM public.model_category WHERE name = 'Image Generation' AND parent_id IS NULL)),
     'loras',
     'FLUX Realism LoRA',
     'LoRA adapter for FLUX realism style'),
    ('black-forest-labs/FLUX.1-schnell',
     (SELECT id FROM public.model_category WHERE name = 'Diffusion'
      AND parent_id = (SELECT id FROM public.model_category WHERE name = 'Image Generation' AND parent_id IS NULL)),
     'checkpoints',
     'FLUX.1 Schnell',
     'Fast FLUX.1 image generation checkpoint'),
    ('Wan-AI/Wan2.2-T2V-A14B',
     (SELECT id FROM public.model_category WHERE name = 'Diffusion'
      AND parent_id = (SELECT id FROM public.model_category WHERE name = 'Video Generation' AND parent_id IS NULL)),
     'Wan-AI',
     'Wan 2.2 T2V A14B',
     'Wan-AI text-to-video 14B parameter model')
ON CONFLICT (repo_id) DO NOTHING;
