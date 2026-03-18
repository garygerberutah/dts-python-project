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
    ('Video Generation',  NULL, 'Text-to-video and video generation models'),
    ('LLM - Code',        NULL, 'Large language models specialized for code generation'),
    ('NLP - Translation', NULL, 'Natural language translation models'),
    ('Embedding',         NULL, 'Embedding models for vector representations')
ON CONFLICT DO NOTHING;

-- Seed architecture sub-categories
INSERT INTO public.model_category (name, parent_id, description) VALUES
    ('Transformer', (SELECT id FROM public.model_category WHERE name = 'LLM - Foundation' AND parent_id IS NULL),
     'Transformer-based large language models'),
    ('MoE',         (SELECT id FROM public.model_category WHERE name = 'LLM - Foundation' AND parent_id IS NULL),
     'Mixture-of-experts large language models'),
    ('Hybrid',      (SELECT id FROM public.model_category WHERE name = 'LLM - Foundation' AND parent_id IS NULL),
     'Hybrid-architecture language models (e.g. Liquid Foundation Models)'),
    ('Transformer', (SELECT id FROM public.model_category WHERE name = 'Vision - OCR' AND parent_id IS NULL),
     'Transformer-based vision and OCR models'),
    ('Diffusion',   (SELECT id FROM public.model_category WHERE name = 'Image Generation' AND parent_id IS NULL),
     'Diffusion-based image generation models'),
    ('Diffusion',   (SELECT id FROM public.model_category WHERE name = 'Video Generation' AND parent_id IS NULL),
     'Diffusion-based video generation models'),
    ('Transformer', (SELECT id FROM public.model_category WHERE name = 'LLM - Code' AND parent_id IS NULL),
     'Transformer-based code generation models'),
    ('Transformer', (SELECT id FROM public.model_category WHERE name = 'NLP - Translation' AND parent_id IS NULL),
     'Transformer-based translation models'),
    ('Multimodal',  (SELECT id FROM public.model_category WHERE name = 'Embedding' AND parent_id IS NULL),
     'Multimodal embedding models'),
    ('Code',        (SELECT id FROM public.model_category WHERE name = 'Embedding' AND parent_id IS NULL),
     'Code embedding and retrieval models')
ON CONFLICT DO NOTHING;

-- Helper function-like aliases for readability in INSERT below
-- LLM - Foundation sub-categories
-- Seed model registry entries
INSERT INTO public.model_registry (repo_id, category_id, s3_prefix, display_name, description) VALUES
    -- Image Generation / Diffusion
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
    -- Video Generation / Diffusion
    ('Wan-AI/Wan2.2-T2V-A14B',
     (SELECT id FROM public.model_category WHERE name = 'Diffusion'
      AND parent_id = (SELECT id FROM public.model_category WHERE name = 'Video Generation' AND parent_id IS NULL)),
     'Wan-AI',
     'Wan 2.2 T2V A14B',
     'Wan-AI text-to-video 14B parameter model'),
    -- LLM - Foundation / Transformer
    ('deepseek-ai/DeepSeek-V3.2',
     (SELECT id FROM public.model_category WHERE name = 'Transformer'
      AND parent_id = (SELECT id FROM public.model_category WHERE name = 'LLM - Foundation' AND parent_id IS NULL)),
     'LLM - Foundation/Transformer/deepseek-ai/DeepSeek-V3.2',
     'DeepSeek V3.2',
     'DeepSeek foundation LLM v3.2'),
    ('deepseek-ai/DeepSeek-V3.2-Speciale',
     (SELECT id FROM public.model_category WHERE name = 'Transformer'
      AND parent_id = (SELECT id FROM public.model_category WHERE name = 'LLM - Foundation' AND parent_id IS NULL)),
     'LLM - Foundation/Transformer/deepseek-ai',
     'DeepSeek V3.2 Speciale',
     'DeepSeek V3.2 Speciale variant foundation LLM'),
    ('huihui-ai/Huihui-Qwen3.5-4B-Claude-4.6-Opus-abliterated',
     (SELECT id FROM public.model_category WHERE name = 'Transformer'
      AND parent_id = (SELECT id FROM public.model_category WHERE name = 'LLM - Foundation' AND parent_id IS NULL)),
     'LLM - Foundation/Transformer/huihui-ai',
     'Huihui Qwen3.5 4B Claude Opus Abliterated',
     'Abliterated Qwen3.5 4B dense model fine-tuned on Claude Opus'),
    ('zai-org/GLM-5',
     (SELECT id FROM public.model_category WHERE name = 'Transformer'
      AND parent_id = (SELECT id FROM public.model_category WHERE name = 'LLM - Foundation' AND parent_id IS NULL)),
     'LLM - Foundation/Transformer/zai-org',
     'GLM-5',
     'General Language Model 5 by Zhipu AI'),
    ('zai-org/GLM-5-FP8',
     (SELECT id FROM public.model_category WHERE name = 'Transformer'
      AND parent_id = (SELECT id FROM public.model_category WHERE name = 'LLM - Foundation' AND parent_id IS NULL)),
     'LLM - Foundation/Transformer/zai-org',
     'GLM-5 FP8',
     'General Language Model 5 FP8 precision by Zhipu AI'),
    -- LLM - Foundation / MoE
    ('huihui-ai/Huihui-Qwen3.5-35B-A3B-abliterated',
     (SELECT id FROM public.model_category WHERE name = 'MoE'
      AND parent_id = (SELECT id FROM public.model_category WHERE name = 'LLM - Foundation' AND parent_id IS NULL)),
     'LLM - Foundation/MoE/huihui-ai',
     'Huihui Qwen3.5 35B-A3B Abliterated',
     'Abliterated Qwen3.5 35B MoE with 3B active parameters'),
    ('huihui-ai/Huihui-Qwen3.5-35B-A3B-Claude-4.6-Opus-abliterated',
     (SELECT id FROM public.model_category WHERE name = 'MoE'
      AND parent_id = (SELECT id FROM public.model_category WHERE name = 'LLM - Foundation' AND parent_id IS NULL)),
     'LLM - Foundation/MoE/huihui-ai',
     'Huihui Qwen3.5 35B-A3B Claude Opus Abliterated',
     'Abliterated Qwen3.5 35B MoE fine-tuned on Claude Opus'),
    ('huihui-ai/Huihui-Qwen3.5-122B-A10B-abliterated-GGUF',
     (SELECT id FROM public.model_category WHERE name = 'MoE'
      AND parent_id = (SELECT id FROM public.model_category WHERE name = 'LLM - Foundation' AND parent_id IS NULL)),
     'LLM - Foundation/MoE/huihui-ai',
     'Huihui Qwen3.5 122B-A10B Abliterated GGUF',
     'Abliterated Qwen3.5 122B MoE GGUF quantized, 10B active'),
    ('ox-ox/MiniMax-M2.5-GGUF',
     (SELECT id FROM public.model_category WHERE name = 'MoE'
      AND parent_id = (SELECT id FROM public.model_category WHERE name = 'LLM - Foundation' AND parent_id IS NULL)),
     'LLM - Foundation/MoE/ox-ox',
     'MiniMax M2.5 GGUF',
     'MiniMax M2.5 MoE model in GGUF format'),
    ('tomngdev/MiniMax-M2.5-REAP-139B-A10B-GGUF',
     (SELECT id FROM public.model_category WHERE name = 'MoE'
      AND parent_id = (SELECT id FROM public.model_category WHERE name = 'LLM - Foundation' AND parent_id IS NULL)),
     'LLM - Foundation/MoE/tomngdev',
     'MiniMax M2.5 REAP 139B-A10B GGUF',
     'MiniMax M2.5 REAP 139B MoE GGUF quantized, 10B active'),
    ('nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-BF16',
     (SELECT id FROM public.model_category WHERE name = 'MoE'
      AND parent_id = (SELECT id FROM public.model_category WHERE name = 'LLM - Foundation' AND parent_id IS NULL)),
     'LLM - Foundation/MoE/nvidia',
     'NVIDIA Nemotron 3 Super 120B-A12B BF16',
     'NVIDIA Nemotron 3 Super 120B MoE BF16 precision, 12B active'),
    ('nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-FP8',
     (SELECT id FROM public.model_category WHERE name = 'MoE'
      AND parent_id = (SELECT id FROM public.model_category WHERE name = 'LLM - Foundation' AND parent_id IS NULL)),
     'LLM - Foundation/MoE/nvidia',
     'NVIDIA Nemotron 3 Super 120B-A12B FP8',
     'NVIDIA Nemotron 3 Super 120B MoE FP8 precision, 12B active'),
    ('nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-NVFP4',
     (SELECT id FROM public.model_category WHERE name = 'MoE'
      AND parent_id = (SELECT id FROM public.model_category WHERE name = 'LLM - Foundation' AND parent_id IS NULL)),
     'LLM - Foundation/MoE/nvidia',
     'NVIDIA Nemotron 3 Super 120B-A12B NVFP4',
     'NVIDIA Nemotron 3 Super 120B MoE NVFP4 precision, 12B active'),
    -- LLM - Foundation / Hybrid
    ('huihui-ai/Huihui-LFM2-24B-A2B-abliterated',
     (SELECT id FROM public.model_category WHERE name = 'Hybrid'
      AND parent_id = (SELECT id FROM public.model_category WHERE name = 'LLM - Foundation' AND parent_id IS NULL)),
     'LLM - Foundation/Hybrid/huihui-ai',
     'Huihui LFM2 24B-A2B Abliterated',
     'Abliterated Liquid Foundation Model 2, 24B with 2B active'),
    ('LiquidAI/LFM2.5-1.2B-Thinking',
     (SELECT id FROM public.model_category WHERE name = 'Hybrid'
      AND parent_id = (SELECT id FROM public.model_category WHERE name = 'LLM - Foundation' AND parent_id IS NULL)),
     'LLM - Foundation/Hybrid/LiquidAI',
     'LFM 2.5 1.2B Thinking',
     'Liquid Foundation Model 2.5 1.2B with chain-of-thought'),
    ('LiquidAI/LFM2.5-1.2B-Instruct',
     (SELECT id FROM public.model_category WHERE name = 'Hybrid'
      AND parent_id = (SELECT id FROM public.model_category WHERE name = 'LLM - Foundation' AND parent_id IS NULL)),
     'LLM - Foundation/Hybrid/LiquidAI',
     'LFM 2.5 1.2B Instruct',
     'Liquid Foundation Model 2.5 1.2B instruction-tuned'),
    ('LiquidAI/LFM2.5-1.2B-JP',
     (SELECT id FROM public.model_category WHERE name = 'Hybrid'
      AND parent_id = (SELECT id FROM public.model_category WHERE name = 'LLM - Foundation' AND parent_id IS NULL)),
     'LLM - Foundation/Hybrid/LiquidAI',
     'LFM 2.5 1.2B JP',
     'Liquid Foundation Model 2.5 1.2B Japanese language'),
    -- Vision - OCR / Transformer
    ('deepseek-ai/DeepSeek-OCR-2',
     (SELECT id FROM public.model_category WHERE name = 'Transformer'
      AND parent_id = (SELECT id FROM public.model_category WHERE name = 'Vision - OCR' AND parent_id IS NULL)),
     'Vision - OCR/Transformer/deepseek-ai/DeepSeek-OCR-2',
     'DeepSeek OCR 2',
     'DeepSeek multimodal OCR and document understanding model'),
    ('zai-org/GLM-OCR',
     (SELECT id FROM public.model_category WHERE name = 'Transformer'
      AND parent_id = (SELECT id FROM public.model_category WHERE name = 'Vision - OCR' AND parent_id IS NULL)),
     'Vision - OCR/Transformer/zai-org',
     'GLM-OCR',
     'General Language Model OCR by Zhipu AI'),
    -- LLM - Code / Transformer
    ('Qwen/Qwen3-Coder-Next',
     (SELECT id FROM public.model_category WHERE name = 'Transformer'
      AND parent_id = (SELECT id FROM public.model_category WHERE name = 'LLM - Code' AND parent_id IS NULL)),
     'LLM - Code/Transformer/Qwen',
     'Qwen3 Coder Next',
     'Qwen3 code generation model'),
    ('Qwen/Qwen3-Coder-Next-FP8',
     (SELECT id FROM public.model_category WHERE name = 'Transformer'
      AND parent_id = (SELECT id FROM public.model_category WHERE name = 'LLM - Code' AND parent_id IS NULL)),
     'LLM - Code/Transformer/Qwen',
     'Qwen3 Coder Next FP8',
     'Qwen3 code generation model FP8 precision'),
    ('Qwen/Qwen3-Coder-Next-GGUF',
     (SELECT id FROM public.model_category WHERE name = 'Transformer'
      AND parent_id = (SELECT id FROM public.model_category WHERE name = 'LLM - Code' AND parent_id IS NULL)),
     'LLM - Code/Transformer/Qwen',
     'Qwen3 Coder Next GGUF',
     'Qwen3 code generation model GGUF quantized'),
    -- NLP - Translation / Transformer
    ('google/translategemma-27b-it',
     (SELECT id FROM public.model_category WHERE name = 'Transformer'
      AND parent_id = (SELECT id FROM public.model_category WHERE name = 'NLP - Translation' AND parent_id IS NULL)),
     'NLP - Translation/Transformer/google',
     'TranslateGemma 27B IT',
     'Google TranslateGemma 27B instruction-tuned translation model'),
    ('google/translategemma-4b-it',
     (SELECT id FROM public.model_category WHERE name = 'Transformer'
      AND parent_id = (SELECT id FROM public.model_category WHERE name = 'NLP - Translation' AND parent_id IS NULL)),
     'NLP - Translation/Transformer/google',
     'TranslateGemma 4B IT',
     'Google TranslateGemma 4B instruction-tuned translation model'),
    ('google/translategemma-12b-it',
     (SELECT id FROM public.model_category WHERE name = 'Transformer'
      AND parent_id = (SELECT id FROM public.model_category WHERE name = 'NLP - Translation' AND parent_id IS NULL)),
     'NLP - Translation/Transformer/google',
     'TranslateGemma 12B IT',
     'Google TranslateGemma 12B instruction-tuned translation model'),
    -- Embedding / Multimodal
    ('nomic-ai/colnomic-embed-multimodal-7b',
     (SELECT id FROM public.model_category WHERE name = 'Multimodal'
      AND parent_id = (SELECT id FROM public.model_category WHERE name = 'Embedding' AND parent_id IS NULL)),
     'Embedding/Multimodal/nomic-ai',
     'ColNomic Embed Multimodal 7B',
     'Nomic AI columnar multimodal embedding model 7B'),
    ('nomic-ai/nomic-embed-multimodal-7b',
     (SELECT id FROM public.model_category WHERE name = 'Multimodal'
      AND parent_id = (SELECT id FROM public.model_category WHERE name = 'Embedding' AND parent_id IS NULL)),
     'Embedding/Multimodal/nomic-ai',
     'Nomic Embed Multimodal 7B',
     'Nomic AI multimodal embedding model 7B'),
    ('nomic-ai/colnomic-embed-multimodal-3b',
     (SELECT id FROM public.model_category WHERE name = 'Multimodal'
      AND parent_id = (SELECT id FROM public.model_category WHERE name = 'Embedding' AND parent_id IS NULL)),
     'Embedding/Multimodal/nomic-ai',
     'ColNomic Embed Multimodal 3B',
     'Nomic AI columnar multimodal embedding model 3B'),
    ('nomic-ai/nomic-embed-multimodal-3b',
     (SELECT id FROM public.model_category WHERE name = 'Multimodal'
      AND parent_id = (SELECT id FROM public.model_category WHERE name = 'Embedding' AND parent_id IS NULL)),
     'Embedding/Multimodal/nomic-ai',
     'Nomic Embed Multimodal 3B',
     'Nomic AI multimodal embedding model 3B'),
    -- Embedding / Code
    ('nomic-ai/nomic-embed-code',
     (SELECT id FROM public.model_category WHERE name = 'Code'
      AND parent_id = (SELECT id FROM public.model_category WHERE name = 'Embedding' AND parent_id IS NULL)),
     'Embedding/Code/nomic-ai',
     'Nomic Embed Code',
     'Nomic AI code embedding model'),
    ('nomic-ai/CodeRankEmbed',
     (SELECT id FROM public.model_category WHERE name = 'Code'
      AND parent_id = (SELECT id FROM public.model_category WHERE name = 'Embedding' AND parent_id IS NULL)),
     'Embedding/Code/nomic-ai',
     'CodeRank Embed',
     'Nomic AI code ranking embedding model'),
    ('nomic-ai/CodeRankLLM',
     (SELECT id FROM public.model_category WHERE name = 'Code'
      AND parent_id = (SELECT id FROM public.model_category WHERE name = 'Embedding' AND parent_id IS NULL)),
     'Embedding/Code/nomic-ai',
     'CodeRank LLM',
     'Nomic AI code ranking LLM for retrieval')
ON CONFLICT (repo_id) DO NOTHING;
