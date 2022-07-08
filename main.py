# --*--coding:UTF-8 --*--
import sqlite3
from binary2strings import binary2strings as b2s
import shutil
import argparse


# Ajout d'un argument pour le nom de la base de données
parser = argparse.ArgumentParser()
parser.add_argument('database', help='nom de la base de données')
args = parser.parse_args()
db = args.database

# copie de la base de données
src = db
des = r'' + db.split('.')[0] + '_copy.db'

try:
    shutil.copy(src, des)
except IOError as e:
    print("Erreur lors de la copie de la base de données : " + e.strerror)
else:
    print("**** Copie de la base de données effectuée avec succès. ****")


# connexion à la base de données SQLite
connexion = sqlite3.connect(des)
cursor = connexion.cursor()


def query(query_str):
    """
    @param query_str: string (requête SQL)
    @return: une liste de dictionnaires (résultat de la requête)
    @description: Fonction qui permet de faire une requête SQL et qui retourne une liste contenant des dictionnaires.
    Chaque dictionnaire correspond à une ligne (nom du champ : valeur du champ)."""
    cursor.execute(query_str)
    connexion.commit()
    return [dict(zip([column[0] for column in cursor.description], row)) for row in cursor.fetchall()]


def search_column_blob(table):
    """
    @param: table: string (nom de la table)
    @description: Fonction qui retourne la liste des colonnes blob de la table.
    @return: dictionnaire de strings (nom des colonnes blob : correspondance avec la colonne texte à créer).
    Exemple de retour : {'data': 'data_text', 'replydata': 'replydata_text'}
    """
    colonnes_blob = {}
    table_info = query("PRAGMA table_info(" + table + ")")
    # table_info est une liste de dictionnaires. Chaque dictionnaire contient les informations sur une colonne de la table.
    for element in table_info:
        if element['type'] == "BLOB" or element['type'] == "blob":
            colonnes_blob[element['name']] = element['name'] + '_text'
            print("**** La colonne " + element['name'] +
                  " est une colonne de type blob. ****")
    return colonnes_blob


def duplicates_colonnes_blob(table, dict_colonnes_blob):
    """
    @param: table: string (nom de la table)
    @param: dict_colonnes_blob: dictionnaire de strings (nom des colonnes blob : correspondance avec la colonne texte à créer).
    @description: Fonction qui crée les colonnes texte à partir des colonnes blob.
    @return: message de confirmation
    """
    # Création des colonnes blob dupliquées en text
    message = ""
    for colonne in dict_colonnes_blob.values():
        try:
            query("ALTER TABLE " + table + " ADD COLUMN " + colonne + " TEXT")
            message = message + "La colonne " + colonne + " a été créée !" + "\n"
        except sqlite3.OperationalError:
            message = message + "La colonne " + colonne + " existe déjà." + "\n"
    return message


def convert_blob_to_text(colonne_blob, nouvelle_colonne, table):
    """
    @param: colonne_blob: string (nom de la colonne blob)
    @param: nouvelle_colonne: string (nom de la nouvelle colonne)
    @description: Fonction qui convertit les données blob en text.
    """
    resultats_requete = query("SELECT " + colonne_blob + " FROM " + table)
    for ligne in resultats_requete:
        colonne_text = ''
        if ligne[colonne_blob] is not None:
            for (string, type, span, is_interesting) in b2s.extract_all_strings(ligne[colonne_blob], only_interesting=True):
                colonne_text = colonne_text + f"{string}" + '\n'
        cursor.execute(
            "UPDATE " + table + " SET " + nouvelle_colonne + "= ? WHERE " + colonne_blob + "= ?", (colonne_text, ligne[colonne_blob]))
        connexion.commit()
    print("Conversion des données blob en txt effectuée concernant la colonne : " + colonne_blob + ".")


# Liste les tables de la base de données
tables = query(
    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
for table in tables:
    print("**** Travail en cours sur la table " + table['name'] + " ****")
    # Recherche les colonnes de type BLOB
    colonnes_blob = search_column_blob(table['name'])
    if len(colonnes_blob) == 0:
        print("**** Aucune colonne blob n'a été trouvée dans la table " +
              table['name'] + " ****")
    # Pour chaque colonne de type BLOB trouvée, on crée une colonne texte correspondante
    message = duplicates_colonnes_blob(table['name'], colonnes_blob)
    if len(message) > 0:
        print(message.rstrip())
    # Pour chaque valeur de la colonne blob, on convertit la valeur en texte
    for tuples in colonnes_blob.items():
        convert_blob_to_text(tuples[0], tuples[1], table['name'])

cursor.close()
connexion.close()
