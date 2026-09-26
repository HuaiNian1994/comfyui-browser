import json
import struct
import tempfile
import unittest
import zlib
from pathlib import Path
from PIL import Image
from PIL.PngImagePlugin import PngInfo
from module_loader import load_module
from test_execution_graph import basic_graph

extract = load_module('utils.image_utils').extract_detailed_metadata

class ImageMetadataTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name)

    def test_png_values_and_dimensions(self):
        meta = PngInfo(); meta.add_text('prompt', json.dumps(basic_graph()))
        file = self.path / 'test.png'
        Image.new('RGB', (48, 32)).save(file, pnginfo=meta)
        info = extract(str(file))
        self.assertEqual((info['width'], info['height']), (48, 32))
        self.assertTrue(info['has_metadata'])
        self.assertEqual(info['models'], ['base.safetensors'])

    def test_apng_comf_chunk_after_image_data(self):
        file = self.path / 'test.png'
        Image.new('RGB', (48, 32)).save(file)
        raw = file.read_bytes()
        payload = b'prompt\0' + json.dumps(basic_graph()).encode('latin-1')
        chunk = struct.pack('>I', len(payload)) + b'comf' + payload + struct.pack('>I', zlib.crc32(b'comf'+payload))
        file.write_bytes(raw[:-12] + chunk + raw[-12:])
        self.assertTrue(extract(str(file))['has_metadata'])

    def test_webp_exif(self):
        file = self.path / 'test.webp'
        image = Image.new('RGB', (48, 32)); exif = image.getexif()
        exif[0x0110] = 'prompt:' + json.dumps(basic_graph())
        image.save(file, exif=exif)
        self.assertTrue(extract(str(file))['has_metadata'])

    def test_missing_and_workflow_only(self):
        for workflow in (False, True):
            meta = PngInfo()
            if workflow: meta.add_text('workflow', '{}')
            file = self.path / 'empty.png'
            Image.new('RGB', (48, 32)).save(file, pnginfo=meta)
            info = extract(str(file))
            self.assertEqual(info['parse_status'], 'missing')
            self.assertFalse(info['has_metadata'])
            self.assertEqual(info['width'], 48)

    def test_invalid_graph_preserves_dimensions(self):
        meta = PngInfo(); meta.add_text('prompt', '{broken')
        file = self.path / 'broken.png'
        Image.new('RGB', (48, 32)).save(file, pnginfo=meta)
        info = extract(str(file))
        self.assertEqual(info['parse_status'], 'invalid')
        self.assertEqual(info['height'], 32)

    def test_other_container_basic_information(self):
        file = self.path / 'test.jpg'; Image.new('RGB', (48, 32)).save(file)
        self.assertEqual(extract(str(file))['parse_status'], 'unsupported_container')
