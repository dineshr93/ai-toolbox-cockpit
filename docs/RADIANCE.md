# Standalone Radiance on R9700

Select **AMD Radeon AI PRO R9700 → Standalone Radiance** in Toolboxes and install the ROCm 10.1 image. Models and Server Mode use Radiance’s native `.rad` format, including its tokenizer, vision tower and bundled drafter. The separate **vLLM Radiance (legacy)** entry keeps its earlier checkpoint format and launch controls.

## Models and GPU layouts

| Native artifact | Download | GPU layout | Bundled decoding |
| --- | ---: | --- | --- |
| Qwen3.8-27B FP8 | 30.78 GB | 2 R9700s | DFlash2, 7 draft tokens |
| Qwen3.8-27B MXFP4 | 19.38 GB | 1 R9700 | DFlash2, 7 draft tokens |
| Qwen3.8-Flash-Next IQ4R | 121.97 GB | 4 R9700s | MTP, 3 draft tokens |

The model manager pins each repository revision and downloads into `~/models/radiance`. **Download / Repair** uses the saved Hugging Face authentication. **Scan Local** checks complete file sizes; acquisition integrity comes from the Hugging Face client. A model can also sit directly in the chosen models directory.

Flash Next keeps its 47.68 GiB n-gram table in pinned host RAM. Its selected profile passes `--ngram-placement ram`; allow about 54 GiB of available host RAM at startup, including loading headroom. The remaining model tensors use the four GPU pools. The download size is not the VRAM requirement.

## Start and stop

Choose the native model in Server Mode. Cockpit selects its qualified GPU count, FP8 KV cache, exact inter-GPU communication and GPU weight placement. Start with the default 8,192-token context and one concurrent session. The context field includes prompt and output tokens and is bounded at 67,840 for these profiles.

Select **Target only** or the model’s **Bundled draft** mode. Choose image input and thinking effort explicitly. For Qwen sampled thinking requests, use temperature 1.0, top-p 0.95, top-k 20 and min-p 0. Non-thinking requests use temperature 0.7, top-p 0.8, top-k 20, min-p 0 and presence penalty 1.5. Client request settings take precedence over server defaults.

**Start Radiance** shows the complete command for review, mounts only the selected model file read-only and binds the API to loopback by default. Ctrl+C stops the foreground server and returns to Cockpit. The API includes `/health`, `/v1/models`, `/v1/chat/completions`, `/v1/completions`, `/tokenize` and `/metrics`.

The source-built image uses the supplied ROCm compiler. See the [R9700 toolbox guide](https://github.com/kyuz0/amd-r9700-ai-toolboxes/blob/main/docs/radiance-rocm-10.1.md) for the pinned source, build workflow and measured profiles.
