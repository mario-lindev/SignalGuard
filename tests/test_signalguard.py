import io
import math
import struct
import tempfile
import unittest
import wave
from pathlib import Path
import signalguard as sg

def tone(freq=250, amplitude=.2, seconds=3):
    out=io.BytesIO()
    with wave.open(out,'wb') as f:
        f.setparams((1,2,8000,0,'NONE','not compressed'))
        f.writeframes(b''.join(struct.pack('<h',int(amplitude*32767*math.sin(2*math.pi*freq*i/8000))) for i in range(int(seconds*8000))))
    return out.getvalue()

class AudioTests(unittest.TestCase):
    def test_quality_rejection(self):
        for data in [b'bad',tone(amplitude=0),tone(seconds=1),tone(amplitude=1)]:
            with self.subTest(size=len(data)),self.assertRaises(ValueError):sg.features(data)
    def test_learning_and_deviation(self):
        healthy,_=sg.features(tone())
        changed,_=sg.features(tone(1000))
        self.assertEqual(sg.assess(healthy,[])['status'],'Uncalibrated')
        training=[healthy]*5
        self.assertEqual(sg.assess(healthy,training)['status'],'Within baseline')
        self.assertEqual(sg.assess(changed,training)['status'],'Changed sound')
    def test_persistence_and_foreign_keys(self):
        old=sg.DB
        with tempfile.TemporaryDirectory() as tmp:
            sg.DB=Path(tmp)/'data'/'test.db'
            try:
                with sg.connect() as db:db.execute('INSERT INTO pumps(name,location) VALUES(?,?)',('Well','Village'))
                with sg.connect() as db:self.assertEqual(db.execute('SELECT name FROM pumps').fetchone()[0],'Well')
            finally:sg.DB=old

if __name__=='__main__':unittest.main()
