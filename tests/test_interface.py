import unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest


class InterfaceTests(unittest.TestCase):
    @unittest.skipUnless((Path(__file__).resolve().parents[1] / 'Forme_data.xlsm').exists(), 'Modèle privé non fourni')
    def test_model_import(self):
        folder = str(Path(__file__).resolve().parents[1])
        code = f'''
import sys, runpy, streamlit as st
from pathlib import Path
folder = Path({folder!r})
sys.path.insert(0, str(folder))
class Upload:
    name = 'Forme_data.xlsm'
    def getvalue(self):
        return (folder / self.name).read_bytes()
st.file_uploader = lambda *args, **kwargs: [Upload()]
runpy.run_path(str(folder / 'app.py'), run_name='__main__')
'''
        app = AppTest.from_string(code, default_timeout=60).run()
        self.assertFalse(app.exception, [e.message for e in app.exception])
        self.assertTrue(any('Aucun point de dérating' in x.value for x in app.info))
        self.assertTrue(any('Informations d’import' in item.label for item in app.sidebar.expander))
        self.assertTrue(app.sidebar.warning)
        self.assertFalse(app.main.warning)
        cycle = next(widget for widget in app.multiselect if widget.label == 'Voies du graphique de cyclage')
        self.assertTrue(cycle.value)
        self.assertTrue(any(widget.value == 'Temperature cycling / thermal shock' for widget in app.text_input))

    def test_synthetic_derating_graph(self):
        folder = str(Path(__file__).resolve().parents[1])
        code = f'''
import sys, runpy, streamlit as st
from pathlib import Path
folder = Path({folder!r})
sys.path.insert(0, str(folder))
sys.path.insert(0, str(folder / 'tests'))
from test_data import sample
class Upload:
    name = 'essai.xlsm'
    def getvalue(self):
        return sample()
st.file_uploader = lambda *args, **kwargs: [Upload()]
runpy.run_path(str(folder / 'app.py'), run_name='__main__')
'''
        app = AppTest.from_string(code, default_timeout=60).run()
        self.assertFalse(app.exception, [e.message for e in app.exception])
        self.assertFalse(any('Aucun point de dérating' in x.value for x in app.info))
        cycle = next(widget for widget in app.multiselect if widget.label == 'Voies du graphique de cyclage')
        self.assertEqual(cycle.value, [1])

    def test_cycling_superimposes_multiple_files(self):
        folder = str(Path(__file__).resolve().parents[1])
        code = f'''
import sys, runpy, streamlit as st
from pathlib import Path
folder = Path({folder!r})
sys.path.insert(0, str(folder))
sys.path.insert(0, str(folder / 'tests'))
from test_data import sample
import chart_component
def capture(fig, chart_id, *args):
    st.session_state['test_' + chart_id] = fig.to_plotly_json()
    st.markdown('GRAPH_' + chart_id)
chart_component.draw = capture
class Upload:
    def __init__(self, name): self.name = name
    def getvalue(self): return sample()
st.file_uploader = lambda *args, **kwargs: [Upload('a.xlsm'), Upload('b.xlsm')]
runpy.run_path(str(folder / 'app.py'), run_name='__main__')
'''
        app = AppTest.from_string(code, default_timeout=60).run()
        self.assertFalse(app.exception, [e.message for e in app.exception])
        traces = app.session_state['test_cycle']['data']
        self.assertEqual(len(traces), 2)
        self.assertEqual([trace['name'] for trace in traces], ['a.xlsm · Courant', 'b.xlsm · Courant'])
        for chart_id in ('cycle', 'brut', 'derating'):
            legend = app.session_state['test_' + chart_id]['layout']['legend']
            self.assertEqual(legend['orientation'], 'h')
            self.assertLess(legend['y'], 0)
        self.assertTrue(all(not item.proto.expanded for item in app.expander))
        contents = [item.value for item in app.markdown]
        self.assertLess(contents.index('GRAPH_brut'), contents.index('**⚙️ Réglages du graphique temporel**'))
        self.assertLess(contents.index('**⚙️ Réglages du graphique temporel**'), contents.index('GRAPH_derating'))
        self.assertLess(contents.index('GRAPH_derating'), contents.index('**⚙️ Réglages de la courbe de dérating**'))


if __name__ == '__main__':
    unittest.main()

