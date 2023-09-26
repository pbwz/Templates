'''
A class for quick local database deployment. Serves as a wrapper 
for many of the SQLite3 commands but any more advanced commands 
can still be executed using exec_sql method.

v1.1
    - Added SQL injection protection for most methods
    
Author: Paul Belland
'''

import sqlite3

# Visualizer settings
VIS_LEN = 15  # length of rows for visualizing
VIS_SPACE = 5

# Search settings
FORMAT_SEARCH = True  # formats searches into dictionaries for lookup

class Database:
    '''Database class using SQLite 3 for quick project development.
    Allows simple interaction with the API + extra features.
    
    **WARNING** exec_sql and create_table are not safe from SQL injection.
    Please do no let users use create_table and if use safe_exec_sql for
    any queries where there is a risk of SQL injection.'''

    def __init__(self, db_name:str) -> None:
        # create/connect to db
        if db_name.endswith('.db'):
            self._con = sqlite3.connect(db_name)
        else:
            raise Exception('Filename must end with .db')
        
        self._cur = self._con.cursor()

    def create_table(self, table_name:str, table_cols:list[str]) -> None:
        '''Creates all tables needed for database

        Input: str - table_name
        Returns: list[str] - list of col names'''
        try:
            cols_str = ','.join(table_cols)
            tab_str = f"CREATE TABLE {table_name}({cols_str})"
            self._cur.execute(tab_str)
        except sqlite3.OperationalError as error:
            raise Exception('Table already exists')

    def get_table_names(self) -> list[str]:
        '''Returns names of all existing tables in DB

        Input: None
        Returns: list(str) of tables'''
        res = self._cur.execute("SELECT name FROM sqlite_master")
        raw_names = res.fetchall()

        # trim extra
        list_of_names = []
        for raw_name in raw_names:
            list_of_names.append(raw_name[0])

        return list_of_names

    def visualize_table(self, table_name:str) -> None:
        '''Allows visualization of tables in terminal

        Input: str - table name
        Return: None'''
        # get data from table
        data = self.get_table_rows(table_name)

        # get col names
        cols = self.get_table_cols(table_name)

        # assemble data
        matrix = []
        for i in range(len(cols)):
            inner_list = [cols[i]]

            for row in data:
                inner_list.append(row[i])

            matrix.append(inner_list)

        self._print_visual(matrix)

    def get_table_rows(self, table_name:str) -> list[tuple[str or int]]:
        '''Returns a list of every column inside of a given table
        
        Input: str - table_name
        Return: list[tuple] - all rows'''
        self._valid_table(table_name)   # injection check
        
        res = self._cur.execute(f"SELECT * FROM {table_name}")
        data = res.fetchall()
        return data
    
    def get_table_col(self, table_name:str, col_name:str) -> list[str or int]:
        '''Searches a given table and returns all values in
        the requested column.
        
        Input: str - table name, str - column name
        Return: list - column items'''
        # injection checks
        self._valid_table(table_name)
        self._valid_col(table_name, col_name)
        
        res = self._cur.execute(f"SELECT {col_name} FROM {table_name}")
        data = res.fetchall()
        
        # remove unnecessary tuples
        cleaned_data = []
        for item in data:
            cleaned_data.append(item[0])
            
        return cleaned_data
        
    def _valid_table(self, table_name:str) -> None:
        '''Checks if given table name exists, if not raises
        exception. Protects against SQL Injection
        
        Input: str - table name
        Return: None'''
        names = self.get_table_names()
        if table_name not in names:
            raise Exception('That table does not exist!')
        
    def _valid_col(self, table_name:str, col_name:str) -> None:
        '''Checks if a given column name exists, if not raises
        exception. Protects against SQL Injection
        
        Input: str - table name, str - column name
        Return: None'''
        cols = self.get_table_cols(table_name)
        if col_name not in cols:
            raise Exception('That column does not exist!')

    def _print_visual(self, data:list[list]):
        '''Prints out a visual of given table'''
        spacer = ' ' * VIS_SPACE
        divider = '-' * VIS_LEN

        # print headers
        for category in data:
            print(f'{category.pop(0)[:VIS_LEN]:<{VIS_LEN}}', end=spacer)
        print()

        # print divider
        for category in data:
            print(divider, end=spacer)
        print()

        # print items
        for i in range(len(category)):
            for category in data:
                item = str(category.pop(0))
                print(f'{item[:VIS_LEN]:<{VIS_LEN}}', end=spacer)
            print()

    def get_table_cols(self, table_name:str) -> list[str]:
        '''Returns names of all columns in table

        Input: str - table name
        Return: list[str] - col names'''
        self._valid_table(table_name)   # injection check
        
        schema = self._cur.execute(f"PRAGMA table_info({table_name})")

        # get names of all cols
        columns = []
        for row in schema:
            columns.append(row[1])  # get name

        return columns

    def insert(self, table_name:str, values:list) -> None:
        '''Inserts a new row into a database table

        Input: str - table name, list -  items for cols
        Return: None'''
        self._valid_table(table_name)   # injection check
        
        # account for different lengths
        form_values = tuple(values)
        q_vals = '?,' * len(values)
        q_vals = q_vals[:-1]  # remove trailing comma
        
        # try to insert given values
        try:
            self._cur.execute(f"INSERT INTO {table_name} values ({q_vals})",form_values)
            self._con.commit()
        except sqlite3.OperationalError as error:
            raise error

    def drop_table(self, table_name:str) -> None:
        '''Deletes/Drops a table from the database
        
        Input: str - table_name
        Return: None'''
        self._valid_table(table_name)   # injection check
        
        self._cur.execute(f"DROP TABLE {table_name}")

    def delete(self, table_name:str, ref_name:str, ref_val:int or str) -> None:
        '''Deletes an item (row) from the database using reference
        
        Input: str - table_name, str - ref_col_name, any - ref_val
        Return: None'''
        # injection checks
        self._valid_table(table_name)
        self._valid_col(table_name, ref_name)
        
        exec_str = f"DELETE FROM {table_name} WHERE {ref_name}=?"
        try:
            self._cur.execute(exec_str, (ref_val,))
            self._con.commit()
        except sqlite3.OperationalError as error:
            raise error

    def exec_sql(self,command:str,commit:bool = False) -> sqlite3.Cursor:
        '''Allows execution of more advanced SQL queries.
        If a commit is needed, add True as an arg after command.
        
        Input: str - command, bool - commit
        Return: sqlite3.Cursor'''
        try:
            response = self._cur.execute(command)
            
            # commits if needed
            if commit:
                self._con.commit()
            
            return response
        except sqlite3.OperationalError as error:
            raise error
        
    def safe_exec_sql(self,command:str,params:list,commit:bool = False) -> sqlite3.Cursor:
        '''Allows execution of more advanced SQL queries.
        If a commit is needed, add True as an arg after command.
        
        Safely tries to execute query. Use ? as placeholders in
        command then pass their values in a list under params.
        Protects against SQL Injection
        
        Input: str - command, list - params, bool - commit
        Return: sqlite3.Cursor'''
        try:
            params = tuple(params)
            response = self._cur.execute(command,params)
            
            # commits if needed
            if commit:
                self._con.commit()
            
            return response
        except sqlite3.OperationalError as error:
            raise error
    
    def search_for(self, table_name:str, ref_name:str,
                   ref_val:int or str) -> int or str:
        '''Very simple searching method, needs a reference
        and a value to find row, then returns all values
        
        ie. search_for('Table_1', 'ID', 365):
            This will attempt to search for a row containing
            an ID cell with the value 365 and will return the
            value of the cell Price associated with it
        
        Input: str - table_name, str - ref_name, str/int - ref_val  
        Return: int or str - result '''
        # injection checks
        self._valid_table(table_name)
        self._valid_col(table_name, ref_name)
        
        exec_str = f"SELECT * FROM {table_name} WHERE {ref_name} = ?"
        
        try:
            res = self._cur.execute(exec_str,(ref_val,))
            results = list(res.fetchall())
            
            # format if setting on
            if FORMAT_SEARCH:
                cols = self.get_table_cols(table_name)
                
                form_dict = {}
                for i in range(len(results)):
                    form_dict[i] = {}
                    
                    for j in range(len(results[i])):
                        form_dict[i][cols[j]] = results[i][j]
                return form_dict
            return results
            
        except sqlite3.OperationalError as error:
            raise Exception('No matches found')
    
    def insert_for(self, table:str, r_name:str, r_val:int or str, 
                   c_name:str, c_val: int or str) -> None:
        '''Inserts a value into a cell, needs a reference
        and a reference value to find correct row.
        
        ie. insert_for('Table_1','ID',365,'Name','Dan')
            This will search table 1 for a row containing an
            ID of 365, then will update the Name of that row
            to Dan.
            
        Input: str - table, str - ref_name, str or int - ref_val,
        str - change_name, str or int - change_value
        Return: None'''
        # injection checks
        self._valid_table(table)
        self._valid_col(table, c_name)
        self._valid_col(table, r_name)
        
        cmd =f"UPDATE {table} SET {c_name} = ? WHERE {r_name} = ?" 
        
        try:
            self._cur.execute(cmd, (c_val,r_val))
            self._con.commit()
        except sqlite3.OperationalError as error:
            raise Exception('Failed to update cell')
    
def main():
    '''Main function for testing purposes'''
    database = Database('test.db')

if __name__ == '__main__':
    main()
