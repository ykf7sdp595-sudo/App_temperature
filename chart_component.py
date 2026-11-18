"""Graphique Plotly local : clics et déplacement des annotations."""
import streamlit as st
from streamlit.components.v2 import component
from plotly.offline import get_plotlyjs

JS = r"""
const plots = new WeakMap();
export default function(c) {
 const el = c.parentElement.querySelector('.plot');
 let state = plots.get(el);
 if (!state) { state = {queue: Promise.resolve()}; plots.set(el, state); }
 state.c = c; state.data = c.data;
 state.queue = state.queue.then(async () => {
  const d = state.data, fig = JSON.parse(d.spec);
  await window.Plotly.react(el, fig.data, fig.layout, d.config);
  el.removeAllListeners('plotly_click'); el.removeAllListeners('plotly_relayout');
  el.on('plotly_click', event => {
   const p = event.points?.[0];
   if (state.data.placing && p && p.data.meta?.annotatable) {
    state.c.setTriggerValue('point', {x:p.x, y:p.y, axis:p.data.yaxis || 'y', name:p.data.name});
   }
  });
  el.on('plotly_relayout', changes => {
   if (Object.keys(changes).some(k => k.startsWith('annotations['))) {
    state.c.setTriggerValue('moved', {annotations: el.layout.annotations});
   }
  });
 }).catch(e => {el.textContent = 'Erreur du graphique : ' + e.message;});
 return () => {window.Plotly.purge(el); plots.delete(el);};
}
"""
CHART = component('temperature_plot', html='<div class="plot" style="width:100%;background:white"></div>', js=get_plotlyjs() + '\n' + JS, isolate_styles=False)


def draw(fig, chart_id, placing, width, height):
    key = 'plot_' + chart_id
    def on_point():
        point = st.session_state.get(key, {}).get('point')
        if point and isinstance(point.get('y'), (int, float)):
            label = st.session_state.get(chart_id + '_label', '')
            color = st.session_state.get(chart_id + '_annotation_color', '#c62828')
            text = f"{label} : {point['y']:.4g}" if label else f"{point['y']:.4g}"
            st.session_state.setdefault('annotations_' + chart_id, []).append(dict(
                x=point['x'], y=point['y'], xref='x', yref=point['axis'], text=text,
                showarrow=True, arrowhead=2, ax=45, ay=-55, axref='pixel', ayref='pixel',
                bgcolor='white', bordercolor=color, arrowcolor=color, font={'color': color}, borderpad=4))
    def on_moved():
        moved = st.session_state.get(key, {}).get('moved', {}).get('annotations')
        if isinstance(moved, list):
            st.session_state['annotations_' + chart_id] = moved
    fig.update_layout(annotations=st.session_state.setdefault('annotations_' + chart_id, []), uirevision=chart_id)
    config = {'responsive': True, 'displaylogo': False, 'editable': True,
              'edits': {'annotationPosition': True},
              'toImageButtonOptions': {'format':'png', 'filename':chart_id, 'width':width, 'height':height, 'scale':2}}
    CHART(data={'spec': fig.to_json(), 'config':config, 'placing':placing}, key=key,
          height=height + 20, on_point_change=on_point, on_moved_change=on_moved)

