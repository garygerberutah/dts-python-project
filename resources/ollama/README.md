./install.sh
ollama --version

GPU Acceleration (NVIDIA Users)
If you have an NVIDIA GPU, you should ensure that the NVIDIA Container Toolkit is installed within your WSL2 instance so Ollama can offload model weights to your VRAM.

Install the toolkit (if not already present):
Follow the official NVIDIA guide for Apt-based systems (Ubuntu/Debian).

Restart the Ollama service:

Bash
sudo systemctl restart ollama

ollama run nemotron-3-super
ollama run qwen3.5
ollama run qwen3-coder-next
ollama run kimi-k2.5:cloud


[
  {
    "model_name": "lfm2",
    "url": "https://huggingface.co/LiquidAI/LFM2.5-1.2B-Thinking/resolve/main/model.safetensors",
    "sha256": "112fba7db6c4544d9944002fcfe1c21e23e03d8fc0a0c7e2b6655de6c738583d", 
    "description": "LFM2 is a family of hybrid models designed for on-device deployment."
  },
  {
    "model_name": "nemotron-3-super",
    "url": "https://ollama.com/library/nemotron-3-super",
    "sha256": "95acc78b3ffd",
    "description": "NVIDIA Nemotron 3 Super is a 120B open MoE model."
  },
  {
    "model_name": "qwen3.5-9B",
    "url": ["https://huggingface.co/Qwen/Qwen3.5-9B/resolve/main/model.safetensors.index.json",
		"https://huggingface.co/Qwen/Qwen3.5-9B/resolve/main/model.safetensors-00001-of-00004.safetensors",
                "https://huggingface.co/Qwen/Qwen3.5-9B/resolve/main/model.safetensors-00002-of-00004.safetensors",
                "https://huggingface.co/Qwen/Qwen3.5-9B/resolve/main/model.safetensors-00003-of-00004.safetensors",
		"https://huggingface.co/Qwen/Qwen3.5-9B/resolve/main/model.safetensors-00004-of-00004.safetensors"],
    "sha256": ["26d3539b516be613f39563617cb9d33b3f83d401298125be392c80cefb8f7fe5",
                "db6f444b43d318c92f360a13a25561a6a65b10c0631b8ed305a426dbaa6c380e",
                "31c7d7e2dd5d207840b31cc59083c8f4c4718959149e0358c0364052bb9a0330",
		"7ec36ba3a4176a44c3c0876ad80c56a2f70c84bf008d82e9501df642f17dadec",
		"b62b0c4cd7e44edee103ee8f4fe225f246d5e768e07bfd5f25b63a8aa1fdd0c6"],
    "description": "Qwen 3.5 is a family of open-source multimodal models."
  },
  {
    "model_name": "glm-5",
    "url": "https://ollama.com/library/glm-5",
    "sha256": "",
    "description": "A strong reasoning and agentic model from Z.ai with 744B total parameters."
  },
  {
    "model_name": "minimax-m2.5",
    "url": "https://ollama.com/library/minimax-m2.5",
    "sha256": "c0d5751c800f",
    "description": "State-of-the-art large language model designed for productivity and coding."
  },
  {
    "model_name": "qwen3-coder-next",
    "url": "https://ollama.com/library/qwen3-coder-next",
    "sha256": "",
    "description": "Coding-focused language model optimized for agentic workflows."
  },
  {
    "model_name": "glm-ocr",
    "url": "https://ollama.com/library/glm-ocr",
    "sha256": "6effedd0dc8a",
    "description": "Multimodal OCR model for complex document understanding."
  },
  {
    "model_name": "kimi-k2.5",
    "url": "https://ollama.com/library/kimi-k2.5",
    "sha256": "6d1c3246c608",
    "description": "Open-source, native multimodal agentic model."
  },
  {
    "model_name": "lfm2.5-thinking",
    "url": "https://ollama.com/library/lfm2.5-thinking",
    "sha256": "",
    "description": "New family of hybrid models designed for on-device deployment."
  },
  {
    "model_name": "glm-4.7-flash",
    "url": "https://ollama.com/library/glm-4.7-flash",
    "sha256": "",
    "description": "Strongest model in the 30B class for lightweight deployment."
  }
]
