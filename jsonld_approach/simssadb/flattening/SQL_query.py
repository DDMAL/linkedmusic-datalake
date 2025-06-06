import psycopg2
import csv
import re


# steps:
#   1. upload the simssadb dump to a local postgreSQL database called 'simssadb'.
#   2. change db_params fields below as needed.
#   3. Run the scripts, generate the flattened.csv file.
#   Each row associates with a different file_id. File-to-work flattening happens after this, in the script restructure.py (with pandas)
#   flattened.csv however has all the associated features of each file flattened.
#   4. Reconcile the generated flattened.csv and run the script with restructure.py

# Query main info from the database
db_params = {
    'dbname': 'simssadb',
    'user': 'postgres',
    'password': 'postgres',
    'host': 'localhost'
}

author_query = """
    CREATE VIEW author AS
    SELECT
        musical_work.id AS musical_work_id,
        contribution_musical_work.id AS contribution_id,
        person.given_name AS given_name,
        person.surname AS sur_name,
        person.authority_control_url AS auth_URL
    FROM
        musical_work
    FULL OUTER JOIN
        contribution_musical_work ON contribution_musical_work.contributed_to_work_id = musical_work.id
    FULL OUTER JOIN
        person ON contribution_musical_work.person_id = person.id
    WHERE contribution_musical_work.role = 'AUTHOR'
"""

composer_query = """
    CREATE VIEW composer AS
    SELECT
        musical_work.id AS musical_work_id,
        contribution_musical_work.id AS contribution_id,
        person.given_name AS given_name,
        person.surname AS sur_name,
        person.authority_control_url AS auth_URL
    FROM
        musical_work
    FULL OUTER JOIN
        contribution_musical_work ON contribution_musical_work.contributed_to_work_id = musical_work.id
    FULL OUTER JOIN
        person ON contribution_musical_work.person_id = person.id
    WHERE contribution_musical_work.role = 'COMPOSER'
"""

# flattened_view_query_with_features = """
#     CREATE VIEW flattened_view AS
#     SELECT
#         musical_work.id AS musical_work_id,
#         musical_work.variant_titles AS musical_work_variant_titles,
#         musical_work.sacred_or_secular AS sacred_or_secular,
#         author.given_name AS author_given_name,
#         author.sur_name AS author_sur_name,
#         author.auth_URL AS author_auth_URL,
#         author.contribution_id AS author_contribution_id,
#         composer.given_name AS composer_given_name,
#         composer.sur_name AS composer_sur_name,
#         composer.auth_URL AS composer_auth_URL,
#         composer.contribution_id AS composer_contribution_id,
#         genre_style.genre_style AS genre_style,
#         genre_type.genre_type AS genre_type,
#         source_instantiation.portion AS source_instantiation_portion,
#         source.title AS source_title,
#         source.source_type AS source_type,
#         source.url AS source_url,
#         source.id AS source_id,
#         files.file_type AS file_type,
#         files.file_format AS file_format,
#         files.version AS file_version,
#         'https://db.simssa.ca/files/' || files.id AS url_to_file,
#         extracted.value AS extracted_value,
#         extracted.feature AS feature
#     FROM
#         musical_work
#     FULL OUTER JOIN
#         author ON author.musical_work_id = musical_work.id
#     FULL OUTER JOIN
#         composer ON composer.musical_work_id = musical_work.id
#     FULL OUTER JOIN
#         source_instantiation ON musical_work.id = source_instantiation.work_id
#     FULL OUTER JOIN
#         source ON source_instantiation.source_id = source.id
#     FULL OUTER JOIN
#         files ON files.instantiates_id = source_instantiation.id
#     FULL OUTER JOIN
#         (SELECT m.musicalwork_id AS mid, g.name AS genre_style FROM musical_work_genres_as_in_style m JOIN genre_as_in_style g
#         ON m.genreasinstyle_id = g.id)genre_style
#         ON genre_style.mid = musical_work.id
#     FULL OUTER JOIN
#         (SELECT m.musicalwork_id AS mid, g.name AS genre_type FROM musical_work_genres_as_in_type m JOIN genre_as_in_type g
#         ON m.genreasintype_id = g.id)genre_type
#         ON genre_type.mid = musical_work.id
#     FULL OUTER JOIN
#         (SELECT f.name AS feature, e.feature_of_id AS feature_of_id, e.value AS value FROM extracted_feature e JOIN feature f ON e.instance_of_feature_id = f.id)extracted
#         ON files.id = extracted.feature_of_id
#     WHERE musical_work.id IS NOT NULL
#  """

compact_files_query = """
    CREATE VIEW compact_files AS
    SELECT
        musical_work.id AS musical_work_id,
        files.id AS file_id,
        files.file_type AS file_type,
        files.file_format AS file_format,
        files.version AS file_version,
        'https://db.simssa.ca/files/' || files.id AS url_to_file
    FROM
        musical_work
    FULL OUTER JOIN
        source_instantiation ON musical_work.id = source_instantiation.work_id
    FULL OUTER JOIN
        source ON source_instantiation.source_id = source.id
    FULL OUTER JOIN
        files ON files.instantiates_id = source_instantiation.id
    WHERE musical_work.id IS NOT NULL AND files.id IS NOT NULL
"""

flattened_view_query = """
    CREATE VIEW flattened_view AS
    SELECT
        musical_work.id AS musical_work_id,
        musical_work.variant_titles AS musical_work_variant_titles,
        musical_work.sacred_or_secular AS sacred_or_secular,
        author.given_name AS author_given_name,
        author.sur_name AS author_sur_name,
        author.auth_URL AS author_auth_URL,
        author.contribution_id AS author_contribution_id,
        composer.given_name AS composer_given_name,
        composer.sur_name AS composer_sur_name,
        composer.auth_URL AS composer_auth_URL,
        composer.contribution_id AS composer_contribution_id,
        genre_style.genre_style AS genre_style,
        genre_type.genre_type AS genre_type,
        source_instantiation.portion AS source_instantiation_portion,
        source.title AS source_title,
        source.source_type AS source_type,
        source.url AS source_url,
        source.id AS source_id
    FROM
        musical_work
    FULL OUTER JOIN
        author ON author.musical_work_id = musical_work.id
    FULL OUTER JOIN
        composer ON composer.musical_work_id = musical_work.id
    FULL OUTER JOIN
        source_instantiation ON musical_work.id = source_instantiation.work_id
    FULL OUTER JOIN
        source ON source_instantiation.source_id = source.id
    FULL OUTER JOIN
        (SELECT m.musicalwork_id AS mid, g.name AS genre_style FROM musical_work_genres_as_in_style m JOIN genre_as_in_style g
        ON m.genreasinstyle_id = g.id)genre_style
        ON genre_style.mid = musical_work.id
    FULL OUTER JOIN
        (SELECT m.musicalwork_id AS mid, g.name AS genre_type FROM musical_work_genres_as_in_type m JOIN genre_as_in_type g
        ON m.genreasintype_id = g.id)genre_type
        ON genre_type.mid = musical_work.id
    WHERE musical_work.id IS NOT NULL
 """

# creating the initial flattened view
conn = psycopg2.connect(**db_params)
cur = conn.cursor()
cur.execute(author_query)
cur.execute(composer_query)
cur.execute(flattened_view_query)
cur.execute(compact_files_query)



# # START FEATURE FLATTENING
# # get distinct feature names:
# cur.execute("SELECT DISTINCT feature FROM flattened_view")
# feature_names = [row[0] for row in cur.fetchall()]

# # for renaming feature names for column compatibility
# def sanitize_column_name(name):
#     if name is None:
#         return None
#     return re.sub(' ', '_', name)

# # Create feature columns
# feature_columns = ", ".join(
#     f"MAX(CASE WHEN feature = '{name}' THEN extracted_value ELSE NULL END) AS  \"{sanitize_column_name(name)}\""
#     for name in feature_names
# )
# cur.execute("""SELECT column_name
#     FROM information_schema.columns
#     WHERE table_name = 'flattened_view'""")
# exclude_list=['extracted_value', 'feature']
# flattened_column_names = ", ".join([row[0] for row in cur.fetchall() if row[0] not in exclude_list])

# return all columns
final_query_flattened_view = """
    SELECT *
    FROM flattened_view
"""
# run
cur.execute(final_query_flattened_view)
results = cur.fetchall()

# Export data to CSV
with open('initial_flattened.csv', 'w') as f:
    writer = csv.writer(f)
    writer.writerow([col[0] for col in cur.description])
    writer.writerows(results)

# also export the files to another csv
final_query_compact_files = """
    SELECT *
    FROM compact_files
"""
# run
cur.execute(final_query_compact_files)
results = cur.fetchall()

# Export data to CSV
with open('files.csv', 'w') as f:
    writer = csv.writer(f)
    writer.writerow([col[0] for col in cur.description])
    writer.writerows(results)

# Clean up
cur.close()
conn.close()