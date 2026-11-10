"""SignalGuard: local-first acoustic pump monitoring. Python 3.9+, no dependencies."""
import array
import io
import json
import math
import os
import sqlite3
import statistics
import wave
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).parent
DB = ROOT / 'data' / 'signalguard.db'

def connect():
    DB.parent.mkdir(exist_ok=True)
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    db.executescript('''CREATE TABLE IF NOT EXISTS pumps(id INTEGER PRIMARY KEY, name TEXT NOT NULL, location TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS readings(id INTEGER PRIMARY KEY, pump_id INTEGER REFERENCES pumps(id), created TEXT, baseline INTEGER, features TEXT, result TEXT);''')
    db.execute('PRAGMA foreign_keys=ON')
    return db

def features(raw):
    try:
        with wave.open(io.BytesIO(raw), 'rb') as f:
            rate, channels, width, frames = f.getframerate(), f.getnchannels(), f.getsampwidth(), f.getnframes()
            if width != 2 or channels not in (1, 2) or not 8000 <= rate <= 96000:
                raise ValueError('Use a 16-bit PCM WAV, mono or stereo, 8–96 kHz.')
            duration = frames / rate
            if not 3 <= duration <= 30:
                raise ValueError('Record between 3 and 30 seconds.')
            pcm = array.array('h', f.readframes(frames))
            if len(pcm) != frames * channels:
                raise ValueError('Audio file is incomplete.')
    except (wave.Error, EOFError):
        raise ValueError('Could not read audio. Upload a 16-bit PCM WAV file.')
    import sys
    if sys.byteorder != 'little': pcm.byteswap()
    samples = [sum(pcm[i:i+channels]) / (channels * 32768) for i in range(0, len(pcm), channels)]
    rms = math.sqrt(sum(x*x for x in samples) / len(samples))
    clipped = sum(abs(x) > .98 for x in samples) / len(samples)
    if rms < .003: raise ValueError('Recording is too quiet. Move closer and record again.')
    if clipped > .01: raise ValueError('Recording is distorted. Move farther away and record again.')
    # Fixed 8 kHz sampling by linear interpolation, avoiding input-rate-dependent features.
    signal = []
    for i in range(int(duration * 8000)):
        pos = i * rate / 8000
        a = int(pos)
        signal.append(samples[a] * (1-(pos-a)) + samples[min(a+1,len(samples)-1)] * (pos-a))
    values = []
    for offset in range(0, len(signal)-2047, 2048):
        chunk = signal[offset:offset+2048]
        energy = sum(x*x for x in chunk) / len(chunk)
        zcr = sum((a >= 0) != (b >= 0) for a,b in zip(chunk,chunk[1:])) / (len(chunk)-1)
        row = [math.log(energy + 1e-10), zcr]
        for freq in (125, 250, 500, 1000, 2000, 3000):
            coeff = 2 * math.cos(2*math.pi*freq/8000)
            p = q = 0
            for j, x in enumerate(chunk):
                s = x * (.5-.5*math.cos(2*math.pi*j/2047)) + coeff*p-q
                q,p = p,s
            power = max(0, p*p+q*q-coeff*p*q) / (2048**2)
            row.append(math.log(power/(energy+1e-10)+1e-10))
        values.append(row)
    return [statistics.mean(column) for column in zip(*values)], round(duration,1)

def assess(vector, training):
    if len(training) < 5:
        return {'status':'Uncalibrated','score':None,'message':f'Add {5-len(training)} more verified healthy recordings to establish a baseline.'}
    means = [statistics.mean(c) for c in zip(*training)]
    scales = [max(statistics.stdev(c), .15 if i != 1 else .015) for i,c in enumerate(zip(*training))]
    score = math.sqrt(statistics.mean(((x-m)/s)**2 for x,m,s in zip(vector,means,scales)))
    status = 'Changed sound' if score >= 3 else 'Watch' if score >= 2 else 'Within baseline'
    message = {'Changed sound':'Repeat the recording under the same conditions. If the change persists, arrange a technician inspection.', 'Watch':'Repeat the check and review operating conditions, phone position, and background noise.', 'Within baseline':'Sound resembles the healthy baseline. Continue routine checks and physical inspection.'}[status]
    return {'status':status,'score':round(score,2),'message':message}

class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs): super().__init__(*args,directory=str(ROOT/'static'),**kwargs)
    def reply(self, data, status=200):
        body = json.dumps(data).encode()
        self.send_response(status); self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(body))); self.end_headers(); self.wfile.write(body)
    def do_GET(self):
        if self.path == '/api/pumps':
            with connect() as db:
                pumps = [dict(r) for r in db.execute('SELECT * FROM pumps ORDER BY id DESC')]
                for p in pumps:
                    p['readings'] = [dict(r) for r in db.execute('SELECT id,created,baseline,result FROM readings WHERE pump_id=? ORDER BY id DESC',(p['id'],))]
                    for r in p['readings']: r['result'] = json.loads(r['result'])
            return self.reply(pumps)
        super().do_GET()
    def do_POST(self):
        try:
            length = int(self.headers.get('Content-Length','0'))
            if not 0 < length <= 6000000: return self.reply({'error':'Upload must be under 6 MB.'},413)
            raw = self.rfile.read(length)
            if self.path == '/api/pumps':
                data = json.loads(raw)
                name, location = str(data.get('name','')).strip(), str(data.get('location','')).strip()
                if not name or not location or max(len(name),len(location)) > 100: raise ValueError('Enter a pump name and location, each under 100 characters.')
                with connect() as db: db.execute('INSERT INTO pumps(name,location) VALUES(?,?)',(name,location))
                return self.reply({'ok':True},201)
            if self.path == '/api/analyze':
                pump = int(self.headers.get('X-Pump-Id','0'))
                baseline = self.headers.get('X-Baseline') == 'true'
                vector,duration = features(raw)
                with connect() as db:
                    if not db.execute('SELECT id FROM pumps WHERE id=?',(pump,)).fetchone(): raise ValueError('Choose an existing pump.')
                    training = [json.loads(r[0]) for r in db.execute('SELECT features FROM readings WHERE pump_id=? AND baseline=1',(pump,))]
                    result = assess(vector,training)
                    if baseline: result = {'status':'Baseline saved','score':None,'message':f'{len(training)+1} healthy recordings saved. At least 5 are needed; collect 20 or more across representative operating conditions.'}
                    result['duration'] = duration
                    db.execute('INSERT INTO readings(pump_id,created,baseline,features,result) VALUES(?,?,?,?,?)',(pump,datetime.now(timezone.utc).isoformat(),int(baseline),json.dumps(vector),json.dumps(result)))
                return self.reply(result)
            self.reply({'error':'Not found'},404)
        except (ValueError, TypeError, KeyError) as e: self.reply({'error':str(e)},400)
        except Exception: self.reply({'error':'Analysis could not finish. Try again.'},500)

if __name__ == '__main__':
    connect().close()
    print('SignalGuard running at http://localhost:' + os.environ.get('PORT','8000'),flush=True)
    ThreadingHTTPServer((os.environ.get('HOST','127.0.0.1'),int(os.environ.get('PORT','8000'))),Handler).serve_forever()
