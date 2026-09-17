#!/usr/bin/env python3
import os, json, pathlib, subprocess, hashlib, time
PREFERRED=['/generate','/chat','/predict','/respond','/infer','/run']
def run(cmd, timeout=240): return subprocess.run(cmd,capture_output=True,text=True,timeout=timeout)
def payload_for(spec,prompt):
    payload={}; prompt_set=False
    for p in spec.get('parameters',[]):
        name=p.get('name',''); lname=name.lower(); required=bool(p.get('required',False)); default=p.get('default'); typ=(p.get('type') or {}).get('type')
        if lname in {'message','prompt','text','query','input','instruction','user_message'}: payload[name]=prompt; prompt_set=True
        elif lname in {'chat_history','history','messages'}: payload[name]=[]
        elif lname in {'max_new_tokens','max_tokens','maximum_new_tokens'}: payload[name]=900
        elif lname=='temperature': payload[name]=0.1
        elif lname=='top_p': payload[name]=0.9
        elif lname=='top_k': payload[name]=40
        elif lname in {'system','system_prompt'}: payload[name]='Evidence-grounded education and knowledge transfer analysis. CLAIM<=EVIDENCE.'
        elif required and default is None:
            if typ=='string' and not prompt_set: payload[name]=prompt; prompt_set=True
            else: return None
    return payload if prompt_set else None
def extract(raw):
    raw=raw.strip()
    try:
        obj=json.loads(raw)
        if isinstance(obj,dict):
            for k in ('Response','response','text','output','message'):
                if isinstance(obj.get(k),str): return obj[k].strip()
    except Exception: pass
    return raw
def invoke(space,prompt):
    info=run(['hf-gradio','info',space],120)
    if info.returncode!=0: return False,'',{'stage':'info','error':(info.stderr or info.stdout)[-1200:]}
    try: api=json.loads(info.stdout)
    except Exception as e: return False,'',{'stage':'decode','error':repr(e)}
    endpoints=list(api.items()); endpoints.sort(key=lambda kv:(PREFERRED.index(kv[0]) if kv[0] in PREFERRED else 99,kv[0]))
    errors=[]
    for endpoint,spec in endpoints:
        p=payload_for(spec,prompt)
        if p is None: continue
        pred=run(['hf-gradio','predict',space,endpoint,json.dumps(p,ensure_ascii=False)],240)
        if pred.returncode==0 and (pred.stdout or '').strip():
            text=extract(pred.stdout)
            if text: return True,text,{'stage':'predict','endpoint':endpoint,'sha256':hashlib.sha256(text.encode()).hexdigest()}
        errors.append((pred.stderr or pred.stdout)[-700:])
    return False,'',{'stage':'predict','error':' | '.join(errors[-3:]) or 'No compatible endpoint'}
role=os.getenv('ROLE','UNKNOWN_ROLE'); mission=os.getenv('MISSION','Analyze education and knowledge transfer.'); model=os.getenv('MODEL','huggingface-projects/llama-3.2-3B-Instruct')
prompt=f'''You are the {role} in CEREBRON OMEGA Farm 28 Education & Knowledge Transfer.\nMission: {mission}\nRules: REALITY > COHERENCE; CLAIM <= EVIDENCE; TEACHING != LEARNING; MEMORY != UNDERSTANDING; BENCHMARK != TRANSFER; UNKNOWN REMAINS UNKNOWN.\nReturn assumptions, evidence needed, analysis, failure modes, transferable conclusions, uncertainties, and an Omega-ready summary.'''
ok,text,meta=invoke(model,prompt)
result={'role':role,'model':model,'status':'UNREVIEWED_EXTERNAL_AGENT_OUTPUT' if ok else 'EXTERNAL_INFERENCE_FAILED','inference_success':bool(ok),'output':text if ok else None,'error':None if ok else meta.get('error'),'meta':meta,'timestamp':int(time.time())}
pathlib.Path('outputs').mkdir(exist_ok=True); pathlib.Path(f'outputs/{role}.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)); print(json.dumps({'role':role,'inference_success':bool(ok),'model':model}))
