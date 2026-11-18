"""Application locale de visualisation et de dérating."""
import hashlib
from html import escape

import plotly.graph_objects as go
import streamlit as st

from data_io import PALIER, active_columns, derating, read_recording
from chart_component import draw

st.set_page_config(page_title='Courbes de température', page_icon='🌡️', layout='wide')
st.title('🌡️ Courbes de température et dérating')
st.caption('Importez vos mesures, composez vos graphiques et exportez-les en PNG.')

with st.expander('👋 Premiers pas'):
    st.markdown(
        '1. **Importez** un ou plusieurs classeurs dans le panneau de gauche.\n'
        '2. Choisissez **Dérating** ou **Cyclage / choc thermique**, puis sélectionnez les voies à afficher.\n'
        '3. Personnalisez les courbes et le graphique. Pour enregistrer une image, utilisez '
        'l’icône appareil photo dans la barre du graphique.'
    )


@st.cache_data(max_entries=12, show_spinner='Lecture des mesures…')
def load_file(content, name):
    return read_recording(content, name)


def col_name(rec, i):
    return f'{rec.headers[i] or "Voie sans nom"} [{i + 1}]'


def unit_guess(name):
    text = str(name).lower().strip()
    if 'courant' in text:
        return 'A'
    if 'tension' in text:
        return 'V'
    if 'puissance' in text:
        return 'W'
    if 'résistance' in text or 'resistance' in text:
        return 'mΩ'
    if text.startswith('t ') or text.startswith('tamb') or text.startswith('tcon') or text.startswith('pico t'):
        return '°C'
    return 'À définir'


def limited_indices(values, limit=6000):
    """Conserver extrêmes et ruptures par tranche, uniquement pour l'affichage."""
    n = len(values)
    if n <= limit:
        return list(range(n))
    step = max(1, (n + limit // 4 - 1) // (limit // 4))
    indices = set()
    for start in range(0, n, step):
        end = min(start + step, n)
        valid = [(values[i], i) for i in range(start, end) if values[i] is not None]
        indices.update((start, end - 1))
        if valid:
            indices.add(min(valid)[1]); indices.add(max(valid)[1])
        # Une valeur manquante par bloc matérialise au minimum la rupture.
        missing = next((i for i in range(start, end) if values[i] is None), None)
        if missing is not None:
            indices.add(missing)
    return sorted(indices)


def options(chart, default_title):
    with st.expander('⚙️ Présentation et dimensions du graphique', expanded=False):
        title = st.text_input('Titre', default_title, key=chart+'_title')
        a, b, c = st.columns(3)
        width = a.number_input('Largeur PNG (px)', 600, 3000, 1200, 100, key=chart+'_width')
        height = b.number_input('Hauteur (px)', 400, 1600, 650, 50, key=chart+'_height')
        size = c.number_input('Taille du texte', 8, 32, 14, key=chart+'_font')
        a, b, c = st.columns(3)
        grid = a.checkbox('Grille', True, key=chart+'_grid')
        legend = b.selectbox('Position de légende', ['Droite', 'Bas', 'Haut'], index=1, key=chart+'_legend')
        markers = c.checkbox('Afficher les points', chart == 'derating', key=chart+'_markers')
        x_title = st.text_input('Titre de l’axe horizontal', 'Ambient temperature (°C)' if chart == 'derating' else 'Date and time', key=chart+'_xtitle')
        x_min = st.text_input('Borne X minimale (vide = automatique)', key=chart+'_xmin')
        x_max = st.text_input('Borne X maximale (vide = automatique)', key=chart+'_xmax')
        st.caption('Dates : AAAA-MM-JJ HH:MM:SS ; températures : nombre. Les bornes Y sont réglables par axe ci-dessous.')
    return dict(title=title, width=width, height=height, size=size, grid=grid, legend=legend, markers=markers, x_title=x_title, xmin=x_min, xmax=x_max)


def style(fig, opt, time_axis):
    legend = {'Droite':dict(x=1.02,y=1), 'Bas':dict(x=0,y=-0.2,orientation='h'), 'Haut':dict(x=0,y=1.12,orientation='h')}[opt['legend']]
    fig.update_layout(title=opt['title'], height=opt['height'], paper_bgcolor='white', plot_bgcolor='white',
                      font=dict(color='#202124',size=opt['size']), legend=legend,
                      margin=dict(l=100, r=120 if opt['legend'] == 'Droite' else 40, t=100,
                                  b=140 if opt['legend'] == 'Bas' else 100), hovermode='closest')
    fig.update_xaxes(title=opt['x_title'], showgrid=opt['grid'], gridcolor='#dddddd', zeroline=False)
    if opt['xmin'] and opt['xmax']:
        try:
            bounds = [opt['xmin'], opt['xmax']] if time_axis else [float(opt['xmin']), float(opt['xmax'])]
            fig.update_xaxes(range=bounds)
        except ValueError:
            st.warning('Bornes X invalides : cadrage automatique.')


def annotation_controls(key):
    with st.expander('📍 Étiquettes sur le graphique'):
        placing = st.checkbox('Ajouter une étiquette en cliquant sur une courbe', key=key+'_placing')
        st.text_input('Texte facultatif avant la valeur', key=key+'_label')
        st.color_picker('Couleur de la prochaine étiquette', '#b02020', key=key+'_annotation_color')
        st.caption('Activez le placement, cliquez sur une courbe, puis faites glisser le texte. Pour exporter, utilisez l’appareil photo au-dessus du graphique.')
        anns = st.session_state.setdefault('annotations_'+key, [])
        if anns:
            names = [f'{i+1} : {a.get("text", "")}' for i, a in enumerate(anns)]
            selected = st.selectbox('Étiquette à modifier', range(len(anns)), format_func=lambda i:names[i], key=key+'_selected_ann')
            text = st.text_input('Texte de l’étiquette', value=anns[selected].get('text', ''), key=key+'_edit_'+str(selected))
            if text != anns[selected].get('text'):
                anns[selected]['text'] = escape(text or '')
            if st.button('Supprimer cette étiquette', key=key+'_del', icon=':material/delete:'):
                anns.pop(selected)
                st.rerun()
    return placing


def axis_options(key, unit):
    with st.expander(f'📐 Axe Y — {unit}'):
        title = st.text_input('Titre de l’axe', unit, key=key+'_title')
        a, b = st.columns(2)
        minimum = a.text_input('Minimum (auto si vide)', key=key+'_min')
        maximum = b.text_input('Maximum (auto si vide)', key=key+'_max')
        step = st.text_input('Intervalle des graduations (auto si vide)', key=key+'_step')
    axis = go.layout.YAxis(title=title, showgrid=True)
    try:
        if minimum and maximum:
            axis.range = [float(minimum), float(maximum)]
        if step:
            axis.dtick = float(step)
    except ValueError:
        st.warning(f'Réglage numérique invalide pour {unit}.')
    return axis


def curve_settings(rec, i, key, color):
    """Présenter les réglages de chaque voie sans encombrer la page."""
    with st.popover(f'🎨 {col_name(rec, i)}', width='stretch', key=key+'_settings'):
        st.caption('Personnalisez cette courbe pour le graphique ci-dessous.')
        name = st.text_input('Légende', f'{rec.name} · {rec.headers[i] or "Channel"}', key=key+'_name')
        unit = st.selectbox('Unité', ['°C', 'A', 'V', 'W', 'mΩ', 'À définir'],
                            index=['°C', 'A', 'V', 'W', 'mΩ', 'À définir'].index(unit_guess(rec.headers[i])), key=key+'_unit')
        color = st.color_picker('Couleur', color, key=key+'_color')
        line = st.selectbox('Trait', ['Plein', 'Pointillé', 'Tirets'], key=key+'_line')
        width = st.number_input('Épaisseur', min_value=1, max_value=10, value=2, key=key+'_width')
    return rec, i, name, unit, color, line, width


def temporal_chart(selected, chart_id, title, chart_slot):
    opt = options(chart_id, title)
    units = list(dict.fromkeys(item[3] for item in selected))
    if len(units) > 5:
        with chart_slot:
            st.error('Cinq unités au maximum peuvent être affichées simultanément.')
    elif selected:
        fig = go.Figure()
        axis_config = {}
        for j, unit in enumerate(units):
            config = axis_options(chart_id+'_axis_'+str(j), 'Unspecified unit' if unit == 'À définir' else unit)
            config.showgrid = bool(opt['grid']) and j == 0
            if j:
                config.update(overlaying='y', anchor='free', side='right' if j%2 else 'left', position=(1 - (j//2)*0.07) if j%2 else ((j//2)*0.07))
            axis_config['yaxis' + (str(j+1) if j else '')] = config
        fig.update_layout(**axis_config)
        reduced = False
        for rec, i, name, unit, color, line, width in selected:
            values = rec.columns[i]
            ids = limited_indices(values)
            reduced |= len(ids) < len(values)
            fig.add_trace(go.Scattergl(x=[rec.times[k] for k in ids], y=[values[k] for k in ids],
                name=name, mode='lines+markers' if opt['markers'] else 'lines', connectgaps=False,
                yaxis='y'+(str(units.index(unit)+1) if units.index(unit) else ''),
                line=dict(color=color, width=width, dash={'Plein':'solid','Pointillé':'dot','Tirets':'dash'}[line]), meta={'annotatable':True}))
        if reduced:
            st.info('Affichage réduit pour les courbes volumineuses ; les calculs utilisent toutes les mesures. Les petites variations peuvent ne pas apparaître.')
        style(fig, opt, True)
        placing = annotation_controls(chart_id)
        with chart_slot:
            draw(fig, chart_id, placing, opt['width'], opt['height'])
    else:
        with chart_slot:
            st.info('Sélectionnez des voies pour afficher le graphique temporel.')


with st.sidebar:
    st.header('📂 Fichiers de mesures')
    uploads = st.file_uploader('Importer un ou plusieurs classeurs', type=['xlsm','xlsx'], accept_multiple_files=True)
    st.caption('Sélectionnez plusieurs fichiers à la fois pour superposer vos essais.')
    import_diagnostics_slot = st.container()
    st.divider()
    st.caption('🔒 Données traitées localement · Réglages conservés pendant la session.')
records = []
names = set()
import_diagnostics = []
for upload in uploads:
    if upload.name in names:
        import_diagnostics.append(f'{upload.name} : nom de fichier déjà importé ; renommez un des fichiers.')
        continue
    names.add(upload.name)
    try:
        rec = load_file(upload.getvalue(), upload.name)
        records.append(rec)
        for warning in rec.warnings:
            import_diagnostics.append(f'{rec.name} : {warning}')
    except Exception as exc:
        st.error(f'{upload.name} : lecture impossible : {exc}')

if import_diagnostics:
    with import_diagnostics_slot:
        with st.expander(f'⚠️ Informations d’import ({len(import_diagnostics)})', expanded=False):
            for message in import_diagnostics:
                st.warning(message)

tab_derating, tab_cycle = st.tabs(['📉 Dérating', '🌡️ Cyclage / choc thermique'])
with tab_cycle:
    if not records:
        st.info('👈 Importez un ou plusieurs fichiers Excel dans le panneau de gauche pour commencer.')
    else:
        st.subheader('🌡️ Cyclage de température / choc thermique')
        st.caption('Choisissez les voies à superposer. Les réglages de cet onglet sont indépendants de ceux du dérating.')
        st.subheader('📈 Mesures en fonction du temps')
        cycle_chart_slot = st.container()
        st.caption('Zoomez ou déplacez-vous dans le graphique. Utilisez l’appareil photo pour exporter en PNG.')
        st.subheader('⚙️ Réglages du cyclage')
        cycle_selected = []
        cycle_palette = ['#0072B2', '#D55E00', '#009E73', '#CC79A7', '#E69F00', '#56B4E9']
        for index, rec in enumerate(records):
            filekey = 'cycle_' + hashlib.sha256(rec.name.encode()).hexdigest()[:12]
            active = active_columns(rec)
            defaults = [i for i in active if unit_guess(rec.headers[i]) == '°C'] or active[:1]
            with st.expander(f'📄 {rec.name} — {len(rec.times)} mesures · {len(active)} voies actives', expanded=False):
                choices = st.multiselect('Voies du graphique de cyclage', active, default=defaults,
                    format_func=lambda i: col_name(rec, i), key=filekey+'_channels')
                if choices:
                    st.caption('🎨 Ouvrez une voie pour modifier sa couleur, son unité ou son nom.')
                for i in choices:
                    cycle_selected.append(curve_settings(rec, i, filekey+'_'+str(i), cycle_palette[(index+i)%len(cycle_palette)]))
        temporal_chart(cycle_selected, 'cycle', 'Temperature cycling / thermal shock', cycle_chart_slot)

with tab_derating:
    if not records:
        st.info('👈 Importez un ou plusieurs fichiers Excel dans le panneau de gauche pour commencer.')
    else:
        st.subheader('📉 Analyse de dérating')
        st.caption('Sélectionnez les voies à visualiser et la colonne de courant de chaque échantillon.')
        st.subheader('📈 Mesures en fonction du temps')
        raw_chart_slot = st.container()
        st.caption('Explorez les données brutes ; l’appareil photo du graphique permet d’exporter en PNG.')
        st.markdown('**⚙️ Réglages du graphique temporel**')
        selected = []
        palette = ['#0072B2', '#D55E00', '#009E73', '#CC79A7', '#E69F00', '#56B4E9']
        for index, rec in enumerate(records):
            filekey = hashlib.sha256(rec.name.encode()).hexdigest()[:12]
            active = active_columns(rec)
            with st.expander(f'📄 {rec.name} — {len(rec.times)} mesures · {len(active)} voies actives', expanded=False):
                defaults = [i for i in active if str(rec.headers[i]).strip().lower() in ('courant','t amb','tamb','t con 1','t con 2')]
                choices = st.multiselect('Voies du graphique temporel', active, default=defaults, format_func=lambda i:col_name(rec,i), key=filekey+'_channels')
                if choices:
                    st.caption('🎨 Ouvrez une voie pour modifier sa couleur, son unité ou son nom.')
                for i in choices:
                    selected.append(curve_settings(rec, i, filekey+'_'+str(i), palette[(index+i)%len(palette)]))

        temporal_chart(selected, 'brut', 'Measurements over time', raw_chart_slot)

        st.subheader('📉 Courbe de dérating')
        derating_chart_slot = st.container()
        st.caption('Chaque courbe représente un échantillon. La courbe de dérating est calculée à partir des points disponibles.')
        st.markdown('**⚙️ Réglages de la courbe de dérating**')
        current_columns = []
        with st.expander('🔌 Colonnes de courant des échantillons', expanded=False):
            st.caption('Vérifiez la colonne utilisée pour le calcul de chaque échantillon.')
            for rec in records:
                filekey = hashlib.sha256(rec.name.encode()).hexdigest()[:12]
                current_default = next((i for i in rec.columns if str(rec.headers[i]).strip().lower() == 'courant'), None)
                candidates = list(rec.columns)
                if candidates:
                    current = st.selectbox(f'Colonne courant pour le dérating — {rec.name}', candidates,
                        index=candidates.index(current_default) if current_default in candidates else None,
                        format_func=lambda i:col_name(rec,i), placeholder='Choisir la colonne courant', key=filekey+'_current')
                else:
                    current = None
                current_columns.append(current)
        opt = options('derating', 'Derating curve')
        curves, result, diagnostics = derating(records,current_columns)
        with st.expander(f'🔎 Points indisponibles et diagnostics ({len(diagnostics)})', expanded=False):
            for message in diagnostics:
                st.write('• ' + message)
            if not diagnostics:
                st.write('Tous les points de palier sont disponibles.')
        if result:
            fig = go.Figure()
            for i, rec in enumerate(records):
                pts = curves[rec.name]
                if pts:
                    color = st.color_picker(f'Couleur de {rec.name}', palette[i%len(palette)], key='sample_'+hashlib.sha256(rec.name.encode()).hexdigest()[:12])
                    fig.add_trace(go.Scatter(dict(x=list(PALIER), y=[pts.get(t) for t in PALIER], name=rec.name, mode='lines+markers' if opt['markers'] else 'lines', connectgaps=False, line=dict(color=color), meta={'annotatable':True})))
            # None sépare explicitement les paliers manquants.
            fig.add_trace(go.Scatter(dict(x=list(PALIER), y=[result[t][0] if t in result else None for t in PALIER],
                name='Derating curve', mode='lines+markers', connectgaps=False, fill='tozeroy', fillcolor='rgba(30,110,140,0.3)',
                line=dict(color='#164a60', dash='dash',width=3), meta={'annotatable':True},
                customdata=[result[t][1] if t in result else 0 for t in PALIER], hovertemplate='%{x} °C<br>%{y:.4g} A<br>%{customdata} sample(s)<extra>%{fullData.name}</extra>')))
            axis = axis_options('derating_axis','Current (A)')
            axis.showgrid = bool(opt['grid'])
            fig.update_yaxes(axis)
            style(fig,opt,False)
            placing = annotation_controls('derating')
            with derating_chart_slot:
                draw(fig, 'derating', placing, opt['width'], opt['height'])
        else:
            with derating_chart_slot:
                st.info('Aucun point de dérating disponible dans les fichiers importés.')

