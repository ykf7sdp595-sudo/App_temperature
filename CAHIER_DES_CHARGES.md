# Cahier des charges — Application de traitement de courbes de température

**Statut : cahier des charges consolidé à partir des réponses de l'utilisateur.** Les réponses originales sont conservées en section 8 ; les dernières précisions sont intégrées aux exigences ci-dessous.

## 1. Objectif et contexte

Créer une application locale Streamlit, dans le dossier `App_temperature`, pour importer, visualiser et exploiter des mesures de température et, selon les essais, des grandeurs associées notamment électriques. L'interface et les usages s'inspireront des applications existantes de traction et de vibration, sans supposer que toutes leurs analyses s'appliquent ici.

Prévoir deux espaces : **Cyclage de température / choc thermique** et **Dérating**. L'architecture devra permettre l'ajout ultérieur d'autres formats et types de données.

## 2. Données disponibles et limites connues

- Le modèle `Forme_data.xlsm` contient une feuille `Feuil1`, avec une zone renseignée allant de A1 à CI7 : c'est un extrait de cinq lignes de mesures. Les fichiers réels de ce format placent ces données dans la feuille `Enregistrement` ; les autres feuilles sont ignorées. La première ligne contient les noms et la deuxième les statuts.
- La colonne A, nommée `Temps`, contient des nombres correspondant à des dates et heures Excel, à lire même si les cellules ne sont pas typées comme dates. La ligne 3 doit toujours être exclue ; les mesures à exploiter commencent donc à la ligne 4. Exclure les lignes aux dates manquantes ; en cas de doublon, conserver uniquement la première occurrence. Les retours en arrière ne sont pas attendus dans ces enregistrements échantillonnés ; les signaler et exclure les lignes concernées.
- Les colonnes comprennent notamment tension, courant, puissance, températures, consigne et mesures d'appareils ; les unités ne sont pas explicitement précisées dans les en-têtes observés. Certains noms sont vides, répétés ou égaux à zéro, et plusieurs colonnes sont entièrement nulles. La colonne `Stab Pico T3` contient des erreurs `#N/A`. L'exemple contient des statuts `On`, `On2` et `Off` ; certains ne correspondent pas aux mesures présentes.
- Le classeur contient des références externes dans ses métadonnées ; les valeurs de la feuille de mesures sont enregistrées directement. L'extrait ne contient aucun marqueur de palier en colonne P. Pour des raisons de confidentialité, l'utilisateur effectuera lui-même la validation sur ses fichiers réels.
- Pour le dérating, les données proviennent actuellement de classeurs Excel agrégeant différentes mesures. La première colonne contient une date et une heure complètes. D'autres formats sont attendus, probablement CSV ; leur structure n'est pas encore connue.
- Le statut indiqué on/off n'est pas fiable : il ne doit pas déterminer à lui seul la disponibilité d'une voie.

## 3. Fonctions communes demandées

### 3.1 Import et choix des voies

- Importer plusieurs fichiers simultanément et permettre la superposition de plusieurs courbes, y compris issues de fichiers différents.
- Pour chaque fichier, identifier clairement la source et proposer les voies disponibles ; permettre de sélectionner plusieurs voies et de choisir leur nom dans la légende.
- Préserver les données sources : lecture seule, aucune modification du classeur, aucune exécution de macros.
- Traiter les fichiers indépendamment : signaler un fichier illisible, une voie incompatible ou une date invalide sans masquer silencieusement le problème ni empêcher l'utilisation des autres fichiers valides.
- Prévoir une interface d'import extensible pour accueillir ultérieurement des CSV et de nouveaux formats. La prise en charge effective d'un format CSV particulier dépendra d'un exemple et de la validation de sa structure.

### 3.2 Graphique et superposition

- Afficher les courbes choisies sur un graphique interactif : zoom, déplacement, retour au cadrage et affichage des valeurs au survol.
- Permettre la sélection d'une couleur pour chaque courbe et le réglage de son nom, de sa visibilité, de l'épaisseur et du style de trait.
- Permettre le réglage du titre, des titres et unités d'axes, des bornes, de la grille, de la légende, des dimensions et des tailles de texte. Le contenu précis des options complémentaires reste à valider.
- Exporter en PNG, à des dimensions adaptées à la largeur d'une page Word. Réglage des dimensions, graduations, marqueurs et position fixe de la légende.
- Prévoir jusqu'à cinq axes Y, un par unité, chaque voie de même unité partageant son axe ; pas de conversion d'unités. Unités usuelles : V, A, °C et mΩ pour la résistance de contact. L'affectation des unités et les valeurs par défaut seront à configurer ; ne pas déduire silencieusement une unité incertaine.
- Prévoir la gestion des données manquantes et des grands volumes : ne pas inventer de mesure ; toute réduction d'affichage doit être signalée et ne pas altérer les données utilisées pour les calculs ou les exports.

### 3.3 Étiquettes manuelles

- Permettre d'ajouter plusieurs étiquettes en cliquant sur des points de courbe et de déplacer directement leur texte sur le graphique, comme dans les applications existantes. Chaque étiquette affiche la valeur Y, une flèche vers son point et des options de style.
- Prévoir la modification du texte, de la position et la suppression de chaque étiquette ; afficher les coordonnées du point associé si ce mode est retenu.
- Conserver les positions lors des changements de zoom et dans les exports pendant la session.
- Vérifier techniquement dès le début la persistance du déplacement dans Streamlit et sa restitution dans l'export PNG : ce comportement fait partie des critères d'acceptation, pas seulement de la présentation.

## 4. Règles spécifiques au dérating

### 4.1 Détection des voies actives

Pour chaque colonne de mesure candidate, examiner les **valeurs de mesure**, indépendamment de l'indicateur on/off. Une voie est proposée dans le choix si au moins une valeur de mesure exploitable est différente de zéro ; une voie vide ou ne contenant que des zéros n'est pas proposée. Un zéro reste une mesure valide dans une voie active et ne doit pas être supprimé du tracé. Les valeurs négatives non nulles rendent également la voie active.

Ignorer les lignes 1 à 3 lors du test d'activité et examiner les valeurs à partir de la ligne 4. Ignorer les textes et erreurs Excel dans les voies numériques ; traiter ces cellules comme indisponibles, sans les convertir en zéro. Les valeurs numériques ne seront pas stockées sous forme de texte. Signaler les données non interprétables. Identifier les colonnes par leur position en plus de leur nom pour gérer les noms vides ou identiques. La colonne P `Marqueur` est une exception textuelle utilisée pour le calcul ci-dessous, et non une voie numérique à tracer.

### 4.2 Temps et mesures

- Lire la première colonne comme date et heure complètes, sans inventer d'horodatage. Conserver la précision effectivement disponible.
- Proposer un graphique libre en fonction de la date et heure, pour superposer les voies des différents fichiers synchronisés. Par défaut pour le dérating : courant, Tamb, T con 1 et T con 2 quand ces voies sont disponibles.
- Ne pas recalculer les formules Excel ni exécuter de macros ; l'utilisation éventuelle des dernières valeurs de formule enregistrées dans le fichier sera explicitée et vérifiée sur le modèle.
- Proposer un second graphique de dérating, distinct du graphique temporel, avec la température ambiante en X et le courant en Y, pour plusieurs échantillons/fichiers. L'image `exemple_courbe_derating.png` sert de référence visuelle.

### 4.3 Calcul de la courbe de dérating

1. Rechercher, dans la colonne P `Marqueur`, les lignes de fin de palier dont le texte se termine respectivement par `020`, `040`, `060`, `080`, `100` et `120` ; ces suffixes correspondent aux températures nominales 20, 40, 60, 80, 100 et 120 °C. Le palier nominal 20 °C peut correspondre à une température ambiante comprise entre 20 et 35 °C ; l'abscisse du point reste 20 °C.
2. Pour chaque fichier et chaque palier, relever le courant de la même ligne et tracer les six points de l'échantillon en température nominale / courant, avec une courbe et une couleur par échantillon.
3. Pour chaque température, calculer le minimum des courants disponibles des échantillons, puis multiplier ce minimum par **0,8**. Si un échantillon ne fournit pas un point, calculer le palier à partir des autres points disponibles ; si aucun point n'est disponible, ne pas inventer de résultat et signaler le palier manquant. Relier les points obtenus pour former la courbe de dérating et remplir l'aire sous cette courbe jusqu'à Y = 0, comme sur l'image de référence. La courbe et les points sont visibles avec les échantillons ; les étiquettes des valeurs et leur position sont réglables.
4. Aucun verdict de conformité ni export de tableau ou de rapport n'est demandé. L'image du graphique est exportable en PNG.

Un marqueur de palier ne sera pas répété dans un fichier. Un marqueur absent, un courant absent ou invalide, ou une ligne rejetée ne fournit pas de point ; afficher un diagnostic permettant d'identifier le fichier et le palier concernés. Un minimum calculé sur un sous-ensemble des échantillons doit être identifiable.

## 5. Cyclage de température et choc thermique

L'espace cyclage / choc thermique permet de tracer et superposer librement les mesures de tous les fichiers déjà importés, avec ses propres réglages et annotations, sans analyse automatique pour l'instant. Les autres formats de cyclage ou choc thermique seront ajoutés après fourniture de leur structure.

## 6. Aspects techniques et exploitation

- Application Streamlit locale sur Windows, entièrement hors ligne, avec exécutable autonome dès la première livraison.
- Réduire les dépendances directes : examiner la réutilisation de Streamlit et Plotly présents dans l'application de traction. Une bibliothèque de lecture Excel comme `openpyxl` peut être nécessaire pour `.xlsx` et `.xlsm` ; ce choix sera confirmé après examen du modèle. Toute dépendance supplémentaire doit avoir une utilité identifiée.
- Séparer lecture des fichiers, représentation des voies, calculs et interface afin d'ajouter ultérieurement des lecteurs et des analyses sans changer les données sources.
- Aucune transmission réseau de données de mesure. Fichiers, réglages et annotations restent temporaires : aucune sauvegarde de projet entre sessions n'est demandée.
- Prendre en charge de gros volumes, y compris des essais de 1 000 heures et une augmentation future du nombre de voies. La limite de taille de fichier, le nombre de points et l'objectif de performance restent à mesurer sur des fichiers représentatifs ; 1 000 heures ne déterminent pas à elles seules le nombre de lignes.
- Fournir une notice d'installation et d'utilisation adaptée au mode de distribution retenu.

## 7. Proposition de réalisation et de validation

1. **Cadrage** : utiliser le modèle fourni et les règles définies ci-dessus ; priorité forte au dérating.
2. **Socle commun et dérating** : lecture du modèle validé, détection des voies actives, import multiple, choix des voies, superposition, réglages et annotations déplaçables, export.
3. **Cyclage / choc thermique** : ajouter le ou les lecteurs et les analyses définis à partir d'exemples représentatifs. Si les exemples ne sont pas disponibles, limiter cet espace aux possibilités communes effectivement vérifiables.
4. **Validation** : essais automatisés sur données synthétiques et sur le modèle fourni, contrôle des voies, dates, marqueurs, minima et coefficient 0,8, imports multiples, unités et erreurs. Tester dans un navigateur le déplacement d'étiquettes, leur maintien et leur export. Vérifier les performances sur un volume représentatif synthétique et l'exécutable sur Windows. L'utilisateur réalisera lui-même les essais sur fichiers réels confidentiels, notamment la validation des marqueurs de palier et des performances réelles.

## 8. Questions à trancher

### Fichiers et données

1. Le modèle `Forme_data.xlsm` représente-t-il bien un essai de dérating ? Les autres fichiers ont-ils la même structure ?
C'est bien un essai de dérating, les autres fichiers de ce format excel auront la même structure, pas forcément les autres. On, adaptera quand je les aurai
2. Les données se trouvent-elles toujours dans `Feuil1`, avec les noms en ligne 1, les statuts en ligne 2 et les mesures à partir de la ligne 3 ? Peut-il y avoir plusieurs feuilles de mesures ou des unités dans d'autres fichiers ?
Les données sur ce type de fichier seront sur une feuille nommée "Enregistrement". Il y aura d'autres feuilles mais on va les ignorer pour l'instant. Au niveau des unités ont est sur du basique (tension en V, courant en A, température en °C)
3. Les valeurs sont-elles stockées directement ou calculées par des formules ? Les classeurs sont-ils toujours enregistrés après recalcul dans Excel ?
Valeur stockées directement dans cette feuilles
4. Quelles grandeurs et unités rencontre-t-on typiquement : température, tension, courant, résistance, puissance, autres ? Les noms et unités sont-ils fiables et toujours présents ?
Les noms sont toujours présent, les unitées sont les classiques : tension en V, courant en A, température en °C.  résistance en mOhms par contre, ce sera de la résistance de contact
5. Les cellules peuvent-elles contenir du texte, des erreurs Excel, des nombres stockés en texte ou des valeurs manquantes ? Faut-il interpréter une valeur non numérique non vide comme voie active, ou uniquement les nombres non nuls ?
Oui il peux y avoir du texte, ses valeurs seront ignorées, tout comme les erreurs excel, et nombres stockées. Seule la colonne temps viennent d'une cellule au format date/heure, à prendre en compte. 
6. Les horodatages sont-ils toujours des dates Excel dans le même fuseau horaire ? L'exclusion de la ligne 3 concerne-t-elle uniquement cet exemple ou tous les fichiers ? Que faire des dates manquantes, des doublons et d'autres retours en arrière ?
Oui toujours des dates excel dans le même fuseau. Ligne 3 toujours exclue. dates manquantes, doublons et retours en arrière à exclure. 
7. Quels volumes maximaux prévoir : nombre de fichiers, voies, lignes par fichier et durée d'enregistrement ?
Gros volume, sur certains fichiers ont peux cycler pendant 1000h donc la durée et le nombres de lignes peuvent être énorme. Le nombre de voies pour l'instant on pourra pas en avoir plus, mais prends du gras pour prévoir d'éventuelles évolutions chez nous.
8. Avez-vous un exemple de fichier de cyclage ou choc thermique, même anonymisé ? Les futurs CSV sont-ils suffisamment définis pour être pris en charge dès maintenant ?
Non et non, réaliser plus tard

### Graphiques et annotations

9. Pour superposer plusieurs essais, faut-il utiliser la date réelle, le temps écoulé depuis le début de chaque fichier, ou les deux ? Faut-il un alignement manuel sur un événement commun ?
Normalement en utilisant la colonne temps tout sera synchro.
10. Quelles représentations sont nécessaires : toutes les voies en fonction du temps ; une voie électrique en fonction de la température ; plusieurs graphiques distincts ? Toutes les voies seront en fonction du temps. Laisse une option (je pense un onglet à part, ce sera plus lisible) ou on pourra afficher tout ce qu'on veux. On gèrera les setup par défaut pour chaque colonne dans un 2nd temps. 
11. Combien d'axes Y et d'unités simultanées faut-il gérer ? Souhaitez-vous choisir l'axe de chaque voie et convertir certaines unités ?
Un axe par unité, ça m'étonnerai qu'on ai un jour plus de 5 unités à afficher sur un graph. Chaque voie de même unité sera représentée sur un axe commun. Pas de convertion d'unités.
12. Pour les étiquettes, faut-il cliquer sur un point de courbe ou pouvoir placer du texte libre n'importe où ? Faut-il une flèche vers le point, l'affichage automatique des coordonnées et des réglages de style ?
Cliquer sur un point de la courbe, flèche vers le point, affichage des coordonnées en Y, réglage de style. 
13. Quels réglages graphiques supplémentaires sont indispensables : graduations, échelle logarithmique, format des dates, marqueurs, position de légende, police ou autres ? Quels formats d'export et quelles dimensions d'image souhaitez-vous ?
Echelle (que du temporel), graduation, marqueurs, position des légendes fixes. Format d'export en png, dimension d'image proportionnée pour que ça rentre en largeur sur une feuille word. 

### Analyses et résultats

14. Quel est précisément le résultat attendu pour un essai de dérating ? Quelles grandeurs comparer, quels calculs effectuer et selon quelles règles ou normes internes ? Disposez-vous d'un exemple de résultat attendu ?
Le résultat attendu est de déterminer le courant maximum admissible dans un échantillon en fonction d'une évolution de température ambiante. On as des paliers de température ambiante à 20 (entre 20 et 35), 40, 60, 80, 100 et 120°C. Dans la colonne P ("Marqueur") tu trouvera un texte qui est à la fin de chaque palier de température. Je souhaite 2 graph, 1 affichant les données brutes de façon libre (avec par défaut courant, Tamb, T con 1, T con 2). Le 2ème graph présentera la courbe de dérating de plusieurs échantillon (donc plusieurs fichiers). Tu as un exemple de courbe dans le png "exemple_courbe_derating". Courant en Y, température ambiante en X. Un point à 20, à 40, 60, 80, 100 et 120°C en X pour chaque courbes. Les points seront pris sur la ligne ou il y a du texte dans la colonne "Marqueur". Sa nomination sera variable, mais il y aura toujours à la fin "020" pour le palier 20°C, "040" pour le palier à 40, et ainsi de suite jusqu'à 120°C. Tu récupère la valeur de courant et tu la place en Y pour chaque point. Il n'y a donc que 6 points par courbes. Tu prends ensuite le Y minimum de toutes les courbes pour chaque X. A ses 6 points, tu appliquera un coefficient de réduction 20% en multipliant le ce Y par 0,8. Pour chaque X, tu tracera donc la courbe de dérating avec ses Y corrigés avec coefficient de réduction. Comme sur ma courbe d'exemple, tu tracera une aire sous la courbe de dérating. 
15. Pour le cyclage et les chocs thermiques, souhaitez-vous seulement tracer les mesures ou aussi détecter les cycles, paliers, températures extrêmes, vitesses de variation et durées ? Comment définir précisément ces événements et tolérances ?
Simplement tracer les mesures pour l'instant
16. Faut-il afficher ou exporter un tableau de résultats, les données sélectionnées en CSV ou Excel, ou un rapport ? Un verdict de conformité est-il souhaité et, dans ce cas, quels critères validés appliquer ?
Non, juste un graph exportable en png.

### Utilisation et priorités

17. L'application doit-elle mémoriser les fichiers, réglages et annotations entre deux sessions, ou une utilisation temporaire suffit-elle ? Si sauvegarde : sous forme de projet local à rouvrir ?
Utilisation temporaire seulement
18. Souhaitez-vous dès la première livraison un exécutable Windows autonome, comme pour la traction, ou un lancement depuis Python suffit-il ? L'utilisation doit-elle être entièrement hors ligne ?
Utilisation entièrement hors ligne comme sur les autres. Oui je voudrai un éxécutable autonome comme les autres. 
19. Quelle priorité donnez-vous au dérating, au cyclage/choc thermique et aux exports ? Y a-t-il une échéance ou des cas d'utilisation indispensables pour une première version ?
Dérating en grosse priorité pour l'instant 

