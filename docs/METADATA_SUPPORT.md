# 图片属性与节点支持清单

由 `python scripts/metadata_support.py --write` 从节点注册表生成。

解析版本：3；契约快照：1013 个节点；登记适配：378 个节点。

## 适配基线

| 来源 | 版本 / 源码指纹 |
|---|---|
| ComfyUI | `0.37.0` |
| ComfyUI-GGUF | `{"version": "1.1.10", "python_source_sha256": "c8df7448b8a02243e3b66c95851cc9d71494320a377106ac7f913e0a1305ffb0"}` |
| comfyui-krea2-text-encoder | `{"version": "1.0.6", "python_source_sha256": "f8ce6ffaa8d1630bdb6d0dfd98b7818cefbb247c6a479ad575e639f6346b80b7"}` |
| comfyui-lora-manager | `{"version": "1.2.1", "python_source_sha256": "772f7e5dfc68ec6d43064bdf959f9872e7189cd82ffc9f9870d1edcd454f3ccb"}` |
| rgthree-comfy | `{"version": "1.0.2608210019", "python_source_sha256": "3c87dee2d807ea11c34549c89f5bbe5215095569eb1655bf005faa1af809119a"}` |

扩展以安装包发布版本及 Python 源码 SHA-256 标识；运行时使用项目内冻结规则。

## 数据与展示约定

- 读取 PNG 文本、APNG comf 块、WebP EXIF 中的执行图。其他现有图片格式显示基础信息和封装支持状态。
- 值区分已记录、确定性推导、未知；每项保留节点、字段和传递来源。
- 正反向由条件连接用途确定；多输出关联未确定时旧提示词摘要为空。
- 采样种子属于采样节点；批量工作流的单张图片种子以保存证据为准。
- 图内资源名表示执行图配置；外部模型内容、输入图片像素、通配词库和运行时选择结果由未知状态说明。
- 模型与采样资源沿各自端口追踪；注册之外的节点返回局部诊断。

## 属性 → 节点

| 属性 | 标识 | 直接适配节点（传递节点见下表） |
|---|---|---|
| 正向提示词 | `positive` | `BasicGuider`, `CFGGuider`, `CLIPTextEncode`, `CLIPTextEncodeControlnet`, `CLIPTextEncodeFlux`, `CLIPTextEncodeHiDream`, `CLIPTextEncodeHunyuanDiT`, `CLIPTextEncodeKandinsky5`, `CLIPTextEncodeLumina2`, `CLIPTextEncodePixArtAlpha`, `CLIPTextEncodeSD3`, `CLIPTextEncodeSDXL`, `CLIPTextEncodeSDXLRefiner`, `DualCFGGuider`, `DualModelGuider`, `KSampler`, `KSamplerAdvanced`, `PerpNegGuider`, `Power Prompt (rgthree)`, `Power Prompt - Simple (rgthree)`, `Prompt (LoraManager)`, `SDXL Power Prompt - Positive (rgthree)`, `SDXL Power Prompt - Simple / Negative (rgthree)`, `SamplerCustom`, `SamplerCustomAdvanced`, `TextEncodeBooguEdit`, `TextEncodeJoyImageEdit`, `TextEncodeKrea2`, `TextEncodeMageFlowEdit`, `TextEncodeQwenImage21`, `TextEncodeQwenImageEdit`, `TextEncodeQwenImageEditPlus`, `TextEncodeZImageOmni` |
| 反向提示词 | `negative` | `BasicGuider`, `CFGGuider`, `CLIPTextEncode`, `CLIPTextEncodeControlnet`, `CLIPTextEncodeFlux`, `CLIPTextEncodeHiDream`, `CLIPTextEncodeHunyuanDiT`, `CLIPTextEncodeKandinsky5`, `CLIPTextEncodeLumina2`, `CLIPTextEncodePixArtAlpha`, `CLIPTextEncodeSD3`, `CLIPTextEncodeSDXL`, `CLIPTextEncodeSDXLRefiner`, `DualCFGGuider`, `DualModelGuider`, `KSampler`, `KSamplerAdvanced`, `PerpNegGuider`, `Power Prompt (rgthree)`, `Power Prompt - Simple (rgthree)`, `Prompt (LoraManager)`, `SDXL Power Prompt - Positive (rgthree)`, `SDXL Power Prompt - Simple / Negative (rgthree)`, `SamplerCustom`, `SamplerCustomAdvanced`, `TextEncodeBooguEdit`, `TextEncodeJoyImageEdit`, `TextEncodeKrea2`, `TextEncodeMageFlowEdit`, `TextEncodeQwenImage21`, `TextEncodeQwenImageEdit`, `TextEncodeQwenImageEditPlus`, `TextEncodeZImageOmni` |
| 系统提示词 | `system_prompt` | `BasicGuider`, `CFGGuider`, `CLIPTextEncode`, `CLIPTextEncodeControlnet`, `CLIPTextEncodeFlux`, `CLIPTextEncodeHiDream`, `CLIPTextEncodeHunyuanDiT`, `CLIPTextEncodeKandinsky5`, `CLIPTextEncodeLumina2`, `CLIPTextEncodePixArtAlpha`, `CLIPTextEncodeSD3`, `CLIPTextEncodeSDXL`, `CLIPTextEncodeSDXLRefiner`, `DualCFGGuider`, `DualModelGuider`, `PerpNegGuider`, `Power Prompt (rgthree)`, `Power Prompt - Simple (rgthree)`, `Prompt (LoraManager)`, `SDXL Power Prompt - Positive (rgthree)`, `SDXL Power Prompt - Simple / Negative (rgthree)`, `TextEncodeBooguEdit`, `TextEncodeJoyImageEdit`, `TextEncodeKrea2`, `TextEncodeMageFlowEdit`, `TextEncodeQwenImage21`, `TextEncodeQwenImageEdit`, `TextEncodeQwenImageEditPlus`, `TextEncodeZImageOmni` |
| 未归属提示词 | `unassigned` |  |
| 条件处理 | `conditioning` |  |
| 主模型 | `model` | `Checkpoint Loader (LoraManager)`, `CheckpointLoader`, `CheckpointLoaderSimple`, `DiffusersLoader`, `ImageOnlyCheckpointLoader`, `KSampler`, `KSamplerAdvanced`, `Random Checkpoint Loader (LoraManager)`, `Random Unet Loader (LoraManager)`, `SamplerCustom`, `SamplerCustomAdvanced`, `UNETLoader`, `Unet Loader (LoraManager)`, `UnetLoaderGGUF`, `UnetLoaderGGUFAdvanced`, `unCLIPCheckpointLoader` |
| 文本编码器 | `clip` | `BasicGuider`, `CFGGuider`, `CLIPLoader`, `CLIPLoaderGGUF`, `CLIPTextEncode`, `CLIPTextEncodeControlnet`, `CLIPTextEncodeFlux`, `CLIPTextEncodeHiDream`, `CLIPTextEncodeHunyuanDiT`, `CLIPTextEncodeKandinsky5`, `CLIPTextEncodeLumina2`, `CLIPTextEncodePixArtAlpha`, `CLIPTextEncodeSD3`, `CLIPTextEncodeSDXL`, `CLIPTextEncodeSDXLRefiner`, `Checkpoint Loader (LoraManager)`, `CheckpointLoader`, `CheckpointLoaderSimple`, `DiffusersLoader`, `DualCFGGuider`, `DualCLIPLoader`, `DualCLIPLoaderGGUF`, `DualModelGuider`, `ImageOnlyCheckpointLoader`, `PerpNegGuider`, `Power Prompt (rgthree)`, `Power Prompt - Simple (rgthree)`, `Prompt (LoraManager)`, `QuadrupleCLIPLoader`, `QuadrupleCLIPLoaderGGUF`, `Random Checkpoint Loader (LoraManager)`, `SDXL Power Prompt - Positive (rgthree)`, `SDXL Power Prompt - Simple / Negative (rgthree)`, `TextEncodeBooguEdit`, `TextEncodeJoyImageEdit`, `TextEncodeKrea2`, `TextEncodeMageFlowEdit`, `TextEncodeQwenImage21`, `TextEncodeQwenImageEdit`, `TextEncodeQwenImageEditPlus`, `TextEncodeZImageOmni`, `TripleCLIPLoader`, `TripleCLIPLoaderGGUF`, `unCLIPCheckpointLoader` |
| 变分自编码器 | `vae` | `Checkpoint Loader (LoraManager)`, `CheckpointLoader`, `CheckpointLoaderSimple`, `DiffusersLoader`, `ImageOnlyCheckpointLoader`, `Random Checkpoint Loader (LoraManager)`, `VAELoader`, `unCLIPCheckpointLoader` |
| LoRA 及权重 | `lora` | `Create Hook LoRA (LoraManager)`, `CreateHookLora`, `CreateHookLoraModelOnly`, `LoRA Text Loader (LoraManager)`, `Lora Cycler (LoraManager)`, `Lora Loader (LoraManager)`, `Lora Loader Stack (rgthree)`, `Lora Randomizer (LoraManager)`, `Lora Stack Combiner (LoraManager)`, `Lora Stacker (LoraManager)`, `LoraLoader`, `LoraLoaderBypass`, `LoraLoaderBypassModelOnly`, `LoraLoaderModelOnly`, `LoraModelLoader`, `Power Lora Loader (rgthree)` |
| 模型与编码器设置 | `model_settings` | `APG`, `AnimaLLLiteApply`, `BlockSparseAttention`, `CFGNorm`, `CFGOverride`, `CFGZeroStar`, `CLIPAttentionMultiply`, `CLIPMergeAdd`, `CLIPMergeSimple`, `CLIPMergeSubtract`, `CLIPSetLastLayer`, `ChromaRadianceOptions`, `ContextWindowsManual`, `DifferentialDiffusion`, `EasyCache`, `Epsilon Scaling`, `FluxKVCache`, `FreSca`, `FreeU`, `FreeU_V2`, `HiDreamO1PatchSeamSmoothing`, `HyperTile`, `HypernetworkLoader`, `LTXVContextWindows`, `LTXVModalityGuidance`, `LTXVSpatioTemporalGuidance`, `LatentApplyOperationCFG`, `LazyCache`, `Mahiro`, `MiniMaxH3SigmaShift`, `ModelAttentionBackend`, `ModelComputeDtype`, `ModelMergeAdd`, `ModelMergeAuraflow`, `ModelMergeBlocks`, `ModelMergeCosmos14B`, `ModelMergeCosmos7B`, `ModelMergeCosmosPredict2_14B`, `ModelMergeCosmosPredict2_2B`, `ModelMergeFlux1`, `ModelMergeKrea2`, `ModelMergeLTXV`, `ModelMergeMochiPreview`, `ModelMergeQwenImage`, `ModelMergeSD1`, `ModelMergeSD2`, `ModelMergeSD35_Large`, `ModelMergeSD3_2B`, `ModelMergeSDXL`, `ModelMergeSimple`, `ModelMergeSubtract`, `ModelMergeWAN2_1`, `ModelNoiseScale`, `ModelSamplingAuraFlow`, `ModelSamplingContinuousEDM`, `ModelSamplingContinuousV`, `ModelSamplingDiscrete`, `ModelSamplingFlux`, `ModelSamplingLTXV`, `ModelSamplingSD3`, `ModelSamplingStableCascade`, `MultiGPU_WorkUnits`, `NAGuidance`, `PatchModelAddDownscale`, `PerpNeg`, `PerturbedAttentionGuidance`, `QwenImage21Cache`, `RenormCFG`, `RescaleCFG`, `SUPIRApply`, `ScaleROPE`, `SelectCLIPDevice`, `SelectModelDevice`, `SelectVAEDevice`, `SelfAttentionGuidance`, `SenseNovaSamplingOptions`, `SetClipHooks`, `SkipLayerGuidanceDiT`, `SkipLayerGuidanceDiTSimple`, `SkipLayerGuidanceSD3`, `T5TokenizerOptions`, `TCFG`, `TemporalScoreRescaling`, `TomePatchModel`, `TorchCompileModel`, `TripoSplatSamplingPreview`, `UNetCrossAttentionMultiply`, `UNetSelfAttentionMultiply`, `UNetTemporalAttentionMultiply`, `USOStyleReference`, `VideoLinearCFGGuidance`, `VideoTriangleCFGGuidance`, `WanAnimate2Cache`, `WanContextWindowsManual`, `wanBlockSwap` |
| 采样种子 | `seed` | `Context (rgthree)`, `Context Big (rgthree)`, `ImageAddNoise`, `KSampler`, `KSamplerAdvanced`, `Prompt (LoraManager)`, `RandomNoise`, `SamplerCustom`, `Seed (rgthree)`, `Text (LoraManager)` |
| 配置步数 | `steps` | `AlignYourStepsScheduler`, `BasicScheduler`, `BetaSamplingScheduler`, `Context Big (rgthree)`, `ExponentialScheduler`, `ExtendIntermediateSigmas`, `Flux2Scheduler`, `GITSScheduler`, `Ideogram4Scheduler`, `KSampler`, `KSampler Config (rgthree)`, `KSamplerAdvanced`, `KarrasScheduler`, `LaplaceScheduler`, `OptimalStepsScheduler`, `PolyexponentialScheduler`, `SDTurboScheduler`, `VPScheduler` |
| 阶段步数 | `stage_steps` | `KSampler`, `KSamplerAdvanced`, `SamplerCustom`, `SamplerCustomAdvanced` |
| 采样器 | `sampler` | `KSampler`, `KSampler Config (rgthree)`, `KSamplerAdvanced`, `KSamplerSelect`, `SamplerDPMAdaptative`, `SamplerDPMPP_2M_SDE`, `SamplerDPMPP_2S_Ancestral`, `SamplerDPMPP_3M_SDE`, `SamplerDPMPP_SDE`, `SamplerER_SDE`, `SamplerEulerAncestral`, `SamplerEulerAncestralCFGPP`, `SamplerEulerCFGpp`, `SamplerLCM`, `SamplerLCMUpscale`, `SamplerLMS`, `SamplerSASolver`, `SamplerSEEDS2` |
| 调度器 | `scheduler` | `AlignYourStepsScheduler`, `BasicScheduler`, `BetaSamplingScheduler`, `Context Big (rgthree)`, `ExponentialScheduler`, `Flux2Scheduler`, `GITSScheduler`, `Ideogram4Scheduler`, `KSampler`, `KSampler Config (rgthree)`, `KSamplerAdvanced`, `KarrasScheduler`, `LaplaceScheduler`, `OptimalStepsScheduler`, `PolyexponentialScheduler`, `SDTurboScheduler`, `VPScheduler` |
| CFG 引导强度 | `cfg` | `CFGGuider`, `CFGOverride`, `Context Big (rgthree)`, `DualCFGGuider`, `DualModelGuider`, `KSampler`, `KSampler Config (rgthree)`, `KSamplerAdvanced`, `PerpNegGuider`, `SamplerCustom` |
| 模型引导强度 | `guidance` | `CLIPTextEncodeFlux`, `FluxGuidance` |
| 降噪 | `denoise` | `AlignYourStepsScheduler`, `BasicScheduler`, `GITSScheduler`, `KSampler`, `OptimalStepsScheduler`, `SDTurboScheduler`, `SplitSigmasDenoise` |
| 起始步数 | `start_at_step` | `KSamplerAdvanced` |
| 结束步数 | `end_at_step` | `KSamplerAdvanced` |
| 添加噪声 | `add_noise` | `KSamplerAdvanced`, `SamplerCustom` |
| 保留剩余噪声 | `return_with_leftover_noise` | `KSamplerAdvanced` |
| 采样与噪声设置 | `sampling_settings` |  |
| 生成宽度 | `width` | `ConditioningSetArea`, `ConditioningSetAreaPercentage`, `ConditioningSetAreaPercentageVideo`, `EmptyFlux2LatentImage`, `EmptyHunyuanImageLatent`, `EmptyImage`, `EmptyLatentImage`, `EmptyQwenImageLayeredLatentImage`, `EmptySD3LatentImage`, `GLIGENTextBoxApply`, `Image Resize (rgthree)`, `ImageCrop`, `ImageScale`, `KSampler`, `KSamplerAdvanced`, `LatentCrop`, `LatentUpscale`, `ModelSamplingFlux`, `SamplerCustom`, `SamplerCustomAdvanced`, `StableCascade_EmptyLatentImage`, `StableZero123_Conditioning` |
| 生成高度 | `height` | `ConditioningSetArea`, `ConditioningSetAreaPercentage`, `ConditioningSetAreaPercentageVideo`, `EmptyFlux2LatentImage`, `EmptyHunyuanImageLatent`, `EmptyImage`, `EmptyLatentImage`, `EmptyQwenImageLayeredLatentImage`, `EmptySD3LatentImage`, `GLIGENTextBoxApply`, `Image Resize (rgthree)`, `ImageCrop`, `ImageScale`, `KSampler`, `KSamplerAdvanced`, `LatentCrop`, `LatentUpscale`, `ModelSamplingFlux`, `SamplerCustom`, `SamplerCustomAdvanced`, `StableCascade_EmptyLatentImage`, `StableZero123_Conditioning` |
| 批量大小 | `batch_size` | `EmptyFlux2LatentImage`, `EmptyHunyuanImageLatent`, `EmptyImage`, `EmptyLatentImage`, `EmptyQwenImageLayeredLatentImage`, `EmptySD3LatentImage`, `KSampler`, `KSamplerAdvanced`, `RebatchLatents`, `SDXL Empty Latent Image (rgthree)`, `SamplerCustom`, `SamplerCustomAdvanced`, `StableCascade_EmptyLatentImage`, `StableZero123_Conditioning`, `TextEncodeMageFlowEdit` |
| ControlNet | `controlnet` | `ControlNetLoader`, `DiffControlNetLoader` |
| 控制条件设置 | `control_settings` | `ConditioningAverage`, `ConditioningCombine`, `ConditioningConcat`, `ConditioningMultiply`, `ConditioningSetArea`, `ConditioningSetAreaPercentage`, `ConditioningSetAreaPercentageVideo`, `ConditioningSetAreaStrength`, `ConditioningSetDefaultCombine`, `ConditioningSetMask`, `ConditioningSetProperties`, `ConditioningSetPropertiesAndCombine`, `ConditioningSetTimestepRange`, `ConditioningTimestepsRange`, `ConditioningZeroOut`, `ControlNetApply`, `ControlNetApplyAdvanced`, `ControlNetApplySD3`, `ControlNetInpaintingAliMamaApply`, `InpaintModelConditioning`, `InstructPixToPixConditioning`, `MiniMaxH3FunControlNetApply`, `PairConditioningCombine`, `PairConditioningSetDefaultCombine`, `PairConditioningSetProperties`, `PairConditioningSetPropertiesAndCombine`, `PiDConditioning`, `QwenImageDiffsynthControlnet`, `SD_4XUpscale_Conditioning`, `SaveConditioning`, `SetUnionControlNetType`, `StableCascade_StageB_Conditioning`, `StableZero123_Conditioning`, `WanUni3CControlnetApply`, `ZImageFunControlnet`, `unCLIPConditioning` |
| 放大模型 | `upscale_model` | `LatentUpscaleModelLoader`, `UpscaleModelLoader` |
| 缩放算法 | `upscale_method` | `ImageScale`, `ImageScaleBy`, `ImageScaleToTotalPixels`, `LatentUpscale`, `LatentUpscaleBy`, `PatchModelAddDownscale`, `SamplerLCMUpscale` |
| 缩放倍率 | `scale_by` | `ImageScaleBy`, `LatentUpscaleBy`, `SD_4XUpscale_Conditioning`, `SamplerLCMUpscale` |
| 目标宽度 | `target_width` | `ResizeAndPadImage` |
| 目标高度 | `target_height` | `ResizeAndPadImage` |
| 遮罩扩展 | `grow_mask_by` | `VAEEncodeForInpaint` |
| 噪声遮罩 | `noise_mask` | `InpaintModelConditioning` |
| 图像处理设置 | `processing_settings` | `AddNoise`, `CLIPSave`, `CLIPVisionEncode`, `CLIPVisionLoader`, `Canny`, `CheckpointSave`, `CombineHooks2`, `CombineHooks4`, `CombineHooks8`, `CreateHookKeyframe`, `CreateHookKeyframesFromFloats`, `CreateHookKeyframesInterpolated`, `EmptyFlux2LatentImage`, `EmptyHunyuanImageLatent`, `EmptyImage`, `EmptyLatentImage`, `EmptyQwenImageLayeredLatentImage`, `EmptySD3LatentImage`, `FluxDisableGuidance`, `FluxGuidance`, `FluxKontextImageScale`, `FluxKontextMultiReferenceLatentMethod`, `GLIGENLoader`, `GLIGENTextBoxApply`, `GetImageSize`, `GrowMask`, `Image Inset Crop (rgthree)`, `Image Resize (rgthree)`, `Image or Latent Size (rgthree)`, `ImageAddNoise`, `ImageBatch`, `ImageColorSpace`, `ImageCompositeMasked`, `ImageCrop`, `ImageFlip`, `ImageFromBatch`, `ImageInvert`, `ImagePadForOutpaint`, `ImageRotate`, `ImageScale`, `ImageScaleBy`, `ImageScaleToTotalPixels`, `ImageUpscaleWithModel`, `InvertMask`, `JoinImageWithAlpha`, `LatentAdd`, `LatentApplyOperation`, `LatentBatch`, `LatentBatchSeedBehavior`, `LatentBlend`, `LatentComposite`, `LatentCompositeMasked`, `LatentCrop`, `LatentFlip`, `LatentFromBatch`, `LatentInterpolate`, `LatentMultiply`, `LatentOperationSharpen`, `LatentOperationTonemapReinhard`, `LatentRotate`, `LatentSubtract`, `LatentUpscale`, `LatentUpscaleBy`, `LoadImage`, `LoadImageMask`, `LoadImageOutput`, `LoadLatent`, `MiniMaxH3AddGuide`, `ModelPatchLoader`, `ModelSave`, `PhotoMakerLoader`, `RebatchLatents`, `ReferenceLatent`, `ReferenceTimbreAudio`, `RepeatImageBatch`, `RepeatLatentBatch`, `ResizeAndPadImage`, `SDXL Empty Latent Image (rgthree)`, `SaveLatent`, `SetHookKeyframes`, `SetLatentNoiseMask`, `StableCascade_EmptyLatentImage`, `StableCascade_StageC_VAEEncode`, `StyleModelApply`, `StyleModelLoader`, `ThresholdMask`, `VAEDecode`, `VAEDecodeTiled`, `VAEEncode`, `VAEEncodeForInpaint`, `VAEEncodeTiled`, `VAESave` |

## 节点 → 属性与端口

| 节点 / 来源 | 属性 | 输入字段 | 输出端口 | 解析规则与限制 |
|---|---|---|---|---|
| `APG`<br>comfy_extras.nodes_apg | `model_settings` | `model`, `eta`, `norm_threshold`, `momentum` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `AddNoise`<br>comfy_extras.nodes_custom_sampler | `processing_settings` | `model`, `noise`, `sigmas`, `latent_image` | 0: `LATENT` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `AlignYourStepsScheduler`<br>comfy_extras.nodes_align_your_steps | `denoise`, `scheduler`, `steps` | `model_type`, `steps`, `denoise` | 0: `SIGMAS` | 读取调度设置；配置步数和下游阶段步数分别展示。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `AnimaLLLiteApply`<br>comfy_extras.nodes_model_patch | `model_settings` | `model`, `model_patch`, `image`, `strength`, `start_percent`, `end_percent`, `mask` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `Any Switch (rgthree)`<br>custom_nodes.rgthree-comfy | 向消费节点传递属性 |  | 0: `*` | 按上下文输出端口、字段覆盖关系追踪；选择结果依赖运行时非空值时标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `BasicGuider`<br>comfy_extras.nodes_custom_sampler | `clip`, `negative`, `positive`, `system_prompt` | `model`, `conditioning` | 0: `GUIDER` | 按输入角色追踪模型和正反向条件，保留多组 CFG。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `BasicScheduler`<br>comfy_extras.nodes_custom_sampler | `denoise`, `scheduler`, `steps` | `model`, `scheduler`, `steps`, `denoise` | 0: `SIGMAS` | 读取调度设置；配置步数和下游阶段步数分别展示。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `BetaSamplingScheduler`<br>comfy_extras.nodes_custom_sampler | `scheduler`, `steps` | `model`, `steps`, `alpha`, `beta` | 0: `SIGMAS` | 读取调度设置；配置步数和下游阶段步数分别展示。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `BlockSparseAttention`<br>comfy_extras.nodes_sparse_attention | `model_settings` | `model`, `selection`, `start_percent`, `end_percent`, `dense_blocks`, `min_tokens`, `extra_tokens`, `sink_conditioning`, `verbose` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `CFGGuider`<br>comfy_extras.nodes_custom_sampler | `cfg`, `clip`, `negative`, `positive`, `system_prompt` | `model`, `positive`, `negative`, `cfg` | 0: `GUIDER` | 按输入角色追踪模型和正反向条件，保留多组 CFG。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `CFGNorm`<br>comfy_extras.nodes_cfg | `model_settings` | `model`, `strength`, `pre_cfg` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `CFGOverride`<br>comfy_extras.nodes_custom_sampler | `cfg`, `model_settings` | `model`, `cfg`, `start_percent`, `end_percent` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `CFGZeroStar`<br>comfy_extras.nodes_cfg | `model_settings` | `model` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `CLIPAttentionMultiply`<br>comfy_extras.nodes_attention_multiply | `model_settings` | `clip`, `q`, `k`, `v`, `out` | 0: `CLIP` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `CLIPLoader`<br>nodes | `clip` | `clip_name`, `type`, `device` | 0: `CLIP` | 读取加载文件字段及显式设置，按资源端口追踪。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `CLIPLoaderGGUF`<br>custom_nodes.ComfyUI-GGUF | `clip` | `clip_name`, `type` | 0: `CLIP` | 读取加载文件字段及显式设置，按资源端口追踪。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `CLIPMergeAdd`<br>comfy_extras.nodes_model_merging | `model_settings` | `clip1`, `clip2` | 0: `CLIP` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `CLIPMergeSimple`<br>comfy_extras.nodes_model_merging | `model_settings` | `clip1`, `clip2`, `ratio` | 0: `CLIP` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `CLIPMergeSubtract`<br>comfy_extras.nodes_model_merging | `model_settings` | `clip1`, `clip2`, `multiplier` | 0: `CLIP` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `CLIPSave`<br>comfy_extras.nodes_model_merging | `processing_settings` | `clip`, `filename_prefix` |  | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `CLIPSetLastLayer`<br>nodes | `model_settings` | `clip`, `stop_at_clip_layer` | 0: `CLIP` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `CLIPTextEncode`<br>nodes | `clip`, `negative`, `positive`, `system_prompt` | `text`, `clip` | 0: `CONDITIONING` | 沿条件用途确定正反向，保留文本通道、系统提示词及编码资源。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `CLIPTextEncodeControlnet`<br>comfy_extras.nodes_cond | `clip`, `negative`, `positive`, `system_prompt` | `clip`, `conditioning`, `text` | 0: `CONDITIONING` | 沿条件用途确定正反向，保留文本通道、系统提示词及编码资源。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `CLIPTextEncodeFlux`<br>comfy_extras.nodes_flux | `clip`, `guidance`, `negative`, `positive`, `system_prompt` | `clip`, `clip_l`, `t5xxl`, `guidance` | 0: `CONDITIONING` | 沿条件用途确定正反向，保留文本通道、系统提示词及编码资源。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `CLIPTextEncodeHiDream`<br>comfy_extras.nodes_hidream | `clip`, `negative`, `positive`, `system_prompt` | `clip`, `clip_l`, `clip_g`, `t5xxl`, `llama` | 0: `CONDITIONING` | 沿条件用途确定正反向，保留文本通道、系统提示词及编码资源。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `CLIPTextEncodeHunyuanDiT`<br>comfy_extras.nodes_hunyuan | `clip`, `negative`, `positive`, `system_prompt` | `clip`, `bert`, `mt5xl` | 0: `CONDITIONING` | 沿条件用途确定正反向，保留文本通道、系统提示词及编码资源。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `CLIPTextEncodeKandinsky5`<br>comfy_extras.nodes_kandinsky5 | `clip`, `negative`, `positive`, `system_prompt` | `clip`, `clip_l`, `qwen25_7b` | 0: `CONDITIONING` | 沿条件用途确定正反向，保留文本通道、系统提示词及编码资源。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `CLIPTextEncodeLumina2`<br>comfy_extras.nodes_lumina2 | `clip`, `negative`, `positive`, `system_prompt` | `system_prompt`, `user_prompt`, `clip` | 0: `CONDITIONING` | 沿条件用途确定正反向，保留文本通道、系统提示词及编码资源。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `CLIPTextEncodePixArtAlpha`<br>comfy_extras.nodes_pixart | `clip`, `negative`, `positive`, `system_prompt` | `width`, `height`, `text`, `clip` | 0: `CONDITIONING` | 沿条件用途确定正反向，保留文本通道、系统提示词及编码资源。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `CLIPTextEncodeSD3`<br>comfy_extras.nodes_sd3 | `clip`, `negative`, `positive`, `system_prompt` | `clip`, `clip_l`, `clip_g`, `t5xxl`, `empty_padding` | 0: `CONDITIONING` | 沿条件用途确定正反向，保留文本通道、系统提示词及编码资源。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `CLIPTextEncodeSDXL`<br>comfy_extras.nodes_clip_sdxl | `clip`, `negative`, `positive`, `system_prompt` | `clip`, `width`, `height`, `crop_w`, `crop_h`, `target_width`, `target_height`, `text_g`, `text_l` | 0: `CONDITIONING` | 沿条件用途确定正反向，保留文本通道、系统提示词及编码资源。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `CLIPTextEncodeSDXLRefiner`<br>comfy_extras.nodes_clip_sdxl | `clip`, `negative`, `positive`, `system_prompt` | `ascore`, `width`, `height`, `text`, `clip` | 0: `CONDITIONING` | 沿条件用途确定正反向，保留文本通道、系统提示词及编码资源。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `CLIPVisionEncode`<br>nodes | `processing_settings` | `clip_vision`, `image`, `crop` | 0: `CLIP_VISION_OUTPUT` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `CLIPVisionLoader`<br>nodes | `processing_settings` | `clip_name` | 0: `CLIP_VISION` | 保留辅助模型文件和作用设置。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `Canny`<br>comfy_extras.nodes_canny | `processing_settings` | `image`, `low_threshold`, `high_threshold` | 0: `IMAGE` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `CaseConverter`<br>comfy_extras.nodes_string | 向消费节点传递属性 | `string`, `mode` | 0: `STRING` | 按已登记的纯标量语义解析；依赖外部通配词库的运行结果标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `Checkpoint Loader (LoraManager)`<br>custom_nodes.comfyui-lora-manager | `clip`, `model`, `vae` | `ckpt_name` | 0: `MODEL`, 1: `CLIP`, 2: `VAE` | 按输出端口区分模型、内置编码器与内置 VAE；随机选模结果未保存时标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `CheckpointLoader`<br>nodes | `clip`, `model`, `vae` | `config_name`, `ckpt_name` | 0: `MODEL`, 1: `CLIP`, 2: `VAE` | 按输出端口区分模型、内置编码器与内置 VAE；随机选模结果未保存时标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `CheckpointLoaderSimple`<br>nodes | `clip`, `model`, `vae` | `ckpt_name` | 0: `MODEL`, 1: `CLIP`, 2: `VAE` | 按输出端口区分模型、内置编码器与内置 VAE；随机选模结果未保存时标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `CheckpointSave`<br>comfy_extras.nodes_model_merging | `processing_settings` | `model`, `clip`, `vae`, `filename_prefix` |  | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ChromaRadianceOptions`<br>comfy_extras.nodes_chroma_radiance | `model_settings` | `model`, `preserve_wrapper`, `start_sigma`, `end_sigma`, `nerf_tile_size`, `force_sequential_txt_ids` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `CombineHooks2`<br>comfy_extras.nodes_hooks | `processing_settings` | `hooks_A`, `hooks_B` | 0: `HOOKS` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `CombineHooks4`<br>comfy_extras.nodes_hooks | `processing_settings` | `hooks_A`, `hooks_B`, `hooks_C`, `hooks_D` | 0: `HOOKS` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `CombineHooks8`<br>comfy_extras.nodes_hooks | `processing_settings` | `hooks_A`, `hooks_B`, `hooks_C`, `hooks_D`, `hooks_E`, `hooks_F`, `hooks_G`, `hooks_H` | 0: `HOOKS` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ComfyAndNode`<br>comfy_extras.nodes_logic | 向消费节点传递属性 | `values` | 0: `BOOLEAN` | 按已登记的纯标量语义解析；依赖外部通配词库的运行结果标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ComfyNotNode`<br>comfy_extras.nodes_logic | 向消费节点传递属性 | `value` | 0: `BOOLEAN` | 按已登记的纯标量语义解析；依赖外部通配词库的运行结果标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ComfyOrNode`<br>comfy_extras.nodes_logic | 向消费节点传递属性 | `values` | 0: `BOOLEAN` | 按已登记的纯标量语义解析；依赖外部通配词库的运行结果标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ComfySwitchNode`<br>comfy_extras.nodes_logic | 向消费节点传递属性 | `switch`, `on_false`, `on_true` | 0: `COMFY_MATCHTYPE_V3` | 按已登记的纯标量语义解析；依赖外部通配词库的运行结果标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ConditioningAverage`<br>nodes | `control_settings` | `conditioning_to`, `conditioning_from`, `conditioning_to_strength` | 0: `CONDITIONING` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ConditioningCombine`<br>nodes | `control_settings` | `conditioning_1`, `conditioning_2` | 0: `CONDITIONING` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ConditioningConcat`<br>nodes | `control_settings` | `conditioning_to`, `conditioning_from` | 0: `CONDITIONING` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ConditioningLoader`<br>comfy_extras.nodes_cond | 向消费节点传递属性 | `conditioning_name` | 0: `CONDITIONING` | 记录外部数据引用，内容未嵌入执行图时标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ConditioningMultiply`<br>nodes | `control_settings` | `conditioning`, `multiplier` | 0: `CONDITIONING` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ConditioningSetArea`<br>nodes | `control_settings`, `height`, `width` | `conditioning`, `width`, `height`, `x`, `y`, `strength` | 0: `CONDITIONING` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ConditioningSetAreaPercentage`<br>nodes | `control_settings`, `height`, `width` | `conditioning`, `width`, `height`, `x`, `y`, `strength` | 0: `CONDITIONING` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ConditioningSetAreaPercentageVideo`<br>comfy_extras.nodes_video_model | `control_settings`, `height`, `width` | `conditioning`, `width`, `height`, `temporal`, `x`, `y`, `z`, `strength` | 0: `CONDITIONING` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ConditioningSetAreaStrength`<br>nodes | `control_settings` | `conditioning`, `strength` | 0: `CONDITIONING` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ConditioningSetDefaultCombine`<br>comfy_extras.nodes_hooks | `control_settings` | `cond`, `cond_DEFAULT`, `hooks` | 0: `CONDITIONING` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ConditioningSetMask`<br>nodes | `control_settings` | `conditioning`, `mask`, `strength`, `set_cond_area` | 0: `CONDITIONING` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ConditioningSetProperties`<br>comfy_extras.nodes_hooks | `control_settings` | `cond_NEW`, `strength`, `set_cond_area`, `mask`, `hooks`, `timesteps` | 0: `CONDITIONING` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ConditioningSetPropertiesAndCombine`<br>comfy_extras.nodes_hooks | `control_settings` | `cond`, `cond_NEW`, `strength`, `set_cond_area`, `mask`, `hooks`, `timesteps` | 0: `CONDITIONING` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ConditioningSetTimestepRange`<br>nodes | `control_settings` | `conditioning`, `start`, `end` | 0: `CONDITIONING` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ConditioningTimestepsRange`<br>comfy_extras.nodes_hooks | `control_settings` | `start_percent`, `end_percent` | 0: `TIMESTEPS_RANGE`, 1: `TIMESTEPS_RANGE`, 2: `TIMESTEPS_RANGE` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ConditioningZeroOut`<br>nodes | `control_settings` | `conditioning` | 0: `CONDITIONING` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `Context (rgthree)`<br>custom_nodes.rgthree-comfy | `seed` | `base_ctx`, `model`, `clip`, `vae`, `positive`, `negative`, `latent`, `images`, `seed` | 0: `RGTHREE_CONTEXT`, 1: `MODEL`, 2: `CLIP`, 3: `VAE`, 4: `CONDITIONING`, 5: `CONDITIONING`, 6: `LATENT`, 7: `IMAGE`, 8: `INT` | 按上下文输出端口、字段覆盖关系追踪；选择结果依赖运行时非空值时标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `Context Big (rgthree)`<br>custom_nodes.rgthree-comfy | `cfg`, `scheduler`, `seed`, `steps` | `base_ctx`, `model`, `clip`, `vae`, `positive`, `negative`, `latent`, `images`, `seed`, `steps`, `step_refiner`, `cfg`, `ckpt_name`, `sampler`, `scheduler`, `clip_width`, `clip_height`, `text_pos_g`, `text_pos_l`, `text_neg_g`, `text_neg_l`, `mask`, `control_net` | 0: `RGTHREE_CONTEXT`, 1: `MODEL`, 2: `CLIP`, 3: `VAE`, 4: `CONDITIONING`, 5: `CONDITIONING`, 6: `LATENT`, 7: `IMAGE`, 8: `INT`, 9: `INT`, 10: `INT`, 11: `FLOAT`, 12: `COMBO`, 13: `COMBO`, 14: `COMBO`, 15: `INT`, 16: `INT`, 17: `STRING`, 18: `STRING`, 19: `STRING`, 20: `STRING`, 21: `MASK`, 22: `CONTROL_NET` | 按上下文输出端口、字段覆盖关系追踪；选择结果依赖运行时非空值时标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `Context Merge (rgthree)`<br>custom_nodes.rgthree-comfy | 向消费节点传递属性 |  | 0: `RGTHREE_CONTEXT`, 1: `MODEL`, 2: `CLIP`, 3: `VAE`, 4: `CONDITIONING`, 5: `CONDITIONING`, 6: `LATENT`, 7: `IMAGE`, 8: `INT` | 按上下文输出端口、字段覆盖关系追踪；选择结果依赖运行时非空值时标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `Context Merge Big (rgthree)`<br>custom_nodes.rgthree-comfy | 向消费节点传递属性 |  | 0: `RGTHREE_CONTEXT`, 1: `MODEL`, 2: `CLIP`, 3: `VAE`, 4: `CONDITIONING`, 5: `CONDITIONING`, 6: `LATENT`, 7: `IMAGE`, 8: `INT`, 9: `INT`, 10: `INT`, 11: `FLOAT`, 12: `COMBO`, 13: `COMBO`, 14: `COMBO`, 15: `INT`, 16: `INT`, 17: `STRING`, 18: `STRING`, 19: `STRING`, 20: `STRING`, 21: `MASK`, 22: `CONTROL_NET` | 按上下文输出端口、字段覆盖关系追踪；选择结果依赖运行时非空值时标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `Context Switch (rgthree)`<br>custom_nodes.rgthree-comfy | 向消费节点传递属性 |  | 0: `RGTHREE_CONTEXT`, 1: `MODEL`, 2: `CLIP`, 3: `VAE`, 4: `CONDITIONING`, 5: `CONDITIONING`, 6: `LATENT`, 7: `IMAGE`, 8: `INT` | 按上下文输出端口、字段覆盖关系追踪；选择结果依赖运行时非空值时标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `Context Switch Big (rgthree)`<br>custom_nodes.rgthree-comfy | 向消费节点传递属性 |  | 0: `RGTHREE_CONTEXT`, 1: `MODEL`, 2: `CLIP`, 3: `VAE`, 4: `CONDITIONING`, 5: `CONDITIONING`, 6: `LATENT`, 7: `IMAGE`, 8: `INT`, 9: `INT`, 10: `INT`, 11: `FLOAT`, 12: `COMBO`, 13: `COMBO`, 14: `COMBO`, 15: `INT`, 16: `INT`, 17: `STRING`, 18: `STRING`, 19: `STRING`, 20: `STRING`, 21: `MASK`, 22: `CONTROL_NET` | 按上下文输出端口、字段覆盖关系追踪；选择结果依赖运行时非空值时标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ContextWindowsManual`<br>comfy_extras.nodes_context_windows | `model_settings` | `model`, `context_length`, `context_overlap`, `context_schedule`, `context_stride`, `closed_loop`, `fuse_method`, `dim`, `freenoise`, `cond_retain_index_list`, `split_conds_to_windows`, `latent_retain_index_list`, `causal_window_fix` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ControlNetApply`<br>nodes | `control_settings` | `conditioning`, `control_net`, `image`, `strength` | 0: `CONDITIONING` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ControlNetApplyAdvanced`<br>nodes | `control_settings` | `positive`, `negative`, `control_net`, `image`, `strength`, `start_percent`, `end_percent`, `vae` | 0: `CONDITIONING`, 1: `CONDITIONING` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ControlNetApplySD3`<br>comfy_extras.nodes_sd3 | `control_settings` | `positive`, `negative`, `control_net`, `vae`, `image`, `strength`, `start_percent`, `end_percent` | 0: `CONDITIONING`, 1: `CONDITIONING` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ControlNetInpaintingAliMamaApply`<br>comfy_extras.nodes_controlnet | `control_settings` | `positive`, `negative`, `control_net`, `vae`, `image`, `mask`, `strength`, `start_percent`, `end_percent` | 0: `CONDITIONING`, 1: `CONDITIONING` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ControlNetLoader`<br>nodes | `controlnet` | `control_net_name` | 0: `CONTROL_NET` | 读取加载文件字段及显式设置，按资源端口追踪。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ConvertArrayToString`<br>comfy_extras.nodes_string | 向消费节点传递属性 | `array`, `indent` | 0: `STRING` | 按已登记的纯标量语义解析；依赖外部通配词库的运行结果标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ConvertDictionaryToString`<br>comfy_extras.nodes_string | 向消费节点传递属性 | `dictionary`, `indent` | 0: `STRING` | 按已登记的纯标量语义解析；依赖外部通配词库的运行结果标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `Create Hook LoRA (LoraManager)`<br>custom_nodes.comfyui-lora-manager | `lora` | `text` | 0: `HOOKS`, 1: `STRING`, 2: `STRING` | 读取启用项、名称及双权重，保留重复应用顺序。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `CreateHookKeyframe`<br>comfy_extras.nodes_hooks | `processing_settings` | `strength_mult`, `start_percent`, `prev_hook_kf` | 0: `HOOK_KEYFRAMES` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `CreateHookKeyframesFromFloats`<br>comfy_extras.nodes_hooks | `processing_settings` | `floats_strength`, `start_percent`, `end_percent`, `print_keyframes`, `prev_hook_kf` | 0: `HOOK_KEYFRAMES` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `CreateHookKeyframesInterpolated`<br>comfy_extras.nodes_hooks | `processing_settings` | `strength_start`, `strength_end`, `interpolation`, `start_percent`, `end_percent`, `keyframes_count`, `print_keyframes`, `prev_hook_kf` | 0: `HOOK_KEYFRAMES` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `CreateHookLora`<br>comfy_extras.nodes_hooks | `lora` | `lora_name`, `strength_model`, `strength_clip`, `prev_hooks` | 0: `HOOKS` | 读取启用项、名称及双权重，保留重复应用顺序。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `CreateHookLoraModelOnly`<br>comfy_extras.nodes_hooks | `lora` | `lora_name`, `strength_model`, `prev_hooks` | 0: `HOOKS` | 读取启用项、名称及双权重，保留重复应用顺序。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `CustomCombo`<br>comfy_extras.nodes_logic | 向消费节点传递属性 | `choice` | 0: `STRING`, 1: `INT` | 按已登记的纯标量语义解析；依赖外部通配词库的运行结果标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `DiffControlNetLoader`<br>nodes | `controlnet` | `model`, `control_net_name` | 0: `CONTROL_NET` | 读取加载文件字段及显式设置，按资源端口追踪。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `DifferentialDiffusion`<br>comfy_extras.nodes_differential_diffusion | `model_settings` | `model`, `strength` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `DiffusersLoader`<br>nodes | `clip`, `model`, `vae` | `model_path` | 0: `MODEL`, 1: `CLIP`, 2: `VAE` | 按输出端口区分模型、内置编码器与内置 VAE；随机选模结果未保存时标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `DisableNoise`<br>comfy_extras.nodes_custom_sampler | 向消费节点传递属性 |  | 0: `NOISE` | 读取噪声种子或禁用噪声状态；种子以字符串返回。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `DualCFGGuider`<br>comfy_extras.nodes_custom_sampler | `cfg`, `clip`, `negative`, `positive`, `system_prompt` | `model`, `cond1`, `cond2`, `negative`, `cfg_conds`, `cfg_cond2_negative`, `style` | 0: `GUIDER` | 按输入角色追踪模型和正反向条件，保留多组 CFG。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `DualCLIPLoader`<br>nodes | `clip` | `clip_name1`, `clip_name2`, `type`, `device` | 0: `CLIP` | 读取加载文件字段及显式设置，按资源端口追踪。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `DualCLIPLoaderGGUF`<br>custom_nodes.ComfyUI-GGUF | `clip` | `clip_name1`, `clip_name2`, `type` | 0: `CLIP` | 读取加载文件字段及显式设置，按资源端口追踪。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `DualModelGuider`<br>comfy_extras.nodes_custom_sampler | `cfg`, `clip`, `negative`, `positive`, `system_prompt` | `model`, `positive`, `cfg`, `model_negative`, `negative` | 0: `GUIDER` | 按输入角色追踪模型和正反向条件，保留多组 CFG。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `EasyCache`<br>comfy_extras.nodes_easycache | `model_settings` | `model`, `reuse_threshold`, `start_percent`, `end_percent`, `verbose` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `EmptyFlux2LatentImage`<br>comfy_extras.nodes_flux | `batch_size`, `height`, `processing_settings`, `width` | `width`, `height`, `batch_size` | 0: `LATENT` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `EmptyHunyuanImageLatent`<br>comfy_extras.nodes_hunyuan | `batch_size`, `height`, `processing_settings`, `width` | `width`, `height`, `batch_size` | 0: `LATENT` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `EmptyImage`<br>nodes | `batch_size`, `height`, `processing_settings`, `width` | `width`, `height`, `batch_size`, `color` | 0: `IMAGE` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `EmptyLatentImage`<br>nodes | `batch_size`, `height`, `processing_settings`, `width` | `width`, `height`, `batch_size` | 0: `LATENT` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `EmptyQwenImageLayeredLatentImage`<br>comfy_extras.nodes_qwen | `batch_size`, `height`, `processing_settings`, `width` | `width`, `height`, `layers`, `batch_size` | 0: `LATENT` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `EmptySD3LatentImage`<br>comfy_extras.nodes_sd3 | `batch_size`, `height`, `processing_settings`, `width` | `width`, `height`, `batch_size` | 0: `LATENT` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `Epsilon Scaling`<br>comfy_extras.nodes_eps | `model_settings` | `model`, `scaling_factor` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ExponentialScheduler`<br>comfy_extras.nodes_custom_sampler | `scheduler`, `steps` | `steps`, `sigma_max`, `sigma_min` | 0: `SIGMAS` | 读取调度设置；配置步数和下游阶段步数分别展示。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ExtendIntermediateSigmas`<br>comfy_extras.nodes_custom_sampler | `steps` | `sigmas`, `steps`, `start_at_sigma`, `end_at_sigma`, `spacing` | 0: `SIGMAS` | 追踪上游调度设置，并按切分端口计算可以确定的序列长度。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `FlipSigmas`<br>comfy_extras.nodes_custom_sampler | 向消费节点传递属性 | `sigmas` | 0: `SIGMAS` | 追踪上游调度设置，并按切分端口计算可以确定的序列长度。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `Flux2Scheduler`<br>comfy_extras.nodes_flux | `scheduler`, `steps` | `steps`, `width`, `height` | 0: `SIGMAS` | 读取调度设置；配置步数和下游阶段步数分别展示。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `FluxDisableGuidance`<br>comfy_extras.nodes_flux | `processing_settings` | `conditioning` | 0: `CONDITIONING` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `FluxGuidance`<br>comfy_extras.nodes_flux | `guidance`, `processing_settings` | `conditioning`, `guidance` | 0: `CONDITIONING` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `FluxKVCache`<br>comfy_extras.nodes_flux | `model_settings` | `model` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `FluxKontextImageScale`<br>comfy_extras.nodes_flux | `processing_settings` | `image` | 0: `IMAGE` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `FluxKontextMultiReferenceLatentMethod`<br>comfy_extras.nodes_flux | `processing_settings` | `conditioning`, `reference_latents_method` | 0: `CONDITIONING` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `FreSca`<br>comfy_extras.nodes_fresca | `model_settings` | `model`, `scale_low`, `scale_high`, `freq_cutoff` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `FreeU`<br>comfy_extras.nodes_freelunch | `model_settings` | `model`, `b1`, `b2`, `s1`, `s2` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `FreeU_V2`<br>comfy_extras.nodes_freelunch | `model_settings` | `model`, `b1`, `b2`, `s1`, `s2` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `GITSScheduler`<br>comfy_extras.nodes_gits | `denoise`, `scheduler`, `steps` | `coeff`, `steps`, `denoise` | 0: `SIGMAS` | 读取调度设置；配置步数和下游阶段步数分别展示。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `GLIGENLoader`<br>nodes | `processing_settings` | `gligen_name` | 0: `GLIGEN` | 保留辅助模型文件和作用设置。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `GLIGENTextBoxApply`<br>nodes | `height`, `processing_settings`, `width` | `conditioning_to`, `clip`, `gligen_textbox_model`, `text`, `width`, `height`, `x`, `y` | 0: `CONDITIONING` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `GetImageSize`<br>comfy_extras.nodes_images | `processing_settings` | `image` | 0: `INT`, 1: `INT`, 2: `INT` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `GrowMask`<br>comfy_extras.nodes_mask | `processing_settings` | `mask`, `expand`, `tapered_corners` | 0: `MASK` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `HiDreamO1PatchSeamSmoothing`<br>comfy_extras.nodes_hidream_o1 | `model_settings` | `model`, `start_percent`, `end_percent`, `pattern`, `passes`, `blend`, `strength` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `HyperTile`<br>comfy_extras.nodes_hypertile | `model_settings` | `model`, `tile_size`, `swap_size`, `max_depth`, `scale_depth` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `HypernetworkLoader`<br>comfy_extras.nodes_hypernetwork | `model_settings` | `model`, `hypernetwork_name`, `strength` | 0: `MODEL` | 保留辅助模型文件和作用设置。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `Ideogram4Scheduler`<br>comfy_extras.nodes_ideogram4 | `scheduler`, `steps` | `steps`, `width`, `height`, `mu`, `std` | 0: `SIGMAS` | 读取调度设置；配置步数和下游阶段步数分别展示。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `Image Inset Crop (rgthree)`<br>custom_nodes.rgthree-comfy | `processing_settings` | `image`, `measurement`, `left`, `right`, `top`, `bottom` | 0: `IMAGE` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `Image Resize (rgthree)`<br>custom_nodes.rgthree-comfy | `height`, `processing_settings`, `width` | `image`, `measurement`, `width`, `height`, `fit`, `method` | 0: `IMAGE`, 1: `INT`, 2: `INT` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `Image or Latent Size (rgthree)`<br>custom_nodes.rgthree-comfy | `processing_settings` |  | 0: `INT`, 1: `INT` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ImageAddNoise`<br>comfy_extras.nodes_images | `processing_settings`, `seed` | `image`, `seed`, `strength` | 0: `IMAGE` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ImageBatch`<br>nodes | `processing_settings` | `image1`, `image2` | 0: `IMAGE` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ImageColorSpace`<br>comfy_extras.nodes_images | `processing_settings` | `image`, `source`, `destination` | 0: `IMAGE` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ImageCompositeMasked`<br>comfy_extras.nodes_mask | `processing_settings` | `destination`, `source`, `x`, `y`, `resize_source`, `mask` | 0: `IMAGE` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ImageCrop`<br>comfy_extras.nodes_images | `height`, `processing_settings`, `width` | `image`, `width`, `height`, `x`, `y` | 0: `IMAGE` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ImageFlip`<br>comfy_extras.nodes_images | `processing_settings` | `image`, `flip_method` | 0: `IMAGE` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ImageFromBatch`<br>comfy_extras.nodes_images | `processing_settings` | `image`, `batch_index`, `length` | 0: `IMAGE` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ImageInvert`<br>nodes | `processing_settings` | `image` | 0: `IMAGE` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ImageOnlyCheckpointLoader`<br>comfy_extras.nodes_video_model | `clip`, `model`, `vae` | `ckpt_name` | 0: `MODEL`, 1: `CLIP_VISION`, 2: `VAE` | 按输出端口区分模型、内置编码器与内置 VAE；随机选模结果未保存时标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ImagePadForOutpaint`<br>nodes | `processing_settings` | `image`, `left`, `top`, `right`, `bottom`, `feathering` | 0: `IMAGE`, 1: `MASK` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ImageRotate`<br>comfy_extras.nodes_images | `processing_settings` | `image`, `rotation` | 0: `IMAGE` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ImageScale`<br>nodes | `height`, `processing_settings`, `upscale_method`, `width` | `image`, `upscale_method`, `width`, `height`, `crop` | 0: `IMAGE` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ImageScaleBy`<br>nodes | `processing_settings`, `scale_by`, `upscale_method` | `image`, `upscale_method`, `scale_by` | 0: `IMAGE` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ImageScaleToTotalPixels`<br>comfy_extras.nodes_post_processing | `processing_settings`, `upscale_method` | `image`, `upscale_method`, `megapixels`, `resolution_steps` | 0: `IMAGE` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ImageUpscaleWithModel`<br>comfy_extras.nodes_upscale_model | `processing_settings` | `upscale_model`, `image` | 0: `IMAGE` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `InpaintModelConditioning`<br>nodes | `control_settings`, `noise_mask` | `positive`, `negative`, `vae`, `pixels`, `mask`, `noise_mask` | 0: `CONDITIONING`, 1: `CONDITIONING`, 2: `LATENT` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `InstructPixToPixConditioning`<br>comfy_extras.nodes_ip2p | `control_settings` | `positive`, `negative`, `vae`, `pixels` | 0: `CONDITIONING`, 1: `CONDITIONING`, 2: `LATENT` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `InvertMask`<br>comfy_extras.nodes_mask | `processing_settings` | `mask` | 0: `MASK` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `JoinImageWithAlpha`<br>comfy_extras.nodes_compositing | `processing_settings` | `image`, `alpha` | 0: `IMAGE` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `JsonExtractString`<br>comfy_extras.nodes_string | 向消费节点传递属性 | `json_string`, `key` | 0: `STRING` | 按已登记的纯标量语义解析；依赖外部通配词库的运行结果标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `KSampler`<br>nodes | `batch_size`, `cfg`, `denoise`, `height`, `model`, `negative`, `positive`, `sampler`, `scheduler`, `seed`, `stage_steps`, `steps`, `width` | `model`, `seed`, `steps`, `cfg`, `sampler_name`, `scheduler`, `positive`, `negative`, `latent_image`, `denoise` | 0: `LATENT` | 读取采样字段并沿条件、模型、噪声、调度器和潜空间输入追踪；阶段步数单独推导。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `KSampler Config (rgthree)`<br>custom_nodes.rgthree-comfy | `cfg`, `sampler`, `scheduler`, `steps` | `steps_total`, `refiner_step`, `cfg`, `sampler_name`, `scheduler` | 0: `INT`, 1: `INT`, 2: `FLOAT`, 3: `COMBO`, 4: `COMBO` | 按固定输出端口映射步数、CFG、采样器和调度器。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `KSamplerAdvanced`<br>nodes | `add_noise`, `batch_size`, `cfg`, `end_at_step`, `height`, `model`, `negative`, `positive`, `return_with_leftover_noise`, `sampler`, `scheduler`, `seed`, `stage_steps`, `start_at_step`, `steps`, `width` | `model`, `add_noise`, `noise_seed`, `steps`, `cfg`, `sampler_name`, `scheduler`, `positive`, `negative`, `latent_image`, `start_at_step`, `end_at_step`, `return_with_leftover_noise` | 0: `LATENT` | 读取采样字段并沿条件、模型、噪声、调度器和潜空间输入追踪；阶段步数单独推导。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `KSamplerSelect`<br>comfy_extras.nodes_custom_sampler | `sampler` | `sampler_name` | 0: `SAMPLER` | 读取采样器名称或专用采样器类型及参数。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `KarrasScheduler`<br>comfy_extras.nodes_custom_sampler | `scheduler`, `steps` | `steps`, `sigma_max`, `sigma_min`, `rho` | 0: `SIGMAS` | 读取调度设置；配置步数和下游阶段步数分别展示。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `Krea2SystemPrompt`<br>custom_nodes.comfyui-krea2-text-encoder | 向消费节点传递属性 | `text` | 0: `STRING` | 读取标量输出；特殊随机占位值标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `LTXVContextWindows`<br>comfy_extras.nodes_context_windows | `model_settings` | `model`, `context_length`, `context_overlap`, `context_schedule`, `context_stride`, `closed_loop`, `fuse_method`, `freenoise`, `retain_first_frame`, `split_conds_to_windows` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `LTXVModalityGuidance`<br>comfy_extras.nodes_lt | `model_settings` | `model`, `modality_scale`, `start_percent`, `end_percent` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `LTXVSpatioTemporalGuidance`<br>comfy_extras.nodes_lt | `model_settings` | `model`, `scale`, `blocks`, `start_percent`, `end_percent` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `LaplaceScheduler`<br>comfy_extras.nodes_custom_sampler | `scheduler`, `steps` | `steps`, `sigma_max`, `sigma_min`, `mu`, `beta` | 0: `SIGMAS` | 读取调度设置；配置步数和下游阶段步数分别展示。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `LatentAdd`<br>comfy_extras.nodes_latent | `processing_settings` | `samples1`, `samples2` | 0: `LATENT` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `LatentApplyOperation`<br>comfy_extras.nodes_latent | `processing_settings` | `samples`, `operation` | 0: `LATENT` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `LatentApplyOperationCFG`<br>comfy_extras.nodes_latent | `model_settings` | `model`, `operation` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `LatentBatch`<br>comfy_extras.nodes_latent | `processing_settings` | `samples1`, `samples2` | 0: `LATENT` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `LatentBatchSeedBehavior`<br>comfy_extras.nodes_latent | `processing_settings` | `samples`, `seed_behavior` | 0: `LATENT` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `LatentBlend`<br>nodes | `processing_settings` | `samples1`, `samples2`, `blend_factor` | 0: `LATENT` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `LatentComposite`<br>nodes | `processing_settings` | `samples_to`, `samples_from`, `x`, `y`, `feather` | 0: `LATENT` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `LatentCompositeMasked`<br>comfy_extras.nodes_mask | `processing_settings` | `destination`, `source`, `x`, `y`, `resize_source`, `mask` | 0: `LATENT` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `LatentCrop`<br>nodes | `height`, `processing_settings`, `width` | `samples`, `width`, `height`, `x`, `y` | 0: `LATENT` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `LatentFlip`<br>nodes | `processing_settings` | `samples`, `flip_method` | 0: `LATENT` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `LatentFromBatch`<br>nodes | `processing_settings` | `samples`, `batch_index`, `length` | 0: `LATENT` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `LatentInterpolate`<br>comfy_extras.nodes_latent | `processing_settings` | `samples1`, `samples2`, `ratio` | 0: `LATENT` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `LatentMultiply`<br>comfy_extras.nodes_latent | `processing_settings` | `samples`, `multiplier` | 0: `LATENT` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `LatentOperationSharpen`<br>comfy_extras.nodes_latent | `processing_settings` | `sharpen_radius`, `sigma`, `alpha` | 0: `LATENT_OPERATION` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `LatentOperationTonemapReinhard`<br>comfy_extras.nodes_latent | `processing_settings` | `multiplier` | 0: `LATENT_OPERATION` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `LatentRotate`<br>nodes | `processing_settings` | `samples`, `rotation` | 0: `LATENT` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `LatentSubtract`<br>comfy_extras.nodes_latent | `processing_settings` | `samples1`, `samples2` | 0: `LATENT` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `LatentUpscale`<br>nodes | `height`, `processing_settings`, `upscale_method`, `width` | `samples`, `upscale_method`, `width`, `height`, `crop` | 0: `LATENT` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `LatentUpscaleBy`<br>nodes | `processing_settings`, `scale_by`, `upscale_method` | `samples`, `upscale_method`, `scale_by` | 0: `LATENT` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `LatentUpscaleModelLoader`<br>comfy_extras.nodes_hunyuan | `upscale_model` | `model_name` | 0: `LATENT_UPSCALE_MODEL` | 读取加载文件字段及显式设置，按资源端口追踪。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `LazyCache`<br>comfy_extras.nodes_easycache | `model_settings` | `model`, `reuse_threshold`, `start_percent`, `end_percent`, `verbose` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `LoRA Text Loader (LoraManager)`<br>custom_nodes.comfyui-lora-manager | `lora` | `model`, `lora_syntax`, `clip`, `lora_stack` | 0: `MODEL`, 1: `CLIP`, 2: `STRING`, 3: `STRING` | 读取启用项、名称及双权重，保留重复应用顺序。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `LoadImage`<br>nodes | `processing_settings` | `image` | 0: `IMAGE`, 1: `MASK` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `LoadImageMask`<br>nodes | `processing_settings` | `image`, `channel` | 0: `MASK` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `LoadImageOutput`<br>nodes | `processing_settings` | `image` | 0: `IMAGE`, 1: `MASK` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `LoadLatent`<br>nodes | `processing_settings` | `latent` | 0: `LATENT` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `Lora Cycler (LoraManager)`<br>custom_nodes.comfyui-lora-manager | `lora` | `cycler_config`, `pool_config` | 0: `LORA_STACK` | 组合显式 LoRA 列表；随机和循环选取结果未保存时标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `Lora Loader (LoraManager)`<br>custom_nodes.comfyui-lora-manager | `lora` | `model`, `text` | 0: `MODEL`, 1: `CLIP`, 2: `STRING`, 3: `STRING` | 读取启用项、名称及双权重，保留重复应用顺序。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `Lora Loader Stack (rgthree)`<br>custom_nodes.rgthree-comfy | `lora` | `model`, `clip`, `lora_01`, `strength_01`, `lora_02`, `strength_02`, `lora_03`, `strength_03`, `lora_04`, `strength_04` | 0: `MODEL`, 1: `CLIP` | 读取启用项、名称及双权重，保留重复应用顺序。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `Lora Randomizer (LoraManager)`<br>custom_nodes.comfyui-lora-manager | `lora` | `randomizer_config`, `loras`, `pool_config` | 0: `LORA_STACK` | 组合显式 LoRA 列表；随机和循环选取结果未保存时标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `Lora Stack Combiner (LoraManager)`<br>custom_nodes.comfyui-lora-manager | `lora` | `lora_stack1`, `lora_stack2` | 0: `LORA_STACK` | 组合显式 LoRA 列表；随机和循环选取结果未保存时标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `Lora Stacker (LoraManager)`<br>custom_nodes.comfyui-lora-manager | `lora` | `text` | 0: `LORA_STACK`, 1: `STRING`, 2: `STRING` | 组合显式 LoRA 列表；随机和循环选取结果未保存时标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `LoraLoader`<br>nodes | `lora` | `model`, `clip`, `lora_name`, `strength_model`, `strength_clip` | 0: `MODEL`, 1: `CLIP` | 读取启用项、名称及双权重，保留重复应用顺序。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `LoraLoaderBypass`<br>comfy_extras.nodes_lora_debug | `lora` | `model`, `clip`, `lora_name`, `strength_model`, `strength_clip` | 0: `MODEL`, 1: `CLIP` | 读取启用项、名称及双权重，保留重复应用顺序。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `LoraLoaderBypassModelOnly`<br>comfy_extras.nodes_lora_debug | `lora` | `model`, `lora_name`, `strength_model` | 0: `MODEL` | 读取启用项、名称及双权重，保留重复应用顺序。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `LoraLoaderModelOnly`<br>nodes | `lora` | `model`, `lora_name`, `strength_model` | 0: `MODEL` | 读取启用项、名称及双权重，保留重复应用顺序。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `LoraModelLoader`<br>comfy_extras.nodes_train | `lora` | `model`, `lora`, `strength_model`, `bypass` | 0: `MODEL` | 读取启用项、名称及双权重，保留重复应用顺序。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `Mahiro`<br>comfy_extras.nodes_mahiro | `model_settings` | `model` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ManualSigmas`<br>comfy_extras.nodes_custom_sampler | 向消费节点传递属性 | `sigmas` | 0: `SIGMAS` | 追踪上游调度设置，并按切分端口计算可以确定的序列长度。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `MiniMaxH3AddGuide`<br>comfy_extras.nodes_minimax_h3 | `processing_settings` | `positive`, `latent`, `frame_idx`, `vae`, `audio_vae`, `image`, `audio` | 0: `CONDITIONING` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `MiniMaxH3FunControlNetApply`<br>comfy_extras.nodes_minimax_h3 | `control_settings` | `model`, `model_patch`, `vae`, `strength`, `start_percent`, `end_percent`, `control_video`, `mask`, `source_video` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `MiniMaxH3SigmaShift`<br>comfy_extras.nodes_minimax_h3 | `model_settings` | `model`, `shift_video`, `shift_audio` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ModelAttentionBackend`<br>comfy_extras.nodes_model_advanced | `model_settings` | `model`, `attention` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ModelComputeDtype`<br>comfy_extras.nodes_model_advanced | `model_settings` | `model`, `dtype` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ModelMergeAdd`<br>comfy_extras.nodes_model_merging | `model_settings` | `model1`, `model2` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ModelMergeAuraflow`<br>comfy_extras.nodes_model_merging_model_specific | `model_settings` | `model1`, `model2`, `init_x_linear.`, `positional_encoding`, `cond_seq_linear.`, `register_tokens`, `t_embedder.`, `double_layers.0.`, `double_layers.1.`, `double_layers.2.`, `double_layers.3.`, `single_layers.0.`, `single_layers.1.`, `single_layers.2.`, `single_layers.3.`, `single_layers.4.`, `single_layers.5.`, `single_layers.6.`, `single_layers.7.`, `single_layers.8.`, `single_layers.9.`, `single_layers.10.`, `single_layers.11.`, `single_layers.12.`, `single_layers.13.`, `single_layers.14.`, `single_layers.15.`, `single_layers.16.`, `single_layers.17.`, `single_layers.18.`, `single_layers.19.`, `single_layers.20.`, `single_layers.21.`, `single_layers.22.`, `single_layers.23.`, `single_layers.24.`, `single_layers.25.`, `single_layers.26.`, `single_layers.27.`, `single_layers.28.`, `single_layers.29.`, `single_layers.30.`, `single_layers.31.`, `modF.`, `final_linear.` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ModelMergeBlocks`<br>comfy_extras.nodes_model_merging | `model_settings` | `model1`, `model2`, `input`, `middle`, `out` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ModelMergeCosmos14B`<br>comfy_extras.nodes_model_merging_model_specific | `model_settings` | `model1`, `model2`, `pos_embedder.`, `extra_pos_embedder.`, `x_embedder.`, `t_embedder.`, `affline_norm.`, `blocks.block0.`, `blocks.block1.`, `blocks.block2.`, `blocks.block3.`, `blocks.block4.`, `blocks.block5.`, `blocks.block6.`, `blocks.block7.`, `blocks.block8.`, `blocks.block9.`, `blocks.block10.`, `blocks.block11.`, `blocks.block12.`, `blocks.block13.`, `blocks.block14.`, `blocks.block15.`, `blocks.block16.`, `blocks.block17.`, `blocks.block18.`, `blocks.block19.`, `blocks.block20.`, `blocks.block21.`, `blocks.block22.`, `blocks.block23.`, `blocks.block24.`, `blocks.block25.`, `blocks.block26.`, `blocks.block27.`, `blocks.block28.`, `blocks.block29.`, `blocks.block30.`, `blocks.block31.`, `blocks.block32.`, `blocks.block33.`, `blocks.block34.`, `blocks.block35.`, `final_layer.` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ModelMergeCosmos7B`<br>comfy_extras.nodes_model_merging_model_specific | `model_settings` | `model1`, `model2`, `pos_embedder.`, `extra_pos_embedder.`, `x_embedder.`, `t_embedder.`, `affline_norm.`, `blocks.block0.`, `blocks.block1.`, `blocks.block2.`, `blocks.block3.`, `blocks.block4.`, `blocks.block5.`, `blocks.block6.`, `blocks.block7.`, `blocks.block8.`, `blocks.block9.`, `blocks.block10.`, `blocks.block11.`, `blocks.block12.`, `blocks.block13.`, `blocks.block14.`, `blocks.block15.`, `blocks.block16.`, `blocks.block17.`, `blocks.block18.`, `blocks.block19.`, `blocks.block20.`, `blocks.block21.`, `blocks.block22.`, `blocks.block23.`, `blocks.block24.`, `blocks.block25.`, `blocks.block26.`, `blocks.block27.`, `final_layer.` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ModelMergeCosmosPredict2_14B`<br>comfy_extras.nodes_model_merging_model_specific | `model_settings` | `model1`, `model2`, `pos_embedder.`, `x_embedder.`, `t_embedder.`, `t_embedding_norm.`, `blocks.0.`, `blocks.1.`, `blocks.2.`, `blocks.3.`, `blocks.4.`, `blocks.5.`, `blocks.6.`, `blocks.7.`, `blocks.8.`, `blocks.9.`, `blocks.10.`, `blocks.11.`, `blocks.12.`, `blocks.13.`, `blocks.14.`, `blocks.15.`, `blocks.16.`, `blocks.17.`, `blocks.18.`, `blocks.19.`, `blocks.20.`, `blocks.21.`, `blocks.22.`, `blocks.23.`, `blocks.24.`, `blocks.25.`, `blocks.26.`, `blocks.27.`, `blocks.28.`, `blocks.29.`, `blocks.30.`, `blocks.31.`, `blocks.32.`, `blocks.33.`, `blocks.34.`, `blocks.35.`, `final_layer.` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ModelMergeCosmosPredict2_2B`<br>comfy_extras.nodes_model_merging_model_specific | `model_settings` | `model1`, `model2`, `pos_embedder.`, `x_embedder.`, `t_embedder.`, `t_embedding_norm.`, `blocks.0.`, `blocks.1.`, `blocks.2.`, `blocks.3.`, `blocks.4.`, `blocks.5.`, `blocks.6.`, `blocks.7.`, `blocks.8.`, `blocks.9.`, `blocks.10.`, `blocks.11.`, `blocks.12.`, `blocks.13.`, `blocks.14.`, `blocks.15.`, `blocks.16.`, `blocks.17.`, `blocks.18.`, `blocks.19.`, `blocks.20.`, `blocks.21.`, `blocks.22.`, `blocks.23.`, `blocks.24.`, `blocks.25.`, `blocks.26.`, `blocks.27.`, `final_layer.` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ModelMergeFlux1`<br>comfy_extras.nodes_model_merging_model_specific | `model_settings` | `model1`, `model2`, `img_in.`, `time_in.`, `guidance_in`, `vector_in.`, `txt_in.`, `double_blocks.0.`, `double_blocks.1.`, `double_blocks.2.`, `double_blocks.3.`, `double_blocks.4.`, `double_blocks.5.`, `double_blocks.6.`, `double_blocks.7.`, `double_blocks.8.`, `double_blocks.9.`, `double_blocks.10.`, `double_blocks.11.`, `double_blocks.12.`, `double_blocks.13.`, `double_blocks.14.`, `double_blocks.15.`, `double_blocks.16.`, `double_blocks.17.`, `double_blocks.18.`, `single_blocks.0.`, `single_blocks.1.`, `single_blocks.2.`, `single_blocks.3.`, `single_blocks.4.`, `single_blocks.5.`, `single_blocks.6.`, `single_blocks.7.`, `single_blocks.8.`, `single_blocks.9.`, `single_blocks.10.`, `single_blocks.11.`, `single_blocks.12.`, `single_blocks.13.`, `single_blocks.14.`, `single_blocks.15.`, `single_blocks.16.`, `single_blocks.17.`, `single_blocks.18.`, `single_blocks.19.`, `single_blocks.20.`, `single_blocks.21.`, `single_blocks.22.`, `single_blocks.23.`, `single_blocks.24.`, `single_blocks.25.`, `single_blocks.26.`, `single_blocks.27.`, `single_blocks.28.`, `single_blocks.29.`, `single_blocks.30.`, `single_blocks.31.`, `single_blocks.32.`, `single_blocks.33.`, `single_blocks.34.`, `single_blocks.35.`, `single_blocks.36.`, `single_blocks.37.`, `final_layer.` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ModelMergeKrea2`<br>comfy_extras.nodes_model_merging_model_specific | `model_settings` | `model1`, `model2`, `first.`, `tmlp.`, `txtmlp.`, `tproj.`, `txtfusion.layerwise_blocks.0.`, `txtfusion.layerwise_blocks.1.`, `txtfusion.projector.`, `txtfusion.refiner_blocks.0.`, `txtfusion.refiner_blocks.1.`, `blocks.0.`, `blocks.1.`, `blocks.2.`, `blocks.3.`, `blocks.4.`, `blocks.5.`, `blocks.6.`, `blocks.7.`, `blocks.8.`, `blocks.9.`, `blocks.10.`, `blocks.11.`, `blocks.12.`, `blocks.13.`, `blocks.14.`, `blocks.15.`, `blocks.16.`, `blocks.17.`, `blocks.18.`, `blocks.19.`, `blocks.20.`, `blocks.21.`, `blocks.22.`, `blocks.23.`, `blocks.24.`, `blocks.25.`, `blocks.26.`, `blocks.27.`, `last.` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ModelMergeLTXV`<br>comfy_extras.nodes_model_merging_model_specific | `model_settings` | `model1`, `model2`, `patchify_proj.`, `adaln_single.`, `caption_projection.`, `transformer_blocks.0.`, `transformer_blocks.1.`, `transformer_blocks.2.`, `transformer_blocks.3.`, `transformer_blocks.4.`, `transformer_blocks.5.`, `transformer_blocks.6.`, `transformer_blocks.7.`, `transformer_blocks.8.`, `transformer_blocks.9.`, `transformer_blocks.10.`, `transformer_blocks.11.`, `transformer_blocks.12.`, `transformer_blocks.13.`, `transformer_blocks.14.`, `transformer_blocks.15.`, `transformer_blocks.16.`, `transformer_blocks.17.`, `transformer_blocks.18.`, `transformer_blocks.19.`, `transformer_blocks.20.`, `transformer_blocks.21.`, `transformer_blocks.22.`, `transformer_blocks.23.`, `transformer_blocks.24.`, `transformer_blocks.25.`, `transformer_blocks.26.`, `transformer_blocks.27.`, `scale_shift_table`, `proj_out.` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ModelMergeMochiPreview`<br>comfy_extras.nodes_model_merging_model_specific | `model_settings` | `model1`, `model2`, `pos_frequencies.`, `t_embedder.`, `t5_y_embedder.`, `t5_yproj.`, `blocks.0.`, `blocks.1.`, `blocks.2.`, `blocks.3.`, `blocks.4.`, `blocks.5.`, `blocks.6.`, `blocks.7.`, `blocks.8.`, `blocks.9.`, `blocks.10.`, `blocks.11.`, `blocks.12.`, `blocks.13.`, `blocks.14.`, `blocks.15.`, `blocks.16.`, `blocks.17.`, `blocks.18.`, `blocks.19.`, `blocks.20.`, `blocks.21.`, `blocks.22.`, `blocks.23.`, `blocks.24.`, `blocks.25.`, `blocks.26.`, `blocks.27.`, `blocks.28.`, `blocks.29.`, `blocks.30.`, `blocks.31.`, `blocks.32.`, `blocks.33.`, `blocks.34.`, `blocks.35.`, `blocks.36.`, `blocks.37.`, `blocks.38.`, `blocks.39.`, `blocks.40.`, `blocks.41.`, `blocks.42.`, `blocks.43.`, `blocks.44.`, `blocks.45.`, `blocks.46.`, `blocks.47.`, `final_layer.` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ModelMergeQwenImage`<br>comfy_extras.nodes_model_merging_model_specific | `model_settings` | `model1`, `model2`, `pos_embeds.`, `img_in.`, `txt_norm.`, `txt_in.`, `time_text_embed.`, `transformer_blocks.0.`, `transformer_blocks.1.`, `transformer_blocks.2.`, `transformer_blocks.3.`, `transformer_blocks.4.`, `transformer_blocks.5.`, `transformer_blocks.6.`, `transformer_blocks.7.`, `transformer_blocks.8.`, `transformer_blocks.9.`, `transformer_blocks.10.`, `transformer_blocks.11.`, `transformer_blocks.12.`, `transformer_blocks.13.`, `transformer_blocks.14.`, `transformer_blocks.15.`, `transformer_blocks.16.`, `transformer_blocks.17.`, `transformer_blocks.18.`, `transformer_blocks.19.`, `transformer_blocks.20.`, `transformer_blocks.21.`, `transformer_blocks.22.`, `transformer_blocks.23.`, `transformer_blocks.24.`, `transformer_blocks.25.`, `transformer_blocks.26.`, `transformer_blocks.27.`, `transformer_blocks.28.`, `transformer_blocks.29.`, `transformer_blocks.30.`, `transformer_blocks.31.`, `transformer_blocks.32.`, `transformer_blocks.33.`, `transformer_blocks.34.`, `transformer_blocks.35.`, `transformer_blocks.36.`, `transformer_blocks.37.`, `transformer_blocks.38.`, `transformer_blocks.39.`, `transformer_blocks.40.`, `transformer_blocks.41.`, `transformer_blocks.42.`, `transformer_blocks.43.`, `transformer_blocks.44.`, `transformer_blocks.45.`, `transformer_blocks.46.`, `transformer_blocks.47.`, `transformer_blocks.48.`, `transformer_blocks.49.`, `transformer_blocks.50.`, `transformer_blocks.51.`, `transformer_blocks.52.`, `transformer_blocks.53.`, `transformer_blocks.54.`, `transformer_blocks.55.`, `transformer_blocks.56.`, `transformer_blocks.57.`, `transformer_blocks.58.`, `transformer_blocks.59.`, `proj_out.` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ModelMergeSD1`<br>comfy_extras.nodes_model_merging_model_specific | `model_settings` | `model1`, `model2`, `time_embed.`, `label_emb.`, `input_blocks.0.`, `input_blocks.1.`, `input_blocks.2.`, `input_blocks.3.`, `input_blocks.4.`, `input_blocks.5.`, `input_blocks.6.`, `input_blocks.7.`, `input_blocks.8.`, `input_blocks.9.`, `input_blocks.10.`, `input_blocks.11.`, `middle_block.0.`, `middle_block.1.`, `middle_block.2.`, `output_blocks.0.`, `output_blocks.1.`, `output_blocks.2.`, `output_blocks.3.`, `output_blocks.4.`, `output_blocks.5.`, `output_blocks.6.`, `output_blocks.7.`, `output_blocks.8.`, `output_blocks.9.`, `output_blocks.10.`, `output_blocks.11.`, `out.` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ModelMergeSD2`<br>comfy_extras.nodes_model_merging_model_specific | `model_settings` | `model1`, `model2`, `time_embed.`, `label_emb.`, `input_blocks.0.`, `input_blocks.1.`, `input_blocks.2.`, `input_blocks.3.`, `input_blocks.4.`, `input_blocks.5.`, `input_blocks.6.`, `input_blocks.7.`, `input_blocks.8.`, `input_blocks.9.`, `input_blocks.10.`, `input_blocks.11.`, `middle_block.0.`, `middle_block.1.`, `middle_block.2.`, `output_blocks.0.`, `output_blocks.1.`, `output_blocks.2.`, `output_blocks.3.`, `output_blocks.4.`, `output_blocks.5.`, `output_blocks.6.`, `output_blocks.7.`, `output_blocks.8.`, `output_blocks.9.`, `output_blocks.10.`, `output_blocks.11.`, `out.` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ModelMergeSD35_Large`<br>comfy_extras.nodes_model_merging_model_specific | `model_settings` | `model1`, `model2`, `pos_embed.`, `x_embedder.`, `context_embedder.`, `y_embedder.`, `t_embedder.`, `joint_blocks.0.`, `joint_blocks.1.`, `joint_blocks.2.`, `joint_blocks.3.`, `joint_blocks.4.`, `joint_blocks.5.`, `joint_blocks.6.`, `joint_blocks.7.`, `joint_blocks.8.`, `joint_blocks.9.`, `joint_blocks.10.`, `joint_blocks.11.`, `joint_blocks.12.`, `joint_blocks.13.`, `joint_blocks.14.`, `joint_blocks.15.`, `joint_blocks.16.`, `joint_blocks.17.`, `joint_blocks.18.`, `joint_blocks.19.`, `joint_blocks.20.`, `joint_blocks.21.`, `joint_blocks.22.`, `joint_blocks.23.`, `joint_blocks.24.`, `joint_blocks.25.`, `joint_blocks.26.`, `joint_blocks.27.`, `joint_blocks.28.`, `joint_blocks.29.`, `joint_blocks.30.`, `joint_blocks.31.`, `joint_blocks.32.`, `joint_blocks.33.`, `joint_blocks.34.`, `joint_blocks.35.`, `joint_blocks.36.`, `joint_blocks.37.`, `final_layer.` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ModelMergeSD3_2B`<br>comfy_extras.nodes_model_merging_model_specific | `model_settings` | `model1`, `model2`, `pos_embed.`, `x_embedder.`, `context_embedder.`, `y_embedder.`, `t_embedder.`, `joint_blocks.0.`, `joint_blocks.1.`, `joint_blocks.2.`, `joint_blocks.3.`, `joint_blocks.4.`, `joint_blocks.5.`, `joint_blocks.6.`, `joint_blocks.7.`, `joint_blocks.8.`, `joint_blocks.9.`, `joint_blocks.10.`, `joint_blocks.11.`, `joint_blocks.12.`, `joint_blocks.13.`, `joint_blocks.14.`, `joint_blocks.15.`, `joint_blocks.16.`, `joint_blocks.17.`, `joint_blocks.18.`, `joint_blocks.19.`, `joint_blocks.20.`, `joint_blocks.21.`, `joint_blocks.22.`, `joint_blocks.23.`, `final_layer.` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ModelMergeSDXL`<br>comfy_extras.nodes_model_merging_model_specific | `model_settings` | `model1`, `model2`, `time_embed.`, `label_emb.`, `input_blocks.0`, `input_blocks.1`, `input_blocks.2`, `input_blocks.3`, `input_blocks.4`, `input_blocks.5`, `input_blocks.6`, `input_blocks.7`, `input_blocks.8`, `middle_block.0`, `middle_block.1`, `middle_block.2`, `output_blocks.0`, `output_blocks.1`, `output_blocks.2`, `output_blocks.3`, `output_blocks.4`, `output_blocks.5`, `output_blocks.6`, `output_blocks.7`, `output_blocks.8`, `out.` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ModelMergeSimple`<br>comfy_extras.nodes_model_merging | `model_settings` | `model1`, `model2`, `ratio` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ModelMergeSubtract`<br>comfy_extras.nodes_model_merging | `model_settings` | `model1`, `model2`, `multiplier` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ModelMergeWAN2_1`<br>comfy_extras.nodes_model_merging_model_specific | `model_settings` | `model1`, `model2`, `patch_embedding.`, `time_embedding.`, `time_projection.`, `text_embedding.`, `img_emb.`, `blocks.0.`, `blocks.1.`, `blocks.2.`, `blocks.3.`, `blocks.4.`, `blocks.5.`, `blocks.6.`, `blocks.7.`, `blocks.8.`, `blocks.9.`, `blocks.10.`, `blocks.11.`, `blocks.12.`, `blocks.13.`, `blocks.14.`, `blocks.15.`, `blocks.16.`, `blocks.17.`, `blocks.18.`, `blocks.19.`, `blocks.20.`, `blocks.21.`, `blocks.22.`, `blocks.23.`, `blocks.24.`, `blocks.25.`, `blocks.26.`, `blocks.27.`, `blocks.28.`, `blocks.29.`, `blocks.30.`, `blocks.31.`, `blocks.32.`, `blocks.33.`, `blocks.34.`, `blocks.35.`, `blocks.36.`, `blocks.37.`, `blocks.38.`, `blocks.39.`, `head.` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ModelNoiseScale`<br>comfy_extras.nodes_model_advanced | `model_settings` | `model`, `noise_scale` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ModelPatchLoader`<br>comfy_extras.nodes_model_patch | `processing_settings` | `name` | 0: `MODEL_PATCH` | 保留辅助模型文件和作用设置。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ModelSamplingAuraFlow`<br>comfy_extras.nodes_model_advanced | `model_settings` | `model`, `shift`, `sampling` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ModelSamplingContinuousEDM`<br>comfy_extras.nodes_model_advanced | `model_settings` | `model`, `sampling`, `sigma_max`, `sigma_min` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ModelSamplingContinuousV`<br>comfy_extras.nodes_model_advanced | `model_settings` | `model`, `sampling`, `sigma_max`, `sigma_min` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ModelSamplingDiscrete`<br>comfy_extras.nodes_model_advanced | `model_settings` | `model`, `sampling`, `zsnr` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ModelSamplingFlux`<br>comfy_extras.nodes_model_advanced | `height`, `model_settings`, `width` | `model`, `max_shift`, `base_shift`, `width`, `height` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ModelSamplingLTXV`<br>comfy_extras.nodes_lt | `model_settings` | `model`, `max_shift`, `base_shift`, `latent` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ModelSamplingSD3`<br>comfy_extras.nodes_model_advanced | `model_settings` | `model`, `shift` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ModelSamplingStableCascade`<br>comfy_extras.nodes_model_advanced | `model_settings` | `model`, `shift` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ModelSave`<br>comfy_extras.nodes_model_merging | `processing_settings` | `model`, `filename_prefix` |  | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `MultiGPU_WorkUnits`<br>comfy_extras.nodes_multigpu | `model_settings` | `model`, `max_gpus` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `NAGuidance`<br>comfy_extras.nodes_nag | `model_settings` | `model`, `nag_scale`, `nag_alpha`, `nag_tau` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `OptimalStepsScheduler`<br>comfy_extras.nodes_optimalsteps | `denoise`, `scheduler`, `steps` | `model_type`, `steps`, `denoise` | 0: `SIGMAS` | 读取调度设置；配置步数和下游阶段步数分别展示。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `PairConditioningCombine`<br>comfy_extras.nodes_hooks | `control_settings` | `positive_A`, `negative_A`, `positive_B`, `negative_B` | 0: `CONDITIONING`, 1: `CONDITIONING` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `PairConditioningSetDefaultCombine`<br>comfy_extras.nodes_hooks | `control_settings` | `positive`, `negative`, `positive_DEFAULT`, `negative_DEFAULT`, `hooks` | 0: `CONDITIONING`, 1: `CONDITIONING` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `PairConditioningSetProperties`<br>comfy_extras.nodes_hooks | `control_settings` | `positive_NEW`, `negative_NEW`, `strength`, `set_cond_area`, `mask`, `hooks`, `timesteps` | 0: `CONDITIONING`, 1: `CONDITIONING` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `PairConditioningSetPropertiesAndCombine`<br>comfy_extras.nodes_hooks | `control_settings` | `positive`, `negative`, `positive_NEW`, `negative_NEW`, `strength`, `set_cond_area`, `mask`, `hooks`, `timesteps` | 0: `CONDITIONING`, 1: `CONDITIONING` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `PatchModelAddDownscale`<br>comfy_extras.nodes_model_downscale | `model_settings`, `upscale_method` | `model`, `block_number`, `downscale_factor`, `start_percent`, `end_percent`, `downscale_after_skip`, `downscale_method`, `upscale_method` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `PerpNeg`<br>comfy_extras.nodes_perpneg | `model_settings` | `model`, `empty_conditioning`, `neg_scale` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `PerpNegGuider`<br>comfy_extras.nodes_perpneg | `cfg`, `clip`, `negative`, `positive`, `system_prompt` | `model`, `positive`, `negative`, `empty_conditioning`, `cfg`, `neg_scale` | 0: `GUIDER` | 按输入角色追踪模型和正反向条件，保留多组 CFG。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `PerturbedAttentionGuidance`<br>comfy_extras.nodes_pag | `model_settings` | `model`, `scale` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `PhotoMakerLoader`<br>comfy_extras.nodes_photomaker | `processing_settings` | `photomaker_model_name` | 0: `PHOTOMAKER` | 保留辅助模型文件和作用设置。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `PiDConditioning`<br>comfy_extras.nodes_pid | `control_settings` | `positive`, `latent`, `latent_format`, `degrade_sigma` | 0: `CONDITIONING` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `PolyexponentialScheduler`<br>comfy_extras.nodes_custom_sampler | `scheduler`, `steps` | `steps`, `sigma_max`, `sigma_min`, `rho` | 0: `SIGMAS` | 读取调度设置；配置步数和下游阶段步数分别展示。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `Power Lora Loader (rgthree)`<br>custom_nodes.rgthree-comfy | `lora` | `model`, `clip` | 0: `MODEL`, 1: `CLIP` | 读取启用项、名称及双权重，保留重复应用顺序。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `Power Primitive (rgthree)`<br>custom_nodes.rgthree-comfy | 向消费节点传递属性 |  | 0: `*` | 读取标量输出；特殊随机占位值标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `Power Prompt (rgthree)`<br>custom_nodes.rgthree-comfy | `clip`, `negative`, `positive`, `system_prompt` | `prompt`, `opt_model`, `opt_clip`, `insert_lora`, `insert_embedding`, `insert_saved` | 0: `CONDITIONING`, 1: `MODEL`, 2: `CLIP`, 3: `STRING` | 沿条件用途确定正反向，保留文本通道、系统提示词及编码资源。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `Power Prompt - Simple (rgthree)`<br>custom_nodes.rgthree-comfy | `clip`, `negative`, `positive`, `system_prompt` | `prompt`, `opt_clip`, `insert_embedding`, `insert_saved` | 0: `CONDITIONING`, 1: `STRING` | 沿条件用途确定正反向，保留文本通道、系统提示词及编码资源。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `PreviewImage`<br>nodes | 向消费节点传递属性 | `images` | 0: `IMAGE` | 从图片输入识别输出分支，多输出保留未确定关联。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `PrimitiveBoolean`<br>comfy_extras.nodes_primitive | 向消费节点传递属性 | `value` | 0: `BOOLEAN` | 读取标量输出；特殊随机占位值标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `PrimitiveFloat`<br>comfy_extras.nodes_primitive | 向消费节点传递属性 | `value` | 0: `FLOAT` | 读取标量输出；特殊随机占位值标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `PrimitiveInt`<br>comfy_extras.nodes_primitive | 向消费节点传递属性 | `value` | 0: `INT` | 读取标量输出；特殊随机占位值标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `PrimitiveString`<br>comfy_extras.nodes_primitive | 向消费节点传递属性 | `value` | 0: `STRING` | 读取标量输出；特殊随机占位值标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `PrimitiveStringMultiline`<br>comfy_extras.nodes_primitive | 向消费节点传递属性 | `value` | 0: `STRING` | 读取标量输出；特殊随机占位值标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `Prompt (LoraManager)`<br>custom_nodes.comfyui-lora-manager | `clip`, `negative`, `positive`, `seed`, `system_prompt` | `text`, `clip`, `seed`, `trigger_words1` | 0: `CONDITIONING`, 1: `STRING` | 沿条件用途确定正反向，保留文本通道、系统提示词及编码资源。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `QuadrupleCLIPLoader`<br>comfy_extras.nodes_hidream | `clip` | `clip_name1`, `clip_name2`, `clip_name3`, `clip_name4` | 0: `CLIP` | 读取加载文件字段及显式设置，按资源端口追踪。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `QuadrupleCLIPLoaderGGUF`<br>custom_nodes.ComfyUI-GGUF | `clip` | `clip_name1`, `clip_name2`, `clip_name3`, `clip_name4` | 0: `CLIP` | 读取加载文件字段及显式设置，按资源端口追踪。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `QwenImage21Cache`<br>comfy_extras.nodes_qwen | `model_settings` | `model`, `device`, `dtype` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `QwenImageDiffsynthControlnet`<br>comfy_extras.nodes_model_patch | `control_settings` | `model`, `model_patch`, `vae`, `image`, `strength`, `mask` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `Random Checkpoint Loader (LoraManager)`<br>custom_nodes.comfyui-lora-manager | `clip`, `model`, `vae` | `ckpt_name`, `select_at_random`, `base_model` | 0: `MODEL`, 1: `CLIP`, 2: `VAE`, 3: `STRING` | 按输出端口区分模型、内置编码器与内置 VAE；随机选模结果未保存时标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `Random Unet Loader (LoraManager)`<br>custom_nodes.comfyui-lora-manager | `model` | `unet_name`, `weight_dtype`, `select_at_random`, `base_model` | 0: `MODEL`, 1: `STRING` | 读取加载文件字段及显式设置，按资源端口追踪。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `RandomNoise`<br>comfy_extras.nodes_custom_sampler | `seed` | `noise_seed` | 0: `NOISE` | 读取噪声种子或禁用噪声状态；种子以字符串返回。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `RebatchLatents`<br>comfy_extras.nodes_rebatch | `batch_size`, `processing_settings` | `latents`, `batch_size` | 0: `LATENT` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ReferenceLatent`<br>comfy_extras.nodes_edit_model | `processing_settings` | `conditioning`, `latent` | 0: `CONDITIONING` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ReferenceTimbreAudio`<br>comfy_extras.nodes_ace | `processing_settings` | `conditioning`, `latent` | 0: `CONDITIONING` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `RegexExtract`<br>comfy_extras.nodes_string | 向消费节点传递属性 | `string`, `regex_pattern`, `mode`, `case_insensitive`, `multiline`, `dotall`, `group_index` | 0: `STRING` | 按已登记的纯标量语义解析；依赖外部通配词库的运行结果标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `RegexMatch`<br>comfy_extras.nodes_string | 向消费节点传递属性 | `string`, `regex_pattern`, `case_insensitive`, `multiline`, `dotall` | 0: `BOOLEAN` | 按已登记的纯标量语义解析；依赖外部通配词库的运行结果标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `RegexReplace`<br>comfy_extras.nodes_string | 向消费节点传递属性 | `string`, `regex_pattern`, `replace`, `case_insensitive`, `multiline`, `dotall`, `count` | 0: `STRING` | 按已登记的纯标量语义解析；依赖外部通配词库的运行结果标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `RenormCFG`<br>comfy_extras.nodes_lumina2 | `model_settings` | `model`, `cfg_trunc`, `renorm_cfg` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `RepeatImageBatch`<br>comfy_extras.nodes_images | `processing_settings` | `image`, `amount` | 0: `IMAGE` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `RepeatLatentBatch`<br>nodes | `processing_settings` | `samples`, `amount` | 0: `LATENT` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `RescaleCFG`<br>comfy_extras.nodes_model_advanced | `model_settings` | `model`, `multiplier` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ResizeAndPadImage`<br>comfy_extras.nodes_images | `processing_settings`, `target_height`, `target_width` | `image`, `target_width`, `target_height`, `padding_color`, `interpolation` | 0: `IMAGE` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ResolutionSelector`<br>comfy_extras.nodes_resolution | 向消费节点传递属性 | `aspect_ratio`, `megapixels`, `multiple`, `preview` | 0: `INT`, 1: `INT` | 按已登记的纯标量语义解析；依赖外部通配词库的运行结果标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `SDTurboScheduler`<br>comfy_extras.nodes_custom_sampler | `denoise`, `scheduler`, `steps` | `model`, `steps`, `denoise` | 0: `SIGMAS` | 读取调度设置；配置步数和下游阶段步数分别展示。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `SDXL Empty Latent Image (rgthree)`<br>custom_nodes.rgthree-comfy | `batch_size`, `processing_settings` | `dimensions`, `clip_scale`, `batch_size` | 0: `LATENT`, 1: `INT`, 2: `INT` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `SDXL Power Prompt - Positive (rgthree)`<br>custom_nodes.rgthree-comfy | `clip`, `negative`, `positive`, `system_prompt` | `prompt_g`, `prompt_l`, `opt_model`, `opt_clip`, `opt_clip_width`, `opt_clip_height`, `insert_lora`, `insert_embedding`, `insert_saved`, `target_width`, `target_height`, `crop_width`, `crop_height` | 0: `CONDITIONING`, 1: `MODEL`, 2: `CLIP`, 3: `STRING`, 4: `STRING` | 沿条件用途确定正反向，保留文本通道、系统提示词及编码资源。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `SDXL Power Prompt - Simple / Negative (rgthree)`<br>custom_nodes.rgthree-comfy | `clip`, `negative`, `positive`, `system_prompt` | `prompt_g`, `prompt_l`, `opt_clip`, `opt_clip_width`, `opt_clip_height`, `insert_embedding`, `insert_saved`, `target_width`, `target_height`, `crop_width`, `crop_height` | 0: `CONDITIONING`, 1: `STRING`, 2: `STRING` | 沿条件用途确定正反向，保留文本通道、系统提示词及编码资源。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `SD_4XUpscale_Conditioning`<br>comfy_extras.nodes_sdupscale | `control_settings`, `scale_by` | `images`, `positive`, `negative`, `scale_ratio`, `noise_augmentation` | 0: `CONDITIONING`, 1: `CONDITIONING`, 2: `LATENT` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `SUPIRApply`<br>comfy_extras.nodes_model_patch | `model_settings` | `model`, `model_patch`, `vae`, `image`, `strength_start`, `strength_end`, `restore_cfg`, `restore_cfg_s_tmin` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `SamplerCustom`<br>comfy_extras.nodes_custom_sampler | `add_noise`, `batch_size`, `cfg`, `height`, `model`, `negative`, `positive`, `seed`, `stage_steps`, `width` | `model`, `add_noise`, `noise_seed`, `cfg`, `positive`, `negative`, `sampler`, `sigmas`, `latent_image` | 0: `LATENT`, 1: `LATENT` | 读取采样字段并沿条件、模型、噪声、调度器和潜空间输入追踪；阶段步数单独推导。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `SamplerCustomAdvanced`<br>comfy_extras.nodes_custom_sampler | `batch_size`, `height`, `model`, `negative`, `positive`, `stage_steps`, `width` | `noise`, `guider`, `sampler`, `sigmas`, `latent_image` | 0: `LATENT`, 1: `LATENT` | 读取采样字段并沿条件、模型、噪声、调度器和潜空间输入追踪；阶段步数单独推导。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `SamplerDPMAdaptative`<br>comfy_extras.nodes_custom_sampler | `sampler` | `order`, `rtol`, `atol`, `h_init`, `pcoeff`, `icoeff`, `dcoeff`, `accept_safety`, `eta`, `s_noise` | 0: `SAMPLER` | 读取采样器名称或专用采样器类型及参数。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `SamplerDPMPP_2M_SDE`<br>comfy_extras.nodes_custom_sampler | `sampler` | `solver_type`, `eta`, `s_noise`, `noise_device` | 0: `SAMPLER` | 读取采样器名称或专用采样器类型及参数。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `SamplerDPMPP_2S_Ancestral`<br>comfy_extras.nodes_custom_sampler | `sampler` | `eta`, `s_noise` | 0: `SAMPLER` | 读取采样器名称或专用采样器类型及参数。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `SamplerDPMPP_3M_SDE`<br>comfy_extras.nodes_custom_sampler | `sampler` | `eta`, `s_noise`, `noise_device` | 0: `SAMPLER` | 读取采样器名称或专用采样器类型及参数。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `SamplerDPMPP_SDE`<br>comfy_extras.nodes_custom_sampler | `sampler` | `eta`, `s_noise`, `r`, `noise_device` | 0: `SAMPLER` | 读取采样器名称或专用采样器类型及参数。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `SamplerER_SDE`<br>comfy_extras.nodes_custom_sampler | `sampler` | `solver_type`, `max_stage`, `eta`, `s_noise` | 0: `SAMPLER` | 读取采样器名称或专用采样器类型及参数。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `SamplerEulerAncestral`<br>comfy_extras.nodes_custom_sampler | `sampler` | `eta`, `s_noise` | 0: `SAMPLER` | 读取采样器名称或专用采样器类型及参数。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `SamplerEulerAncestralCFGPP`<br>comfy_extras.nodes_custom_sampler | `sampler` | `eta`, `s_noise` | 0: `SAMPLER` | 读取采样器名称或专用采样器类型及参数。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `SamplerEulerCFGpp`<br>comfy_extras.nodes_advanced_samplers | `sampler` | `version` | 0: `SAMPLER` | 读取采样器名称或专用采样器类型及参数。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `SamplerLCM`<br>comfy_extras.nodes_advanced_samplers | `sampler` | `s_noise`, `s_noise_end`, `noise_clip_std` | 0: `SAMPLER` | 读取采样器名称或专用采样器类型及参数。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `SamplerLCMUpscale`<br>comfy_extras.nodes_advanced_samplers | `sampler`, `scale_by`, `upscale_method` | `scale_ratio`, `scale_steps`, `upscale_method` | 0: `SAMPLER` | 读取采样器名称或专用采样器类型及参数。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `SamplerLMS`<br>comfy_extras.nodes_custom_sampler | `sampler` | `order` | 0: `SAMPLER` | 读取采样器名称或专用采样器类型及参数。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `SamplerSASolver`<br>comfy_extras.nodes_custom_sampler | `sampler` | `model`, `eta`, `sde_start_percent`, `sde_end_percent`, `s_noise`, `predictor_order`, `corrector_order`, `use_pece`, `simple_order_2` | 0: `SAMPLER` | 读取采样器名称或专用采样器类型及参数。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `SamplerSEEDS2`<br>comfy_extras.nodes_custom_sampler | `sampler` | `solver_type`, `eta`, `s_noise`, `r` | 0: `SAMPLER` | 读取采样器名称或专用采样器类型及参数。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `Save Image (LoraManager)`<br>custom_nodes.comfyui-lora-manager | 向消费节点传递属性 | `images`, `filename_prefix`, `file_format`, `lossless_webp`, `quality`, `webp_method`, `jpeg_subsampling`, `embed_workflow`, `save_with_metadata`, `add_loras_to_prompt`, `add_counter_to_filename`, `save_as_recipe` | 0: `IMAGE` | 从图片输入识别输出分支，多输出保留未确定关联。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `SaveAnimatedPNG`<br>comfy_extras.nodes_images | 向消费节点传递属性 | `images`, `filename_prefix`, `fps`, `compress_level` | 0: `IMAGE` | 从图片输入识别输出分支，多输出保留未确定关联。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `SaveAnimatedWEBP`<br>comfy_extras.nodes_images | 向消费节点传递属性 | `images`, `filename_prefix`, `fps`, `lossless`, `quality`, `method` | 0: `IMAGE` | 从图片输入识别输出分支，多输出保留未确定关联。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `SaveConditioning`<br>comfy_extras.nodes_cond | `control_settings` | `conditioning`, `filename_prefix` | 0: `CONDITIONING` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `SaveImage`<br>nodes | 向消费节点传递属性 | `images`, `filename_prefix` | 0: `IMAGE` | 从图片输入识别输出分支，多输出保留未确定关联。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `SaveImageAdvanced`<br>comfy_extras.nodes_images | 向消费节点传递属性 | `images`, `filename_prefix`, `format` | 0: `IMAGE` | 从图片输入识别输出分支，多输出保留未确定关联。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `SaveLatent`<br>nodes | `processing_settings` | `samples`, `filename_prefix` | 0: `LATENT` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ScaleROPE`<br>comfy_extras.nodes_rope | `model_settings` | `model`, `scale_x`, `shift_x`, `scale_y`, `shift_y`, `scale_t`, `shift_t` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `Seed (rgthree)`<br>custom_nodes.rgthree-comfy | `seed` | `seed` | 0: `INT` | 读取标量输出；特殊随机占位值标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `SelectCLIPDevice`<br>comfy_extras.nodes_multigpu | `model_settings` | `clip`, `device` | 0: `CLIP` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `SelectModelDevice`<br>comfy_extras.nodes_multigpu | `model_settings` | `model`, `device` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `SelectVAEDevice`<br>comfy_extras.nodes_multigpu | `model_settings` | `vae`, `device` | 0: `VAE` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `SelfAttentionGuidance`<br>comfy_extras.nodes_sag | `model_settings` | `model`, `scale`, `blur_sigma` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `SenseNovaSamplingOptions`<br>comfy_extras.nodes_sensenova | `model_settings` | `model`, `shift` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `SetClipHooks`<br>comfy_extras.nodes_hooks | `model_settings` | `clip`, `apply_to_conds`, `schedule_clip`, `hooks` | 0: `CLIP` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `SetFirstSigma`<br>comfy_extras.nodes_custom_sampler | 向消费节点传递属性 | `sigmas`, `sigma` | 0: `SIGMAS` | 追踪上游调度设置，并按切分端口计算可以确定的序列长度。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `SetHookKeyframes`<br>comfy_extras.nodes_hooks | `processing_settings` | `hooks`, `hook_kf` | 0: `HOOKS` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `SetLatentNoiseMask`<br>nodes | `processing_settings` | `samples`, `mask` | 0: `LATENT` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `SetUnionControlNetType`<br>comfy_extras.nodes_controlnet | `control_settings` | `control_net`, `type` | 0: `CONTROL_NET` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `SkipLayerGuidanceDiT`<br>comfy_extras.nodes_slg | `model_settings` | `model`, `double_layers`, `single_layers`, `scale`, `start_percent`, `end_percent`, `rescaling_scale` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `SkipLayerGuidanceDiTSimple`<br>comfy_extras.nodes_slg | `model_settings` | `model`, `double_layers`, `single_layers`, `start_percent`, `end_percent` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `SkipLayerGuidanceSD3`<br>comfy_extras.nodes_sd3 | `model_settings` | `model`, `layers`, `scale`, `start_percent`, `end_percent` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `SplitSigmas`<br>comfy_extras.nodes_custom_sampler | 向消费节点传递属性 | `sigmas`, `step` | 0: `SIGMAS`, 1: `SIGMAS` | 追踪上游调度设置，并按切分端口计算可以确定的序列长度。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `SplitSigmasDenoise`<br>comfy_extras.nodes_custom_sampler | `denoise` | `sigmas`, `denoise` | 0: `SIGMAS`, 1: `SIGMAS` | 追踪上游调度设置，并按切分端口计算可以确定的序列长度。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `StableCascade_EmptyLatentImage`<br>comfy_extras.nodes_stable_cascade | `batch_size`, `height`, `processing_settings`, `width` | `width`, `height`, `compression`, `batch_size` | 0: `LATENT`, 1: `LATENT` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `StableCascade_StageB_Conditioning`<br>comfy_extras.nodes_stable_cascade | `control_settings` | `conditioning`, `stage_c` | 0: `CONDITIONING` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `StableCascade_StageC_VAEEncode`<br>comfy_extras.nodes_stable_cascade | `processing_settings` | `image`, `vae`, `compression` | 0: `LATENT`, 1: `LATENT` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `StableZero123_Conditioning`<br>comfy_extras.nodes_stable3d | `batch_size`, `control_settings`, `height`, `width` | `clip_vision`, `init_image`, `vae`, `width`, `height`, `batch_size`, `elevation`, `azimuth` | 0: `CONDITIONING`, 1: `CONDITIONING`, 2: `LATENT` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `StringCompare`<br>comfy_extras.nodes_string | 向消费节点传递属性 | `string_a`, `string_b`, `mode`, `case_sensitive` | 0: `BOOLEAN` | 按已登记的纯标量语义解析；依赖外部通配词库的运行结果标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `StringConcatenate`<br>comfy_extras.nodes_string | 向消费节点传递属性 | `string_a`, `string_b`, `delimiter` | 0: `STRING` | 按已登记的纯标量语义解析；依赖外部通配词库的运行结果标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `StringContains`<br>comfy_extras.nodes_string | 向消费节点传递属性 | `string`, `substring`, `case_sensitive` | 0: `BOOLEAN` | 按已登记的纯标量语义解析；依赖外部通配词库的运行结果标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `StringFormat`<br>comfy_extras.nodes_string | 向消费节点传递属性 | `values`, `f_string` | 0: `STRING` | 按已登记的纯标量语义解析；依赖外部通配词库的运行结果标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `StringLength`<br>comfy_extras.nodes_string | 向消费节点传递属性 | `string` | 0: `INT` | 按已登记的纯标量语义解析；依赖外部通配词库的运行结果标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `StringReplace`<br>comfy_extras.nodes_string | 向消费节点传递属性 | `string`, `find`, `replace` | 0: `STRING` | 按已登记的纯标量语义解析；依赖外部通配词库的运行结果标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `StringSubstring`<br>comfy_extras.nodes_string | 向消费节点传递属性 | `string`, `start`, `end` | 0: `STRING` | 按已登记的纯标量语义解析；依赖外部通配词库的运行结果标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `StringTrim`<br>comfy_extras.nodes_string | 向消费节点传递属性 | `string`, `mode` | 0: `STRING` | 按已登记的纯标量语义解析；依赖外部通配词库的运行结果标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `StyleModelApply`<br>nodes | `processing_settings` | `conditioning`, `style_model`, `clip_vision_output`, `strength`, `strength_type` | 0: `CONDITIONING` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `StyleModelLoader`<br>nodes | `processing_settings` | `style_model_name` | 0: `STYLE_MODEL` | 保留辅助模型文件和作用设置。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `T5TokenizerOptions`<br>comfy_extras.nodes_cond | `model_settings` | `clip`, `min_padding`, `min_length` | 0: `CLIP` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `TCFG`<br>comfy_extras.nodes_tcfg | `model_settings` | `model` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `TemporalScoreRescaling`<br>comfy_extras.nodes_eps | `model_settings` | `model`, `tsr_k`, `tsr_sigma` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `Text (LoraManager)`<br>custom_nodes.comfyui-lora-manager | `seed` | `text`, `seed` | 0: `STRING` | 按已登记的纯标量语义解析；依赖外部通配词库的运行结果标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `TextEncodeBooguEdit`<br>comfy_extras.nodes_boogu | `clip`, `negative`, `positive`, `system_prompt` | `clip`, `prompt`, `negative_prompt`, `vae`, `images` | 0: `CONDITIONING`, 1: `CONDITIONING` | 沿条件用途确定正反向，保留文本通道、系统提示词及编码资源。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `TextEncodeJoyImageEdit`<br>comfy_extras.nodes_joyimage | `clip`, `negative`, `positive`, `system_prompt` | `clip`, `prompt`, `vae`, `images` | 0: `CONDITIONING` | 沿条件用途确定正反向，保留文本通道、系统提示词及编码资源。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `TextEncodeKrea2`<br>custom_nodes.comfyui-krea2-text-encoder | `clip`, `negative`, `positive`, `system_prompt` | `clip`, `prompt`, `system_prompt`, `image1`, `mask1`, `vision_megapixels`, `mask_padding`, `vision_position`, `print_prompt` | 0: `CONDITIONING` | 沿条件用途确定正反向，保留文本通道、系统提示词及编码资源。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `TextEncodeMageFlowEdit`<br>comfy_extras.nodes_mage | `batch_size`, `clip`, `negative`, `positive`, `system_prompt` | `clip`, `prompt`, `negative_prompt`, `images`, `width`, `height`, `batch_size`, `vae` | 0: `CONDITIONING`, 1: `CONDITIONING`, 2: `LATENT` | 沿条件用途确定正反向，保留文本通道、系统提示词及编码资源。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `TextEncodeQwenImage21`<br>comfy_extras.nodes_qwen | `clip`, `negative`, `positive`, `system_prompt` | `clip`, `prompt`, `negative_prompt`, `resolution`, `images`, `vae` | 0: `CONDITIONING`, 1: `CONDITIONING`, 2: `LATENT` | 沿条件用途确定正反向，保留文本通道、系统提示词及编码资源。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `TextEncodeQwenImageEdit`<br>comfy_extras.nodes_qwen | `clip`, `negative`, `positive`, `system_prompt` | `clip`, `prompt`, `vae`, `image` | 0: `CONDITIONING` | 沿条件用途确定正反向，保留文本通道、系统提示词及编码资源。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `TextEncodeQwenImageEditPlus`<br>comfy_extras.nodes_qwen | `clip`, `negative`, `positive`, `system_prompt` | `clip`, `prompt`, `vae`, `image1`, `image2`, `image3` | 0: `CONDITIONING` | 沿条件用途确定正反向，保留文本通道、系统提示词及编码资源。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `TextEncodeZImageOmni`<br>comfy_extras.nodes_zimage | `clip`, `negative`, `positive`, `system_prompt` | `clip`, `prompt`, `auto_resize_images`, `image_encoder`, `vae`, `image1`, `image2`, `image3` | 0: `CONDITIONING` | 沿条件用途确定正反向，保留文本通道、系统提示词及编码资源。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ThresholdMask`<br>comfy_extras.nodes_mask | `processing_settings` | `mask`, `value` | 0: `MASK` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `TomePatchModel`<br>comfy_extras.nodes_tomesd | `model_settings` | `model`, `ratio` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `TorchCompileModel`<br>comfy_extras.nodes_torch_compile | `model_settings` | `model`, `backend` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `TripleCLIPLoader`<br>comfy_extras.nodes_sd3 | `clip` | `clip_name1`, `clip_name2`, `clip_name3` | 0: `CLIP` | 读取加载文件字段及显式设置，按资源端口追踪。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `TripleCLIPLoaderGGUF`<br>custom_nodes.ComfyUI-GGUF | `clip` | `clip_name1`, `clip_name2`, `clip_name3` | 0: `CLIP` | 读取加载文件字段及显式设置，按资源端口追踪。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `TripoSplatSamplingPreview`<br>comfy_extras.nodes_triposplat | `model_settings` | `model`, `vae`, `octree_level`, `num_gaussians`, `yaw`, `pitch`, `point_size` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `UNETLoader`<br>nodes | `model` | `unet_name`, `weight_dtype` | 0: `MODEL` | 读取加载文件字段及显式设置，按资源端口追踪。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `UNetCrossAttentionMultiply`<br>comfy_extras.nodes_attention_multiply | `model_settings` | `model`, `q`, `k`, `v`, `out` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `UNetSelfAttentionMultiply`<br>comfy_extras.nodes_attention_multiply | `model_settings` | `model`, `q`, `k`, `v`, `out` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `UNetTemporalAttentionMultiply`<br>comfy_extras.nodes_attention_multiply | `model_settings` | `model`, `self_structural`, `self_temporal`, `cross_structural`, `cross_temporal` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `USOStyleReference`<br>comfy_extras.nodes_model_patch | `model_settings` | `model`, `model_patch`, `clip_vision_output` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `Unet Loader (LoraManager)`<br>custom_nodes.comfyui-lora-manager | `model` | `unet_name`, `weight_dtype` | 0: `MODEL` | 读取加载文件字段及显式设置，按资源端口追踪。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `UnetLoaderGGUF`<br>custom_nodes.ComfyUI-GGUF | `model` | `unet_name` | 0: `MODEL` | 读取加载文件字段及显式设置，按资源端口追踪。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `UnetLoaderGGUFAdvanced`<br>custom_nodes.ComfyUI-GGUF | `model` | `unet_name`, `dequant_dtype`, `patch_dtype`, `patch_on_device` | 0: `MODEL` | 读取加载文件字段及显式设置，按资源端口追踪。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `UpscaleModelLoader`<br>comfy_extras.nodes_upscale_model | `upscale_model` | `model_name` | 0: `UPSCALE_MODEL` | 读取加载文件字段及显式设置，按资源端口追踪。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `VAEDecode`<br>nodes | `processing_settings` | `samples`, `vae` | 0: `IMAGE` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `VAEDecodeTiled`<br>nodes | `processing_settings` | `samples`, `vae`, `tile_size`, `overlap`, `temporal_size`, `temporal_overlap` | 0: `IMAGE` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `VAEEncode`<br>nodes | `processing_settings` | `pixels`, `vae` | 0: `LATENT` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `VAEEncodeForInpaint`<br>nodes | `grow_mask_by`, `processing_settings` | `pixels`, `vae`, `mask`, `grow_mask_by` | 0: `LATENT` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `VAEEncodeTiled`<br>nodes | `processing_settings` | `pixels`, `vae`, `tile_size`, `overlap`, `temporal_size`, `temporal_overlap` | 0: `LATENT` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `VAELoader`<br>nodes | `vae` | `vae_name` | 0: `VAE` | 读取加载文件字段及显式设置，按资源端口追踪。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `VAESave`<br>comfy_extras.nodes_model_merging | `processing_settings` | `vae`, `filename_prefix` |  | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `VPScheduler`<br>comfy_extras.nodes_custom_sampler | `scheduler`, `steps` | `steps`, `beta_d`, `beta_min`, `eps_s` | 0: `SIGMAS` | 读取调度设置；配置步数和下游阶段步数分别展示。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `VideoLinearCFGGuidance`<br>comfy_extras.nodes_video_model | `model_settings` | `model`, `min_cfg` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `VideoTriangleCFGGuidance`<br>comfy_extras.nodes_video_model | `model_settings` | `model`, `min_cfg` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `WanAnimate2Cache`<br>comfy_extras.nodes_wan | `model_settings` | `model`, `device`, `dtype` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `WanContextWindowsManual`<br>comfy_extras.nodes_context_windows | `model_settings` | `model`, `context_length`, `context_overlap`, `context_schedule`, `context_stride`, `closed_loop`, `fuse_method`, `freenoise`, `retain_first_frame`, `split_conds_to_windows` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `WanUni3CControlnetApply`<br>comfy_extras.nodes_model_patch | `control_settings` | `model`, `model_patch`, `vae`, `render_video`, `strength`, `start_percent`, `end_percent` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `ZImageFunControlnet`<br>comfy_extras.nodes_model_patch | `control_settings` | `model`, `model_patch`, `vae`, `strength`, `image`, `inpaint_image`, `mask` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `unCLIPCheckpointLoader`<br>nodes | `clip`, `model`, `vae` | `ckpt_name` | 0: `MODEL`, 1: `CLIP`, 2: `VAE`, 3: `CLIP_VISION` | 按输出端口区分模型、内置编码器与内置 VAE；随机选模结果未保存时标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `unCLIPConditioning`<br>nodes | `control_settings` | `conditioning`, `clip_vision_output`, `strength`, `noise_augmentation` | 0: `CONDITIONING` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |
| `wanBlockSwap`<br>comfy_extras.nodes_nop | `model_settings` | `model` | 0: `MODEL` | 按数据类型追踪输入资源，保留变换设置；图内明确尺寸可推导，外部图片/模型输出尺寸标未知。<br>外部数据、运行时选择及模型相关输出未保存时，保留配置与未知原因。<br>测试：`tests/test_execution_graph.py` |

## 节点运行计时

| 节点 | 计时类别 | 内部计时范围 |
|---|---|---|
| `APG` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `AddNoise` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `AlignYourStepsScheduler` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `AnimaLLLiteApply` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `Any Switch (rgthree)` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `BasicGuider` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `BasicScheduler` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `BetaSamplingScheduler` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `BlockSparseAttention` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `CFGGuider` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `CFGNorm` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `CFGOverride` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `CFGZeroStar` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `CLIPAttentionMultiply` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `CLIPLoader` | `model_loading` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `CLIPLoaderGGUF` | `model_loading` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `CLIPMergeAdd` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `CLIPMergeSimple` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `CLIPMergeSubtract` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `CLIPSave` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `CLIPSetLastLayer` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `CLIPTextEncode` | `text_encoding` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `CLIPTextEncodeControlnet` | `text_encoding` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `CLIPTextEncodeFlux` | `text_encoding` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `CLIPTextEncodeHiDream` | `text_encoding` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `CLIPTextEncodeHunyuanDiT` | `text_encoding` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `CLIPTextEncodeKandinsky5` | `text_encoding` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `CLIPTextEncodeLumina2` | `text_encoding` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `CLIPTextEncodePixArtAlpha` | `text_encoding` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `CLIPTextEncodeSD3` | `text_encoding` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `CLIPTextEncodeSDXL` | `text_encoding` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `CLIPTextEncodeSDXLRefiner` | `text_encoding` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `CLIPVisionEncode` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `CLIPVisionLoader` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `Canny` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `CaseConverter` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `Checkpoint Loader (LoraManager)` | `model_loading` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `CheckpointLoader` | `model_loading` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `CheckpointLoaderSimple` | `model_loading` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `CheckpointSave` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ChromaRadianceOptions` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `CombineHooks2` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `CombineHooks4` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `CombineHooks8` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ComfyAndNode` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ComfyNotNode` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ComfyOrNode` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ComfySwitchNode` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ConditioningAverage` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ConditioningCombine` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ConditioningConcat` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ConditioningLoader` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ConditioningMultiply` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ConditioningSetArea` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ConditioningSetAreaPercentage` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ConditioningSetAreaPercentageVideo` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ConditioningSetAreaStrength` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ConditioningSetDefaultCombine` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ConditioningSetMask` | `postprocess` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ConditioningSetProperties` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ConditioningSetPropertiesAndCombine` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ConditioningSetTimestepRange` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ConditioningTimestepsRange` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ConditioningZeroOut` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `Context (rgthree)` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `Context Big (rgthree)` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `Context Merge (rgthree)` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `Context Merge Big (rgthree)` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `Context Switch (rgthree)` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `Context Switch Big (rgthree)` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ContextWindowsManual` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ControlNetApply` | `postprocess` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ControlNetApplyAdvanced` | `postprocess` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ControlNetApplySD3` | `postprocess` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ControlNetInpaintingAliMamaApply` | `postprocess` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ControlNetLoader` | `model_loading` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ConvertArrayToString` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ConvertDictionaryToString` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `Create Hook LoRA (LoraManager)` | `lora_application` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `CreateHookKeyframe` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `CreateHookKeyframesFromFloats` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `CreateHookKeyframesInterpolated` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `CreateHookLora` | `lora_application` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `CreateHookLoraModelOnly` | `lora_application` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `CustomCombo` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `DiffControlNetLoader` | `model_loading` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `DifferentialDiffusion` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `DiffusersLoader` | `model_loading` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `DisableNoise` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `DualCFGGuider` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `DualCLIPLoader` | `model_loading` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `DualCLIPLoaderGGUF` | `model_loading` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `DualModelGuider` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `EasyCache` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `EmptyFlux2LatentImage` | `postprocess` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `EmptyHunyuanImageLatent` | `postprocess` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `EmptyImage` | `postprocess` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `EmptyLatentImage` | `postprocess` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `EmptyQwenImageLayeredLatentImage` | `postprocess` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `EmptySD3LatentImage` | `postprocess` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `Epsilon Scaling` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ExponentialScheduler` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ExtendIntermediateSigmas` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `FlipSigmas` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `Flux2Scheduler` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `FluxDisableGuidance` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `FluxGuidance` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `FluxKVCache` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `FluxKontextImageScale` | `postprocess` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `FluxKontextMultiReferenceLatentMethod` | `postprocess` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `FreSca` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `FreeU` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `FreeU_V2` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `GITSScheduler` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `GLIGENLoader` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `GLIGENTextBoxApply` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `GetImageSize` | `postprocess` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `GrowMask` | `postprocess` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `HiDreamO1PatchSeamSmoothing` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `HyperTile` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `HypernetworkLoader` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `Ideogram4Scheduler` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `Image Inset Crop (rgthree)` | `postprocess` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `Image Resize (rgthree)` | `postprocess` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `Image or Latent Size (rgthree)` | `postprocess` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ImageAddNoise` | `postprocess` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ImageBatch` | `postprocess` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ImageColorSpace` | `postprocess` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ImageCompositeMasked` | `postprocess` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ImageCrop` | `postprocess` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ImageFlip` | `postprocess` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ImageFromBatch` | `postprocess` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ImageInvert` | `postprocess` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ImageOnlyCheckpointLoader` | `model_loading` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ImagePadForOutpaint` | `postprocess` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ImageRotate` | `postprocess` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ImageScale` | `postprocess` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ImageScaleBy` | `postprocess` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ImageScaleToTotalPixels` | `postprocess` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ImageUpscaleWithModel` | `postprocess` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `InpaintModelConditioning` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `InstructPixToPixConditioning` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `InvertMask` | `postprocess` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `JoinImageWithAlpha` | `postprocess` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `JsonExtractString` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `KSampler` | `sampling` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `KSampler Config (rgthree)` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `KSamplerAdvanced` | `sampling` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `KSamplerSelect` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `KarrasScheduler` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `Krea2SystemPrompt` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `LTXVContextWindows` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `LTXVModalityGuidance` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `LTXVSpatioTemporalGuidance` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `LaplaceScheduler` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `LatentAdd` | `postprocess` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `LatentApplyOperation` | `postprocess` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `LatentApplyOperationCFG` | `postprocess` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `LatentBatch` | `postprocess` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `LatentBatchSeedBehavior` | `postprocess` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `LatentBlend` | `postprocess` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `LatentComposite` | `postprocess` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `LatentCompositeMasked` | `postprocess` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `LatentCrop` | `postprocess` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `LatentFlip` | `postprocess` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `LatentFromBatch` | `postprocess` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `LatentInterpolate` | `postprocess` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `LatentMultiply` | `postprocess` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `LatentOperationSharpen` | `postprocess` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `LatentOperationTonemapReinhard` | `postprocess` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `LatentRotate` | `postprocess` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `LatentSubtract` | `postprocess` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `LatentUpscale` | `postprocess` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `LatentUpscaleBy` | `postprocess` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `LatentUpscaleModelLoader` | `model_loading` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `LazyCache` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `LoRA Text Loader (LoraManager)` | `lora_application` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `LoadImage` | `input_control` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `LoadImageMask` | `input_control` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `LoadImageOutput` | `input_control` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `LoadLatent` | `postprocess` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `Lora Cycler (LoraManager)` | `lora_application` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `Lora Loader (LoraManager)` | `lora_application` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `Lora Loader Stack (rgthree)` | `lora_application` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `Lora Randomizer (LoraManager)` | `lora_application` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `Lora Stack Combiner (LoraManager)` | `lora_application` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `Lora Stacker (LoraManager)` | `lora_application` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `LoraLoader` | `lora_application` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `LoraLoaderBypass` | `lora_application` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `LoraLoaderBypassModelOnly` | `lora_application` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `LoraLoaderModelOnly` | `lora_application` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `LoraModelLoader` | `lora_application` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `Mahiro` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ManualSigmas` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `MiniMaxH3AddGuide` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `MiniMaxH3FunControlNetApply` | `postprocess` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `MiniMaxH3SigmaShift` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ModelAttentionBackend` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ModelComputeDtype` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ModelMergeAdd` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ModelMergeAuraflow` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ModelMergeBlocks` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ModelMergeCosmos14B` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ModelMergeCosmos7B` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ModelMergeCosmosPredict2_14B` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ModelMergeCosmosPredict2_2B` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ModelMergeFlux1` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ModelMergeKrea2` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ModelMergeLTXV` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ModelMergeMochiPreview` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ModelMergeQwenImage` | `postprocess` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ModelMergeSD1` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ModelMergeSD2` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ModelMergeSD35_Large` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ModelMergeSD3_2B` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ModelMergeSDXL` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ModelMergeSimple` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ModelMergeSubtract` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ModelMergeWAN2_1` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ModelNoiseScale` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ModelPatchLoader` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ModelSamplingAuraFlow` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ModelSamplingContinuousEDM` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ModelSamplingContinuousV` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ModelSamplingDiscrete` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ModelSamplingFlux` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ModelSamplingLTXV` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ModelSamplingSD3` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ModelSamplingStableCascade` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ModelSave` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `MultiGPU_WorkUnits` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `NAGuidance` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `OptimalStepsScheduler` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `PairConditioningCombine` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `PairConditioningSetDefaultCombine` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `PairConditioningSetProperties` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `PairConditioningSetPropertiesAndCombine` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `PatchModelAddDownscale` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `PerpNeg` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `PerpNegGuider` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `PerturbedAttentionGuidance` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `PhotoMakerLoader` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `PiDConditioning` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `PolyexponentialScheduler` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `Power Lora Loader (rgthree)` | `lora_application` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `Power Primitive (rgthree)` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `Power Prompt (rgthree)` | `text_encoding` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `Power Prompt - Simple (rgthree)` | `text_encoding` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `PreviewImage` | `image_save` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `PrimitiveBoolean` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `PrimitiveFloat` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `PrimitiveInt` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `PrimitiveString` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `PrimitiveStringMultiline` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `Prompt (LoraManager)` | `text_encoding` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `QuadrupleCLIPLoader` | `model_loading` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `QuadrupleCLIPLoaderGGUF` | `model_loading` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `QwenImage21Cache` | `postprocess` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `QwenImageDiffsynthControlnet` | `postprocess` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `Random Checkpoint Loader (LoraManager)` | `model_loading` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `Random Unet Loader (LoraManager)` | `model_loading` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `RandomNoise` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `RebatchLatents` | `postprocess` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ReferenceLatent` | `postprocess` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ReferenceTimbreAudio` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `RegexExtract` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `RegexMatch` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `RegexReplace` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `RenormCFG` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `RepeatImageBatch` | `postprocess` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `RepeatLatentBatch` | `postprocess` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `RescaleCFG` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ResizeAndPadImage` | `postprocess` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ResolutionSelector` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `SDTurboScheduler` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `SDXL Empty Latent Image (rgthree)` | `postprocess` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `SDXL Power Prompt - Positive (rgthree)` | `text_encoding` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `SDXL Power Prompt - Simple / Negative (rgthree)` | `text_encoding` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `SD_4XUpscale_Conditioning` | `postprocess` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `SUPIRApply` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `SamplerCustom` | `sampling` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `SamplerCustomAdvanced` | `sampling` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `SamplerDPMAdaptative` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `SamplerDPMPP_2M_SDE` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `SamplerDPMPP_2S_Ancestral` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `SamplerDPMPP_3M_SDE` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `SamplerDPMPP_SDE` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `SamplerER_SDE` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `SamplerEulerAncestral` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `SamplerEulerAncestralCFGPP` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `SamplerEulerCFGpp` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `SamplerLCM` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `SamplerLCMUpscale` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `SamplerLMS` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `SamplerSASolver` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `SamplerSEEDS2` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `Save Image (LoraManager)` | `image_save` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `SaveAnimatedPNG` | `image_save` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `SaveAnimatedWEBP` | `image_save` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `SaveConditioning` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `SaveImage` | `image_save` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `SaveImageAdvanced` | `image_save` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `SaveLatent` | `postprocess` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ScaleROPE` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `Seed (rgthree)` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `SelectCLIPDevice` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `SelectModelDevice` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `SelectVAEDevice` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `SelfAttentionGuidance` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `SenseNovaSamplingOptions` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `SetClipHooks` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `SetFirstSigma` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `SetHookKeyframes` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `SetLatentNoiseMask` | `postprocess` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `SetUnionControlNetType` | `postprocess` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `SkipLayerGuidanceDiT` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `SkipLayerGuidanceDiTSimple` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `SkipLayerGuidanceSD3` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `SplitSigmas` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `SplitSigmasDenoise` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `StableCascade_EmptyLatentImage` | `postprocess` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `StableCascade_StageB_Conditioning` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `StableCascade_StageC_VAEEncode` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `StableZero123_Conditioning` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `StringCompare` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `StringConcatenate` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `StringContains` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `StringFormat` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `StringLength` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `StringReplace` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `StringSubstring` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `StringTrim` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `StyleModelApply` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `StyleModelLoader` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `T5TokenizerOptions` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `TCFG` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `TemporalScoreRescaling` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `Text (LoraManager)` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `TextEncodeBooguEdit` | `text_encoding` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `TextEncodeJoyImageEdit` | `text_encoding` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `TextEncodeKrea2` | `text_encoding` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `TextEncodeMageFlowEdit` | `text_encoding` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `TextEncodeQwenImage21` | `text_encoding` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `TextEncodeQwenImageEdit` | `text_encoding` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `TextEncodeQwenImageEditPlus` | `text_encoding` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `TextEncodeZImageOmni` | `text_encoding` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ThresholdMask` | `postprocess` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `TomePatchModel` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `TorchCompileModel` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `TripleCLIPLoader` | `model_loading` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `TripleCLIPLoaderGGUF` | `model_loading` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `TripoSplatSamplingPreview` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `UNETLoader` | `model_loading` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `UNetCrossAttentionMultiply` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `UNetSelfAttentionMultiply` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `UNetTemporalAttentionMultiply` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `USOStyleReference` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `Unet Loader (LoraManager)` | `model_loading` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `UnetLoaderGGUF` | `model_loading` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `UnetLoaderGGUFAdvanced` | `model_loading` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `UpscaleModelLoader` | `model_loading` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `VAEDecode` | `vae_decode` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `VAEDecodeTiled` | `vae_decode` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `VAEEncode` | `vae_encode` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `VAEEncodeForInpaint` | `vae_encode` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `VAEEncodeTiled` | `vae_encode` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `VAELoader` | `model_loading` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `VAESave` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `VPScheduler` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `VideoLinearCFGGuidance` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `VideoTriangleCFGGuidance` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `WanAnimate2Cache` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `WanContextWindowsManual` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `WanUni3CControlnetApply` | `postprocess` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `ZImageFunControlnet` | `postprocess` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `unCLIPCheckpointLoader` | `model_loading` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `unCLIPConditioning` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |
| `wanBlockSwap` | `node_other` | 扩展内部绕过标准函数的子阶段不单独计时；节点调用仍计时。 |

## 核查与测试

- `python scripts/metadata_support.py --check`：检查生成清单与注册表一致。
- `python scripts/metadata_support.py --compare-url http://127.0.0.1:8000`：检查节点增减、输入类型和输出端口变化。
- `python -m unittest discover -s tests -v`：验证属性、阶段、图片封装、任务状态与数据库并发。
- `tests/test_execution_graph.py` 覆盖节点语义与连接；`tests/test_image_utils.py` 覆盖封装；`tests/test_metadata_indexer.py` 覆盖缓存提交。
- 新增节点适配时更新注册表、契约快照、语义测试，再重新生成本清单。

## 范围

快照同时保留官方在线服务、视频、音频和三维节点用于版本对比。本轮登记以本地图片参数及其传递节点为对象，未登记节点通过侧边栏诊断显示。
