"""计时区间、无损封装与持久任务独立于 ComfyUI 的回归测试。"""
import asyncio
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image, PngImagePlugin
from module_loader import load_module

recording = load_module('timing.recording')
containers = load_module('timing.containers')
storage = load_module('timing.storage')


def record():
    return {'version': 1, 'status': 'success', 'task_id': 'test-task', 'total_ms': 1000,
            'sampling_ms': 600, 'sampling_complete': True, 'iterations_complete': True,
            'iterations': 3, 'spans': []}


def image_bytes(fmt='PNG', animated=False):
    stream = io.BytesIO()
    info = PngImagePlugin.PngInfo()
    info.add_text('prompt', '{"1": {"class_type": "Example"}}')
    info.add_text('workflow', '{"nodes": []}')
    options = {'pnginfo': info} if fmt == 'PNG' else {'exif': b'Exif\x00\x00original'}
    if animated: options.update(save_all=True, append_images=[Image.new('RGB', (16, 16), 'blue')], duration=200, loop=0)
    Image.new('RGB', (16, 16), 'red').save(stream, fmt, **options)
    return stream.getvalue()


class RecordingTests(unittest.TestCase):
    def test_interval_union(self):
        self.assertEqual(recording.union_duration([(0, 10), (3, 4), (5, 12), (20, 25)]), 17)

    def test_nested_and_sampling_summary(self):
        clock = iter([0, 1000000, 2000000, 6000000, 9000000, 10000000]).__next__
        session = recording.Session('task', {'1': {'class_type': 'KSampler'}}, clock=clock)
        with session.span('sampling', kind='node', node_id='1'):
            with session.span('sampling_loop', node_id='1', iterations=2, iterations_known=True): pass
        payload = session.finish(True)
        self.assertEqual(payload['total_ms'], 10)
        self.assertEqual(payload['sampling_ms'], 4)
        self.assertEqual(payload['spans'][0]['self_ms'], 4)
        self.assertEqual(payload['iterations'], 2)

    def test_missing_sampling_and_cache(self):
        session = recording.Session('task', {'1': {'class_type': 'KSampler'}, '2': {}})
        session.cached.add('2')
        with session.span('sampling', kind='node', node_id='1'): pass
        result = session.finish(True)
        self.assertFalse(result['sampling_complete'])
        self.assertIsNone(result['sampling_ms'])
        self.assertEqual(result['nodes'][1]['status'], 'cached')

    def test_failure_and_invalid_values(self):
        session = recording.Session('task', {})
        with self.assertRaises(RuntimeError):
            with session.span('node_other'): raise RuntimeError('expected')
        self.assertIsNone(recording.summary(session.finish(False)))
        for value in [None, float('nan'), -1, True, 10 ** 1000]:
            self.assertIsNone(recording.summary({**record(), 'total_ms': value}))
        self.assertNotIn('iterations', recording.summary({**record(), 'iterations': 0}))

    def test_async_task_context_isolation(self):
        async def run():
            async def task(name):
                session = recording.Session(name, {})
                token = recording.active_session.set(session)
                try:
                    with session.span('node_other'):
                        await asyncio.sleep(0.001)
                        self.assertIs(recording.active_session.get(), session)
                    return session.finish(True)
                finally: recording.active_session.reset(token)
            return await asyncio.gather(task('a'), task('b'))
        a, b = asyncio.run(run())
        self.assertNotEqual(a['task_id'], b['task_id'])
        self.assertGreater(a['spans'][0]['elapsed_ms'], 0)
        self.assertIsNone(a['spans'][0]['parent_id'])


class ContainerTests(unittest.TestCase):
    def test_png_apng_webp_roundtrip_preserves_pixels_and_chunks(self):
        for fmt in ['PNG', 'WEBP']:
            for animated in [False, True]:
                with self.subTest(fmt=fmt, animated=animated):
                    original = image_bytes(fmt, animated)
                    updated = containers.embed_bytes(original, record())
                    self.assertEqual(containers.read_payload(updated), record())
                    self.assertEqual(containers.preserved_chunks(original), containers.preserved_chunks(updated))
                    self.assertEqual(containers.embed_bytes(updated, record()), updated)
                    with Image.open(io.BytesIO(original)) as a, Image.open(io.BytesIO(updated)) as b:
                        self.assertEqual(a.n_frames, b.n_frames)
                        for i in range(a.n_frames):
                            a.seek(i);b.seek(i)
                            self.assertEqual(a.tobytes(), b.tobytes())
                            self.assertEqual(a.info.get('duration'), b.info.get('duration'))
                        self.assertEqual(a.info.get('prompt'), b.info.get('prompt'))
                        self.assertEqual(a.info.get('workflow'), b.info.get('workflow'))
                        self.assertEqual(a.info.get('exif'), b.info.get('exif'))

    def test_existing_xmp_preserved(self):
        data = image_bytes('WEBP')
        packet = b'<x:xmpmeta xmlns:x="adobe:ns:meta/"><rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"><rdf:Description xmlns:d="urn:example" d:rating="5"><d:title>Original</d:title></rdf:Description></rdf:RDF></x:xmpmeta>'
        body = data[8:] + containers.riff_chunk(b'XMP ', packet)
        import struct
        data = b'RIFF' + struct.pack('<I', len(body)) + body
        updated = containers.embed_bytes(data, record())
        root = containers.xmp_root(next(p for k,p,_ in containers.chunks(updated)[1] if k == b'XMP '))
        self.assertEqual(root.find('.//{urn:example}title').text, 'Original')
        self.assertEqual(root.find('.//{'+containers.RDF+'}Description').get('{urn:example}rating'), '5')

    def test_corruption_limits_future_version(self):
        data = image_bytes()
        with self.assertRaises(ValueError): containers.embed_bytes(data[:-1], record())
        with self.assertRaises(ValueError): containers.xmp_root(b'<!DOCTYPE x [<!ENTITY e SYSTEM "file:///secret">]><x/>')
        future = containers.embed_bytes(data, {**record(), 'version': 999})
        with self.assertRaises(ValueError): containers.embed_bytes(future, record())
        with self.assertRaises(ValueError): containers.embed_bytes(data, {**record(), 'extra': 'x' * containers.MAX_METADATA})

    def test_changed_file_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory)/'a.png';p.write_bytes(image_bytes())
            identity=containers.fingerprint(p)
            p.write_bytes(image_bytes(animated=True));updated=p.read_bytes()
            with self.assertRaises(ValueError): containers.write_payload(p, record(), identity)
            self.assertEqual(p.read_bytes(), updated)

    def test_independent_timing_without_prompt(self):
        stream=io.BytesIO();Image.new('RGB',(10,10)).save(stream,'PNG')
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'a.png';p.write_bytes(containers.embed_bytes(stream.getvalue(),record()))
            result=load_module('utils.image_utils').extract_detailed_metadata(str(p))
            self.assertFalse(result['has_metadata'])
            self.assertEqual(result['generation_timing']['total_ms'],1000)


class StorageTests(unittest.TestCase):
    def test_resume_identity_and_callback(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'a.png';p.write_bytes(image_bytes())
            db=Path(directory)/'test.db';calls=[]
            writer=storage.TimingStore(db,start_worker=False)
            writer.persist(record(),[(str(p),'1',containers.fingerprint(p))])
            self.assertTrue(writer.lookup(p)[1])
            writer=storage.TimingStore(db,on_written=lambda path:calls.append(path),start_worker=False)
            self.assertTrue(writer.process_one())
            self.assertEqual(len(calls),1)
            self.assertFalse(writer.lookup(p)[1])
            self.assertEqual(containers.read_payload(p.read_bytes())['output_node_id'],'1')
            p.write_bytes(image_bytes(animated=True))
            self.assertIsNone(writer.lookup(p)[0])

    def test_deleted_and_disabled_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'a.png';p.write_bytes(image_bytes());original=p.read_bytes()
            writer=storage.TimingStore(Path(directory)/'test.db',start_worker=False)
            writer.persist(record(),[(str(p),'1',containers.fingerprint(p))],embed=False)
            self.assertFalse(writer.process_one());self.assertEqual(p.read_bytes(),original)
            writer.persist({**record(),'task_id':'next'},[(str(p),'1',containers.fingerprint(p))])
            p.unlink();writer.process_one()
            with writer.connect() as conn:self.assertEqual(conn.execute("SELECT state FROM timing_files WHERE task_id='next'").fetchone()[0],'failed')

    def test_busy_file_retries_after_delay(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / 'busy.png'
            p.write_bytes(image_bytes())
            writer = storage.TimingStore(Path(directory) / 'test.db', start_worker=False)
            writer.persist(record(), [(str(p), '1', containers.fingerprint(p))])
            with patch.object(storage, 'write_payload', side_effect=PermissionError), patch.object(storage.time, 'time', return_value=100):
                self.assertTrue(writer.process_one())
                self.assertFalse(writer.process_one())
                with writer.connect() as conn:
                    row = conn.execute('SELECT * FROM timing_files').fetchone()
                self.assertEqual(row['next_attempt'], 102)
                self.assertEqual(row['state'], 'pending')
            self.assertTrue(writer.process_one())
            self.assertEqual(containers.read_payload(p.read_bytes())['task_id'], 'test-task')

    def test_restart_recovers_last_attempt_interrupted_by_process_exit(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / 'resume.png'
            p.write_bytes(image_bytes())
            db = Path(directory) / 'test.db'
            writer = storage.TimingStore(db, start_worker=False)
            writer.persist(record(), [(str(p), '1', containers.fingerprint(p))])
            with writer.connect() as conn:
                conn.execute("UPDATE timing_files SET state='writing',attempts=5")
            writer = storage.TimingStore(db, start_worker=False)
            self.assertTrue(writer.process_one())
            self.assertEqual(containers.read_payload(p.read_bytes())['task_id'], 'test-task')

if __name__ == '__main__': unittest.main()
