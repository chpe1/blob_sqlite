# --*--coding:UTF-8 --*--
import sqlite3
from binary2strings import binary2strings as b2s
import shutil
import argparse


# Add an argument for the database name
parser = argparse.ArgumentParser()
parser.add_argument('database', help='nom de la base de données')
args = parser.parse_args()
db = args.database


print('''
    ____  __    ____  ____     __________     _____________  ________   _____   __   _____ ____    __    ________________
   / __ )/ /   / __ \/ __ )   /_  __/ __ \   /_  __/ ____/ |/ /_  __/  /  _/ | / /  / ___// __ \  / /   /  _/_  __/ ____/
  / __  / /   / / / / __  |    / / / / / /    / / / __/  |   / / /     / //  |/ /   \__ \/ / / / / /    / /  / / / __/   
 / /_/ / /___/ /_/ / /_/ /    / / / /_/ /    / / / /___ /   | / /    _/ // /|  /   ___/ / /_/ / / /____/ /  / / / /___   
/_____/_____/\____/_____/    /_/  \____/    /_/ /_____//_/|_|/_/    /___/_/ |_/   /____/\___\_\/_____/___/ /_/ /_____/   
                                                                                                                         
\n''')

print('This script creates a copy of a sqlite database, parses the BLOB tables and , for each table found, creates a new BLOB_TEXT table in which the ASCII characters of the original table have been extracted.')
print('This allows to query on this new table.')
print('The script requires a SQLITE database as input.\n')

print("Specify the name of the database file or its path if it is not in the same folder as the script :")

# copy of the database
src = db
des = r'' + db.split('.')[0] + '_copy.db'

try:
    shutil.copy(src, des)
except IOError as e:
    print("Error while copying the database : " + e.strerror + " ***")
else:
    print("*** Successful copy of the database. ***")


# connection to the SQLite database
connexion = sqlite3.connect(des)
cursor = connexion.cursor()


def query(query_str):
    """
    @param query_str: string (SQL query)
    @return: dictionaries list (result of  de la requête)
    @description: Function that makes a SQL query and returns a list containing dictionaries.
    Each dictionary corresponds to a line (field name : field value).
    """
    cursor.execute(query_str)
    connexion.commit()
    return [dict(zip([column[0] for column in cursor.description], row)) for row in cursor.fetchall()]


def search_column_blob(table):
    """
    @param: table: string (name of the table)
    @description: Function that returns the list of blob columns of the table.
    @return: dictionary of strings (name of the blob columns: correspondence with the text column to create).
    Example of return : {'data': 'data_text', 'replydata': 'replydata_text'}
    """
    colonnes_blob = {}
    table_info = query("PRAGMA table_info(" + table + ")")
    # table_info is a list of dictionaries. Each dictionary contains information about a column of the table.
    for element in table_info:
        if element['type'] == "BLOB" or element['type'] == "blob":
            colonnes_blob[element['name']] = element['name'] + '_text'
            print("*** The column " + element['name'] +
                  " is a blob column ! ***")
    return colonnes_blob


def duplicates_colonnes_blob(table, dict_colonnes_blob):
    """
    @param: table: string (nom de la table)
    @param: dict_colonnes_blob: dictionary of strings (name of the blob columns: correspondence with the text column to create).
    @description: Function that creates text columns from blob columns.
    @return: confirmation message
    """
    # Creation of duplicate blob columns in text
    message = ""
    for colonne in dict_colonnes_blob.values():
        try:
            query("ALTER TABLE " + table + " ADD COLUMN " + colonne + " TEXT")
            message = message + "*** The column " + \
                colonne + " has been created ! ***" + "\n"
        except sqlite3.OperationalError:
            message = message + "*** The column " + colonne + " already exists.***" + "\n"
    return message


def convert_blob_to_text(colonne_blob, nouvelle_colonne, table):
    """
    @param: colonne_blob: string (name of the blob column)
    @param: nouvelle_colonne: string (name of the new column)
    @description: Function that converts blob data to text.
    """
    resultats_requete = query("SELECT " + colonne_blob + " FROM " + table)
    index = 0
    for ligne in resultats_requete:
        index += 1
        colonne_text = ''
        if ligne[colonne_blob] is not None:
            for (string, type, span, is_interesting) in b2s.extract_all_strings(ligne[colonne_blob], only_interesting=True):
                colonne_text = colonne_text + f"{string}" + '\n'
        if index == 1:
            print("*** Work in progress in the column " +
                  colonne_blob + " , please wait... ***")
        cursor.execute(
            "UPDATE " + table + " SET " + nouvelle_colonne + "= ? WHERE " + colonne_blob + "= ?", (colonne_text, ligne[colonne_blob]))
        connexion.commit()
    print("*** Conversion of blob data to txt performed on the column : " +
          colonne_blob + ". ***")


if __name__ == '__main__':
    # List the tables of the database
    tables = query(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    for table in tables:
        print("*** Work in progress on the table " + table['name'] + " ***")
        # Search for columns of type BLOB
        colonnes_blob = search_column_blob(table['name'])
        if len(colonnes_blob) == 0:
            print("*** No blob column was found in the table " +
                  table['name'] + " ***")
        # For each column of type BLOB found, we create a corresponding text column
        message = duplicates_colonnes_blob(table['name'], colonnes_blob)
        if len(message) > 0:
            print(message.rstrip())
        # For each value of the blob column, we convert the value into text
        for tuples in colonnes_blob.items():
            convert_blob_to_text(tuples[0], tuples[1], table['name'])
    print("The end ! The result is in : " + des)

cursor.close()
connexion.close()
