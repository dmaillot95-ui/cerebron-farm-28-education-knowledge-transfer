import json, os, sys, time

role = os.getenv('ROLE', 'UNKNOWN_ROLE')
mission = os.getenv('MISSION', 'Analyze education and knowledge transfer.')
model = os.getenv('MODEL', 'huggingface-projects/llama-3.2-3B-Instruct')

prompt = f'''You are the {role} in CEREBRON OMEGA Farm 28 Education & Knowledge Transfer.
Mission: {mission}
Rules: REALITY > COHERENCE; CLAIM <= EVIDENCE; TEACHING != LEARNING; MEMORY != UNDERSTANDING; BENCHMARK != TRANSFER; UNKNOWN REMAINS UNKNOWN.
Return: assumptions, evidence needed, analysis, failure modes, transferable conclusions, uncertainties, and an Omega-ready summary.
'''

result = {
    'role': role,
    'model': model,
    'status': 'UNREVIEWED_EXTERNAL_AGENT_OUTPUT',
    'inference_success': False,
    'output': None,
    'error': None,
    'timestamp': int(time.time())
}

try:
    from gradio_client import Client
    client = Client(model)
    out = client.predict(prompt, api_name='/chat')
    result['output'] = str(out)
    result['inference_success'] = True
except Exception as e:
    result['error'] = repr(e)

os.makedirs('outputs', exist_ok=True)
with open(f"outputs/{role}.json", 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(json.dumps(result, ensure_ascii=False))
if not result['inference_success']:
    sys.exit(0)
