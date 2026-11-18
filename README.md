# Courbes de température et dérating

Application Windows locale, sans service distant. Après la fermeture du dernier onglet de l'application, le programme s'arrête automatiquement après un délai de 15 secondes, pour permettre une reconnexion.

## Installation et lancement

Dans PowerShell, depuis ce dossier :

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe launcher.py
```

Après installation, `lancer.bat` lance également l'application. Sur le poste de développement, les scripts acceptent aussi un environnement `.venv` situé dans le dossier parent. Les données de mesure et les images d'exemple restent locales et ne sont pas incluses dans le dépôt.

## Utilisation

1. Importez un ou plusieurs classeurs `.xlsm` ou `.xlsx`. Les fichiers de production doivent contenir une feuille `Enregistrement`, avec noms en ligne 1, statuts en ligne 2, ligne 3 ignorée, mesures dès la ligne 4, dates en colonne A et marqueurs en colonne P. Le modèle local `Forme_data.xlsm`, non publié, est accepté exceptionnellement avec sa feuille `Feuil1`.
   Les informations sur les valeurs et lignes ignorées sont regroupées sous l'import, dans le panneau latéral.
2. Choisissez la colonne de courant et les voies du graphique temporel. Ouvrez le bouton 🎨 de chaque voie pour vérifier son unité et personnaliser son nom, sa couleur ou son trait. Les textes et erreurs des voies numériques sont ignorés ; les dates invalides, doublons et retours en arrière sont exclus. La première date en doublon est conservée.
3. Dans le graphique de dérating, les suffixes `020`, `040`, `060`, `080`, `100` et `120` en colonne P repèrent les fins de palier. Le courant est lu sur la même ligne. Le minimum des points disponibles à chaque palier est multiplié par 0,8. Les points absents sont signalés et le nombre d'échantillons utilisés apparaît au survol.
4. Pour annoter, activez le placement puis cliquez sur une courbe et faites glisser le texte. L'appareil photo du graphique exporte un PNG. Les réglages et annotations ne sont conservés que pendant la session.

Dans l'onglet **Cyclage de température / choc thermique**, les mêmes fichiers importés sont disponibles pour un affichage libre : choisissez les voies, leurs unités et leurs couleurs, puis réglez le graphique et ses annotations indépendamment de l'onglet dérating. Les autres formats de fichiers seront ajoutés lorsque leur structure sera connue.

La réduction éventuelle des courbes temporelles concerne uniquement leur affichage ; les calculs de dérating utilisent toutes les données lues. Les calculs sur vos fichiers de production restent à valider par vos soins.

## Vérification et exécutable Windows

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\construire_exe.bat
```

L'exécutable construit est `dist/App_temperature.exe` ; il n'est pas inclus dans le dépôt. Les tests avec le modèle privé sont ignorés s'il est absent ; les autres utilisent des données synthétiques. La construction et l'utilisation sur un autre poste restent à vérifier.

