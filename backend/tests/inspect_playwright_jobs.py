import sqlite3
import json
import hashlib
import os

conn = sqlite3.connect('backend/data/arecavision.db')
c = conn.cursor()
job_ids = ['job-ee740144e1ff', 'job-76038b470349', 'job-494933ad5546', 'job-c4a0c95e530a']

out_list = []
for jid in job_ids:
    c.execute('SELECT id, created_at, result_json FROM jobs WHERE id=?', (jid,))
    r = c.fetchone()
    if r:
        res = json.loads(r[2]) if r[2] else {}
        img_url = res.get('imageUrl', '')
        fname = os.path.basename(img_url)
        local_path = os.path.join('backend/data/uploads', fname)
        h = 'N/A'
        sz = 0
        if os.path.exists(local_path):
            with open(local_path, 'rb') as f:
                b = f.read()
                sz = len(b)
                h = hashlib.sha256(b).hexdigest().upper()
        top3 = [(d['disease'], d['probability']) for d in res.get('differentialDiagnosis', [])[:3]]
        item = {
            'job_id': r[0],
            'created_at': r[1],
            'upload_file': fname,
            'size': sz,
            'sha256': h,
            'disease': res.get('disease'),
            'stage': res.get('stage'),
            'confidence': res.get('confidence'),
            'top3': top3
        }
        out_list.append(item)
        print(f"Job: {item['job_id']} | File: {item['upload_file']} | Size: {item['size']} | SHA256: {item['sha256'][:16]}... | Disease: {item['disease']} | Stage: {item['stage']}")

out_path = 'backend/tests/results/a2_1_playwright_clickthrough.json'
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(out_list, f, indent=2)

print(f"\nSaved A2.1 clickthrough jobs to: {out_path}")
