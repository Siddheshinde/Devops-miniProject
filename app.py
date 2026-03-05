from flask import Flask, jsonify, render_template
from flask_cors import CORS
import psutil, docker, subprocess, json, os, platform

app = Flask(__name__)
CORS(app)

# ─── CPU ───────────────────────────────────────────────
@app.route('/api/cpu')
def get_cpu():
    cpu = psutil.cpu_percent(interval=1)
    freq = psutil.cpu_freq()
    return jsonify({
        'usage_percent': cpu,
        'core_count': psutil.cpu_count(),
        'frequency_mhz': round(freq.current,2) if freq else 0,
        'per_core': psutil.cpu_percent(percpu=True)
    })

# ─── MEMORY ────────────────────────────────────────────
@app.route('/api/memory')
def get_memory():
  m = psutil.virtual_memory()
    s = psutil.swap_memory()
    return jsonify({
        'total_gb': round(m.total/(1024**3),2),
        'used_gb':  round(m.used/(1024**3),2),
        'available_gb': round(m.available/(1024**3),2),
        'usage_percent': m.percent,
        'swap_used_gb': round(s.used/(1024**3),2)
    })

# ─── DISK ──────────────────────────────────────────────
@app.route('/api/disk')
def get_disk():
    d = psutil.disk_usage('/')
    io = psutil.disk_io_counters()
    return jsonify({
        'total_gb': round(d.total/(1024**3),2),
        'used_gb':  round(d.used/(1024**3),2),
        'free_gb':  round(d.free/(1024**3),2),
        'usage_percent': d.percent
    })

# ─── DOCKER CONTAINERS ─────────────────────────────────
@app.route('/api/docker')
def get_docker():
    try:
        client = docker.from_env()
        containers = client.containers.list(all=True)
        return jsonify({
            'count': len(containers),
            'containers': [{'name':c.name,'status':c.status,
                            'image':c.image.tags[0] if c.image.tags else 'unknown'}
                           for c in containers]
        })
    except Exception as e:
        return jsonify({'error':str(e),'containers':[]})

# ─── KUBERNETES PODS ───────────────────────────────────
@app.route('/api/kubernetes')
def get_k8s():
    try:
        r = subprocess.run(['kubectl','get','pods','--all-namespaces','-o','json'],
                           capture_output=True, text=True, timeout=10)
        if r.returncode == 0:
            data = json.loads(r.stdout)
            pods = [{'name':i['metadata']['name'],
                     'namespace':i['metadata']['namespace'],
                     'status':i['status']['phase']}
                    for i in data.get('items',[])]
            return jsonify({'count':len(pods),'pods':pods})
        return jsonify({'error':'kubectl unavailable','pods':[]})
    except Exception as e:
        return jsonify({'error':str(e),'pods':[]})

# ─── SYSTEM INFO (added in Phase 1) ────────────────────
@app.route('/api/system')
def get_system():
    return jsonify({
        'os': platform.system(),
        'hostname': platform.node(),
        'uptime_hours': round((psutil.time.time()-psutil.boot_time())/3600, 1),
        'python_version': platform.python_version()
    })

@app.route('/api/health')
def health(): return jsonify({'status':'ok'})

@app.route('/')
def index(): return render_template('index.html')

if __name__=='__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
