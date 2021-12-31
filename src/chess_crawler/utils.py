"""
Utility functions to be used with the chess crawler
"""
from typing import List

import pandas as pd
import sqlalchemy as sal

def delete_duplicate_entries_from_db(engine: sal.engine.Engine, table_name: str) -> None:
    """
    Deletes the entries with the same player_id from the database
    """
    # Define the SQL command
    sql_command = f"""
    WITH temp AS
    (SELECT MAX(row_id) AS max_id FROM {table_name} 
    GROUP BY username)  

    DELETE FROM {table_name} WHERE row_id NOT IN
    (SELECT max_id FROM temp);
    """

    # Convert to SQLAlchemy text
    sql_text = sal.text(sql_command)

    # exectute the command
    with engine.begin() as conn:
        conn.execute(sql_text)

def get_usernames(engine: sal.engine.Engine) -> List[str]:
    """
    Gets the unique usernames in the 'profiles' table and returns them as a list
    """
    with engine.connect() as conn:
        df = pd.read_sql_table('profiles', conn)

    # Remove duplicates of the same user
    df.drop_duplicates(subset = 'id', inplace = True)

    return df.username.tolist()