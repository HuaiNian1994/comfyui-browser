"""在本机 ComfyUI 执行真实计时验收，保留可回读工作流和报告。"""
import argparse
import copy
import json
import time
import urllib.request
from pathlib import Path

BASE = 'http://127.0.0.1:8000'
ARTIFACTS = Path(__file__).resolve().parents[1] / '.timing-e2e'


def request(route, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(BASE + route, data=data, headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req, timeout=30) as response: return json.load(response)


def graph(case):
    batch = 2 if case in ('batch', 'formats') else 1
    seed = {'cold': 12341, 'warm': 12342, 'batch': 12343, 'multi': 12344, 'cached': 12344, 'formats': 12345, 'reload': 12346}[case]
    nodes = {
      '1': {'class_type':'CheckpointLoaderSimple','inputs':{'ckpt_name':'dreamshaper_8.safetensors'}},
      '2': {'class_type':'CLIPTextEncode','inputs':{'clip':['1',1], 'text':'A quiet mountain lake, pine trees, sunrise, landscape painting'}},
      '3': {'class_type':'CLIPTextEncode','inputs':{'clip':['1',1], 'text':'blurry, watermark, text'}},
      '4': {'class_type':'EmptyLatentImage','inputs':{'width':512,'height':512,'batch_size':batch}},
      '5': {'class_type':'KSampler','inputs':{'model':['1',0],'positive':['2',0],'negative':['3',0],'latent_image':['4',0],'seed':seed,'steps':10,'cfg':7.0,'sampler_name':'euler','scheduler':'normal','denoise':1.0}},
      '6': {'class_type':'VAEDecode','inputs':{'samples':['5',0],'vae':['1',2]}},
      '7': {'class_type':'SaveImage','inputs':{'images':['6',0],'filename_prefix':'comfyui-browser-timing-e2e/'+case}},
    }
    if case in ('multi','cached'):
      nodes.update({
        '8': {'class_type':'LatentUpscaleBy','inputs':{'samples':['5',0],'upscale_method':'nearest-exact','scale_by':1.25}},
        '9': {'class_type':'KSampler','inputs':{**nodes['5']['inputs'],'latent_image':['8',0],'seed':12399,'steps':6,'denoise':0.5}},
        '10': {'class_type':'VAEDecode','inputs':{'samples':['9',0],'vae':['1',2]}},
        '11': {'class_type':'SaveImage','inputs':{'images':['10',0],'filename_prefix':'comfyui-browser-timing-e2e/'+case+'_upscaled'}},
      })
    if case == 'formats':
      nodes['8']={'class_type':'SaveAnimatedPNG','inputs':{'images':['6',0],'filename_prefix':'comfyui-browser-timing-e2e/animation','fps':5.0,'compress_level':4}}
      nodes['9']={'class_type':'SaveAnimatedWEBP','inputs':{'images':['6',0],'filename_prefix':'comfyui-browser-timing-e2e/webp','fps':5.0,'lossless':True,'quality':80,'method':'default'}}
    return nodes


def workflow(prompt):
    contracts = request('/object_info')
    nodes=[];links=[];link_id=0
    for index,(key,node) in enumerate(prompt.items()):
      contract=contracts[node['class_type']]
      inputs=[];widgets=[]
      fields={**contract['input'].get('required',{}),**contract['input'].get('optional',{})}
      for name,spec in fields.items():
        if name not in node['inputs']:continue
        value=node['inputs'][name]
        if isinstance(value,list) and len(value)==2 and value[0] in prompt:
          link_id+=1;source,port=value
          data_type=contracts[prompt[source]['class_type']]['output'][port]
          links.append([link_id,int(source),port,int(key),len(inputs),data_type])
          inputs.append({'name':name,'type':data_type,'link':link_id})
        else:
          widgets.append(value)
          if name in ('seed','noise_seed'):widgets.append('fixed')
      outputs=[{'name':name,'type':typ,'links':[]} for name,typ in zip(contract.get('output_name',contract['output']),contract['output'])]
      nodes.append({'id':int(key),'type':node['class_type'],'pos':[80+(index%3)*360,80+(index//3)*260],'size':[320,210],'flags':{},'order':index,'mode':0,'inputs':inputs,'outputs':outputs,'properties':{'Node name for S&R':node['class_type']},'widgets_values':widgets})
    by_id={n['id']:n for n in nodes}
    for link in links:by_id[link[1]]['outputs'][link[2]]['links'].append(link[0])
    return {'last_node_id':max(map(int,prompt)),'last_link_id':link_id,'nodes':nodes,'links':links,'groups':[],'config':{},'extra':{},'version':0.4}


def run(case):
    q=request('/queue')
    if q['queue_running'] or q['queue_pending']:raise RuntimeError('生成队列有其他任务，请空闲后重试')
    ARTIFACTS.mkdir(exist_ok=True)
    prompt=graph(case);canvas=workflow(prompt)
    (ARTIFACTS/(case+'-workflow.json')).write_text(json.dumps(canvas,ensure_ascii=False,indent=2),encoding='utf-8')
    (ARTIFACTS/(case+'-prompt.json')).write_text(json.dumps(prompt,indent=2),encoding='utf-8')
    start=time.perf_counter()
    result=request('/prompt',{'prompt':prompt,'extra_data':{'extra_pnginfo':{'workflow':canvas}}})
    task=result['prompt_id'];print('submitted',case,task,flush=True)
    last_notice=0
    while True:
      history=request('/history/'+task)
      if task in history:break
      elapsed=time.perf_counter()-start
      if elapsed>1800:raise TimeoutError('generation timeout')
      if elapsed-last_notice>20:print('running',round(elapsed,1),'s',flush=True);last_notice=elapsed
      time.sleep(1)
    row=history[task]
    report={'case':case,'task_id':task,'external_elapsed_ms':(time.perf_counter()-start)*1000,'history':row}
    (ARTIFACTS/(case+'-result.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print('finished',row['status']['status_str'],round(report['external_elapsed_ms']/1000,2),'s',flush=True)
    if row['status']['status_str']!='success':raise RuntimeError(str(row['status']['messages'])[:2000])

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('case',choices=['cold','warm','batch','multi','cached','formats','reload']);run(parser.parse_args().case)
