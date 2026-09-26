import importlib.util
import unittest
from pathlib import Path
from typing import Any, Dict


IMAGE_UTILS_PATH = Path(__file__).resolve().parents[1] / "utils" / "image_utils.py"


def load_image_utils_module():
    """直接加载 image_utils.py，避免执行 utils 包入口。"""
    spec = importlib.util.spec_from_file_location("image_utils_under_test", IMAGE_UTILS_PATH)
    image_utils_module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(image_utils_module)
    return image_utils_module


class PositiveAndNegativePromptParseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        image_utils_module = load_image_utils_module()
        cls.parse_positive_and_negative_prompts = staticmethod(
            image_utils_module._parse_positive_and_negative_prompts
        )

    def test_krea2_positive_ignores_earlier_clip_text_encode(self) -> None:
        prompt_json: Dict[str, Any] = {
            "1": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": "earlier clip prompt"},
            },
            "5": {
                "class_type": "TextEncodeKrea2",
                "inputs": {
                    "prompt": "Photo of a man,猎魔人",
                    "system_prompt": "do not use this system prompt",
                },
            },
            "6": {
                "class_type": "ConditioningZeroOut",
                "inputs": {"conditioning": ["5", 0]},
            },
            "10": {
                "class_type": "KSampler",
                "inputs": {
                    "positive": ["5", 0],
                    "negative": ["6", 0],
                },
            },
        }

        positive_prompt, negative_prompt = self.parse_positive_and_negative_prompts(prompt_json)

        self.assertEqual(positive_prompt, "Photo of a man,猎魔人")
        self.assertEqual(negative_prompt, "")

    def test_sampler_links_override_json_order(self) -> None:
        prompt_json: Dict[str, Any] = {
            "1": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": "json order first"},
            },
            "2": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": "json order second"},
            },
            "10": {
                "class_type": "KSampler",
                "inputs": {
                    "positive": ["2", 0],
                    "negative": ["1", 0],
                },
            },
        }

        positive_prompt, negative_prompt = self.parse_positive_and_negative_prompts(prompt_json)

        self.assertEqual(positive_prompt, "json order second")
        self.assertEqual(negative_prompt, "json order first")

    def test_encoder_order_when_no_sampler(self) -> None:
        prompt_json: Dict[str, Any] = {
            "3": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": "first encoder"},
            },
            "8": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": "second encoder"},
            },
        }

        positive_prompt, negative_prompt = self.parse_positive_and_negative_prompts(prompt_json)

        self.assertEqual(positive_prompt, "first encoder")
        self.assertEqual(negative_prompt, "second encoder")


if __name__ == "__main__":
    unittest.main()
