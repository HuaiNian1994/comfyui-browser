"""验证属性实际值、来源与阶段关系。"""
import json
from pathlib import Path
import unittest

from module_loader import load_module

parse = load_module("metadata.graph").parse_execution_graph


def node(cls, **inputs):
    return {"class_type": cls, "inputs": inputs}


def basic_graph():
    return {
        "1": node("CheckpointLoaderSimple", ckpt_name="base.safetensors"),
        "2": node("CLIPTextEncode", clip=["1", 1], text="山间的房屋"),
        "3": node("CLIPTextEncode", clip=["1", 1], text="blur"),
        "4": node("EmptyLatentImage", width=512, height=768, batch_size=2),
        "5": node("KSampler", model=["1", 0], positive=["2", 0], negative=["3", 0], latent_image=["4", 0], seed=18446744073709551615, steps=20, cfg=7.0, sampler_name="euler", scheduler="normal", denoise=1.0),
        "6": node("VAEDecode", samples=["5", 0], vae=["1", 2]),
        "7": node("SaveImage", images=["6", 0], filename_prefix="test"),
    }


def properties(info, stage="5", attr=None):
    values = next(s for s in info["stages"] if s["id"] == stage)["properties"]
    return [p for p in values if attr is None or p["id"] == attr]


class GraphTests(unittest.TestCase):
    def test_official_flux_fixture(self):
        graph = json.loads((Path(__file__).parent / 'fixtures/flux_schnell.json').read_text(encoding='utf-8'))['graph']
        info = parse(graph)
        self.assertEqual(info['parse_status'], 'complete')
        self.assertEqual(properties(info, '13', 'stage_steps')[0]['value'], 4)
        self.assertEqual(properties(info, '13', 'width')[0]['value'], 1024)
        self.assertEqual(properties(info, '13', 'scheduler')[0]['value'], 'simple')

    def test_lora_stack_cycle_produces_local_diagnostic(self):
        graph = basic_graph()
        graph['10'] = node('Lora Stack Combiner (LoraManager)', lora_stack1=['10', 0])
        graph['11'] = node('LoRA Text Loader (LoraManager)', model=['1', 0], lora_syntax='', lora_stack=['10', 0])
        graph['5']['inputs']['model'] = ['11', 0]
        info = parse(graph)
        self.assertTrue(any(d['code'] == 'cycle' for d in info['diagnostics']))

    def test_resize_percentage_and_zero_dimension(self):
        graph = basic_graph()
        graph['10'] = node('Image Resize (rgthree)', image=['6', 0], measurement='percentage', width=50, height=50, fit='contain', method='nearest-exact')
        graph['7']['inputs']['images'] = ['10', 0]
        # 将缩放结果作为下一个采样阶段的输入，验证可静态还原的尺寸。
        graph['11'] = node('VAEEncode', pixels=['10', 0], vae=['1', 2])
        graph['12'] = node('KSampler', **{**graph['5']['inputs'], 'latent_image': ['11', 0]})
        graph['7']['inputs']['images'] = ['12', 0]
        info = parse(graph)
        self.assertEqual(properties(info, '12', 'width')[0]['value'], 256)
        self.assertEqual(properties(info, '12', 'height')[0]['value'], 384)
    def test_basic_values_and_resource_ports(self):
        info = parse(basic_graph())
        self.assertEqual(info["positive_prompt"], "山间的房屋")
        self.assertEqual(info["negative_prompt"], "blur")
        self.assertEqual(properties(info, attr="seed")[0]["value"], "18446744073709551615")
        self.assertEqual(properties(info, attr="stage_steps")[0]["value"], 20)
        self.assertEqual(properties(info, attr="batch_size")[0]["value"], 2)
        self.assertEqual(properties(info, "6", "vae")[0]["value"], {"builtin_checkpoint": "base.safetensors"})
        self.assertEqual(properties(info, attr="model")[0]["sources"][0]["field"], "ckpt_name")

    def test_zero_condition_and_unassigned_text(self):
        graph = basic_graph()
        graph["8"] = node("ConditioningZeroOut", conditioning=["2", 0])
        graph["5"]["inputs"]["negative"] = ["8", 0]
        info = parse(graph)
        self.assertEqual(info["negative_prompt"], "")
        self.assertEqual(properties(info, attr="conditioning")[0]["value"], "zeroed")
        self.assertTrue(any(p["value"] == "blur" for p in info["unassigned"]))

    def test_encoder_order_never_assigns_polarity(self):
        info = parse({"1": node("CLIPTextEncode", text="one"), "2": node("CLIPTextEncode", text="two")})
        self.assertEqual(info["positive_prompt"], "")
        self.assertEqual(info["negative_prompt"], "")
        self.assertEqual([p["value"] for p in info["unassigned"]], ["one", "two"])

    def test_advanced_sampler_clamps_step_range(self):
        graph = basic_graph()
        graph["5"]["class_type"] = "KSamplerAdvanced"
        graph["5"]["inputs"].update(start_at_step=12, end_at_step=10000, add_noise="disable", noise_seed=0)
        info = parse(graph)
        self.assertEqual(properties(info, attr="stage_steps")[0]["value"], 8)
        self.assertIn("0", [p["value"] for p in properties(info, attr="seed")])

    def test_split_sampler_uses_selected_sigma_port(self):
        graph = basic_graph()
        graph.update({"10": node("RandomNoise", noise_seed=123), "11": node("CFGGuider", model=["1", 0], positive=["2", 0], negative=["3", 0], cfg=0), "12": node("KSamplerSelect", sampler_name="euler"), "13": node("BasicScheduler", model=["1", 0], scheduler="normal", steps=20, denoise=1), "14": node("SplitSigmas", sigmas=["13", 0], step=6)})
        graph["5"] = node("SamplerCustomAdvanced", noise=["10", 0], guider=["11", 0], sampler=["12", 0], sigmas=["14", 1], latent_image=["4", 0])
        info = parse(graph)
        self.assertEqual(properties(info, attr="stage_steps")[0]["value"], 14)
        self.assertEqual(properties(info, attr="steps")[0]["value"], 20)
        self.assertEqual(properties(info, attr="cfg")[0]["value"], 0)
        graph["5"]["inputs"]["sigmas"][1] = 0
        self.assertEqual(properties(parse(graph), attr="stage_steps")[0]["value"], 6)

    def test_multistage_keeps_prompts_and_models_separate(self):
        graph = basic_graph()
        graph["8"] = node("KSampler", **{**graph["5"]["inputs"], "latent_image": ["5", 0], "steps": 4, "seed": 99})
        graph["6"]["inputs"]["samples"] = ["8", 0]
        info = parse(graph)
        self.assertEqual(properties(info, "5", "steps")[0]["value"], 20)
        self.assertEqual(properties(info, "8", "steps")[0]["value"], 4)
        self.assertEqual(next(s for s in info["stages"] if s["id"] == "8")["depends_on"], ["5"])

    def test_multiple_outputs_have_no_legacy_prompt_guess(self):
        graph = basic_graph()
        graph["8"] = node("SaveImage", images=["6", 0], filename_prefix="second")
        info = parse(graph)
        self.assertEqual(len(info["branches"]), 2)
        self.assertTrue(all(b["association"] == "unconfirmed" for b in info["branches"]))
        self.assertEqual(info["positive_prompt"], "")

    def test_rgthree_and_lora_manager_structured_inputs(self):
        for cls, extras in [
            ("Power Lora Loader (rgthree)", {"lora_1": {"on": True, "lora": "a.safetensors", "strength": 0, "strengthTwo": 0.7}, "lora_2": {"on": False, "lora": "off", "strength": 1}}),
            ("Lora Loader (LoraManager)", {"text": "unused", "loras": {"__value__": [{"active": True, "name": "a.safetensors", "strength": 0, "clipStrength": 0.7}]}}),
        ]:
            with self.subTest(cls=cls):
                graph = basic_graph()
                graph["9"] = node(cls, model=["1", 0], clip=["1", 1], **extras)
                graph["5"]["inputs"]["model"] = ["9", 0]
                values = properties(parse(graph), attr="lora")
                self.assertEqual(len(values), 1)
                self.assertEqual(values[0]["value"]["strength_clip"], 0.7)
                self.assertEqual(values[0]["value"]["strength_model"], 0)

    def test_unknown_dynamic_model_does_not_claim_configured_name(self):
        graph = basic_graph()
        graph["1"] = node("Random Checkpoint Loader (LoraManager)", ckpt_name="configured", select_at_random=True, base_model="Any")
        info = parse(graph)
        self.assertEqual(properties(info, attr="model")[0]["state"], "unknown")
        self.assertEqual(info["models"], [])

    def test_context_output_port_resolves_seed_and_model(self):
        graph = basic_graph()
        graph["9"] = node("Context (rgthree)", model=["1", 0], seed=42)
        graph["5"]["inputs"].update(model=["9", 1], seed=["9", 8])
        info = parse(graph)
        self.assertEqual(properties(info, attr="seed")[0]["value"], "42")
        self.assertEqual(info["models"], ["base.safetensors"])

    def test_krea_system_prompt_separate_and_string_link(self):
        graph = basic_graph()
        graph["9"] = node("StringConcatenate", string_a="hello", string_b="world", delimiter=" ")
        graph["2"] = node("TextEncodeKrea2", clip=["1", 1], prompt=["9", 0], system_prompt="system")
        info = parse(graph)
        self.assertEqual(info["positive_prompt"], "hello world")
        self.assertEqual(properties(info, attr="system_prompt")[0]["value"], "system")

    def test_broken_cycle_unknown_do_not_block_other_values(self):
        for replacement in [node("UnknownNode", conditioning=["2", 0]), node("ConditioningCombine", conditioning_1=["9", 0], conditioning_2=["missing", 0])]:
            graph = basic_graph()
            graph["9"] = replacement
            graph["5"]["inputs"]["positive"] = ["9", 0]
            info = parse(graph)
            self.assertEqual(info["parse_status"], "partial")
            self.assertEqual(properties(info, attr="seed")[0]["value"], "18446744073709551615")

    def test_controlnet_and_inpaint_properties(self):
        graph = basic_graph()
        graph["8"] = node("ControlNetLoader", control_net_name="depth.safetensors")
        graph["9"] = node("ControlNetApplyAdvanced", positive=["2", 0], negative=["3", 0], control_net=["8", 0], strength=0.5, start_percent=0, end_percent=0.8)
        graph["5"]["inputs"].update(positive=["9", 0], negative=["9", 1])
        info = parse(graph)
        self.assertEqual(info["positive_prompt"], "山间的房屋")
        self.assertEqual(info["negative_prompt"], "blur")
        self.assertEqual(properties(info, attr="controlnet")[0]["value"], "depth.safetensors")
        self.assertTrue(any(p["channel"] == "start_percent" and p["value"] == 0 for p in properties(info, attr="control_settings")))

    def test_latent_upscale_dimensions(self):
        graph = basic_graph()
        graph["9"] = node("LatentUpscaleBy", samples=["4", 0], upscale_method="nearest-exact", scale_by=2)
        graph["5"]["inputs"]["latent_image"] = ["9", 0]
        info = parse(graph)
        self.assertEqual(properties(info, attr="width")[0]["value"], 1024)
        self.assertEqual(properties(info, attr="height")[0]["value"], 1536)

    def test_resolution_selector_restores_real_image_dimensions(self):
        graph = basic_graph()
        graph['9'] = node('ResolutionSelector', aspect_ratio='2:3 (Portrait Photo)', megapixels=1.0, multiple=8, preview='')
        graph['4']['inputs'].update(width=['9', 0], height=['9', 1])
        info = parse(graph)
        self.assertEqual(properties(info, attr='width')[0]['value'], 840)
        self.assertEqual(properties(info, attr='height')[0]['value'], 1256)
        self.assertEqual(properties(info, attr='width')[0]['sources'][0]['node_id'], '9')

    def test_qwen_positive_and_negative_output_ports(self):
        graph = basic_graph()
        graph['2'] = node('TextEncodeQwenImage21', clip=['1', 1], prompt='positive', negative_prompt='negative', resolution=1024, images={}, vae=['1', 2])
        graph['5']['inputs'].update(positive=['2', 0], negative=['2', 1])
        info = parse(graph)
        self.assertEqual(info['positive_prompt'], 'positive')
        self.assertEqual(info['negative_prompt'], 'negative')

    def test_model_merge_retains_models_and_ratio(self):
        graph = basic_graph()
        graph['10'] = node('UNETLoader', unet_name='other.safetensors', weight_dtype='default')
        graph['11'] = node('ModelMergeSimple', model1=['1', 0], model2=['10', 0], ratio=0.25)
        graph['5']['inputs']['model'] = ['11', 0]
        info = parse(graph)
        self.assertEqual(info['models'], ['base.safetensors', 'other.safetensors'])
        self.assertTrue(any(p.get('channel') == 'ratio' and p['value'] == 0.25 for p in properties(info)))

    def test_repeated_lora_keeps_order_and_strength(self):
        graph = basic_graph()
        graph['10'] = node('LoraLoaderModelOnly', model=['1', 0], lora_name='repeat', strength_model=0.2)
        graph['11'] = node('LoraLoaderModelOnly', model=['10', 0], lora_name='repeat', strength_model=0.4)
        graph['5']['inputs']['model'] = ['11', 0]
        info = parse(graph)
        self.assertEqual([p['value']['strength_model'] for p in properties(info, attr='lora')], [0.2, 0.4])

    def test_lora_manager_stack_combiner_and_literal_list(self):
        graph = basic_graph()
        graph['10'] = node('Lora Stacker (LoraManager)', text='', loras={'__value__': [{'name':'first','strength':0.5,'active':True}]})
        graph['11'] = node('Lora Stacker (LoraManager)', text='', loras=[{'name':'second','strength':0.2,'active':True}])
        graph['12'] = node('Lora Stack Combiner (LoraManager)', lora_stack1=['10',0], lora_stack2=['11',0])
        graph['13'] = node('LoRA Text Loader (LoraManager)', model=['1',0], lora_syntax='', lora_stack=['12',0])
        graph['5']['inputs']['model']=['13',0]
        self.assertEqual([p['value']['name'] for p in properties(parse(graph),attr='lora')],['first','second'])


if __name__ == '__main__':
    unittest.main()
