import mysql.connector # type: ignore
from mysql.connector import Error # type: ignore
import config # type: ignore
from tkinter import messagebox
import typing

class Database:
    def __init__(self):
        self.connection: typing.Any = None
        self.cursor: typing.Any = None
        self.connect()

    def connect(self):
        """Establish a connection to the MySQL database."""
        try:
            self.connection = mysql.connector.connect(
                host=config.DB_HOST,
                user=config.DB_USER,
                password=config.DB_PASSWORD,
                database=config.DB_NAME
            )
            if self.connection and self.connection.is_connected():
                self.cursor = self.connection.cursor(dictionary=True)
                print("DEBUG: Successfully connected to database")
        except Error as e:
            messagebox.showerror("Database Error", f"Failed to connect to MySQL database.\nError: {e}\nEnsure MySQL is running and the database exists.")
            print(f"Error while connecting to MySQL: {e}")
            self.connection = None
            self.cursor = None

    def execute_query(self, query, params=None):
        """Execute a single query (INSERT, UPDATE, DELETE)."""
        if self.connection and self.connection.is_connected():
            try:
                self.cursor.execute(query, params or ())
                self.connection.commit()
                return self.cursor.lastrowid
            except Error as e:
                print(f"Error executing query: {e}")
                self.connection.rollback()
                return None
        return None

    def fetch_all(self, query, params=None):
        """Fetch multiple rows from a SELECT query."""
        if self.connection and self.connection.is_connected():
            try:
                self.cursor.execute(query, params or ())
                return self.cursor.fetchall()
            except Error as e:
                print(f"Error fetching data: {e}")
                return []
        return []

    def fetch_one(self, query, params=None):
        """Fetch a single row from a SELECT query."""
        if self.connection and self.connection.is_connected():
            try:
                self.cursor.execute(query, params or ())
                return self.cursor.fetchone()
            except Error as e:
                print(f"Error fetching data: {e}")
                return None
        return None

    def close(self):
        """Close the database connection and cursor."""
        try:
            if self.cursor:
                self.cursor.close()
            if self.connection and self.connection.is_connected():
                self.connection.close()
            print("MySQL connection is closed.")
        except Exception as e:
            print(f"Error during database close: {e}")
