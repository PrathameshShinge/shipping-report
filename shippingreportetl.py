# -*- coding: utf-8 -*-
"""shippingReportETL.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/14HvCjEzIss4i2byMOWGhmU04cPSl7MLw
"""

!pip install mysql-connector-python pandas sqlalchemy

import mysql.connector
from mysql.connector import Error
import pandas as pd
from sqlalchemy import create_engine
import requests
import json

# Database credentials
hostname = 'sql5.freesqldatabase.com'
database = 'sql5711603'
username = 'sql5711603'
password = 'icLgYtdYxS'

# Create a connection to the database
def create_connection():
    try:
        connection = mysql.connector.connect(
            host=hostname,
            database=database,
            user=username,
            password=password
        )
        if connection.is_connected():
            print("Connected to MySQL database")
        return connection
    except Error as e:
        print(f"Error: {e}")
        return None

# Drop tables and handle foreign key constraints
def drop_tables(connection):
    cursor = connection.cursor()
    try:
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
        cursor.execute("DROP TABLE IF EXISTS Shipment;")
        cursor.execute("DROP TABLE IF EXISTS Orders;")
        cursor.execute("DROP TABLE IF EXISTS Product;")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
        connection.commit()
        print("Tables dropped successfully.")
    except Error as e:
        print(f"Error: {e}")
    cursor.close()

# Create tables
def create_tables(connection):
    create_product_table = """
    CREATE TABLE IF NOT EXISTS Product (
        ProductCode VARCHAR(50) PRIMARY KEY,
        ProductDescription VARCHAR(255)
    );
    """
    create_orders_table = """
    CREATE TABLE IF NOT EXISTS Orders (
        OrderId VARCHAR(50) PRIMARY KEY,
        CurrencyCode VARCHAR(10),
        OrderDate DATE,
        ProductCode VARCHAR(50),
        ProductDescription VARCHAR(255),
        OrderQuantity DECIMAL(10, 2),
        UnitCost DECIMAL(10, 2),
        OrderNumber VARCHAR(50),
        OrderSource TEXT,
        AddressLine1 VARCHAR(255),
        AddressLine2 VARCHAR(255),
        CountryCode VARCHAR(50),
        FirstName VARCHAR(50),
        LastName VARCHAR(50),
        Postcode VARCHAR(50),
        Town VARCHAR(50)
    );
    """
    create_shipment_table = """
    CREATE TABLE IF NOT EXISTS Shipment (
        OrderId VARCHAR(50) PRIMARY KEY,
        Carrier VARCHAR(50),
        DispatchDate DATE,
        DispatchReference VARCHAR(50),
        ProductCode VARCHAR(50),
        ProductDescription VARCHAR(255),
        DispatchedQuantity DECIMAL(10, 2),
        SerialNumbers TEXT,
        TrackingNumber VARCHAR(50),
        TrackingURL VARCHAR(255)
    );
    """
    cursor = connection.cursor()
    cursor.execute(create_product_table)
    cursor.execute(create_orders_table)
    cursor.execute(create_shipment_table)
    connection.commit()
    cursor.close()

# Verify table creation and data insertion
def verify_schema(connection):
    cursor = connection.cursor()

    try:
        # Check table creation
        cursor.execute("SHOW TABLES;")
        tables = cursor.fetchall()
        print("Tables in the database:")
        for table in tables:
            print(table[0])

        # Check table structure
        tables_to_describe = ['Product', 'Orders', 'Shipment']
        for table in tables_to_describe:
            print(f"\nStructure of {table}:")
            cursor.execute(f"DESCRIBE {table};")
            structure = cursor.fetchall()
            for column in structure:
                print(column)

        # Check data insertion
        tables_to_select = ['Product', 'Orders', 'Shipment']
        for table in tables_to_select:
            print(f"\nData in {table}:")
            cursor.execute(f"SELECT * FROM {table} LIMIT 3;")
            rows = cursor.fetchall()
            if rows:
                for row in rows:
                    print(row)
            else:
                print("No data found.")

        # Run sample queries
        print("\nSample query results:")
        sample_queries = [
            """
            SELECT p.ProductCode, p.ProductDescription, s.DispatchedQuantity\
            , s.DispatchDate
            FROM Product p
            JOIN Shipment s ON p.ProductCode = s.ProductCode
            LIMIT 3;
            """,
            """
            SELECT o.OrderId, o.OrderDate, o.OrderNumber, s.ProductCode\
            , s.DispatchedQuantity, s.DispatchDate
            FROM Orders o
            JOIN Shipment s ON o.OrderId = s.OrderId
            LIMIT 3;
            """,
            """
            SELECT o.OrderId, o.OrderDate, o.OrderNumber, s.DispatchReference\
            , s.Carrier, s.DispatchDate, p.ProductCode, p.ProductDescription\
            , s.DispatchedQuantity
            FROM Orders o
            JOIN Shipment s ON o.OrderId = s.OrderId
            JOIN Product p ON s.ProductCode = p.ProductCode
            LIMIT 3;
            """
        ]
        for query in sample_queries:
            print(f"\nRunning query:\n{query.strip()}")
            cursor.execute(query)
            results = cursor.fetchall()
            if results:
                for result in results:
                    print(result)
            else:
                print("No results found.")

    except Error as e:
        print(f"Error: {e}")

    cursor.close()

# Load data into tables
def load_data(connection, df, table_name, if_exists='replace'):
    engine = create_engine(f'mysql+mysqlconnector://{username}:{password}@{hostname}/{database}')
    df.to_sql(table_name, con=engine, if_exists=if_exists, index=False)

# Main function
def main():
    connection = create_connection()
    if connection is None:
        return

    drop_tables(connection)

    create_tables(connection)

    # Fetch the JSON data from the URL
    url = "https://nanit-bi-assginment.s3.amazonaws.com/shippingdata.json"
    response = requests.get(url)
    data = response.json()

    # Convert JSON to DataFrame
    orders = data['Order']
    orders_df = pd.json_normalize(orders, sep='_')

    # Rename ShippingAddress columns
    orders_df.rename(columns={
        'ShippingAddress_AddressLine1': 'AddressLine1',
        'ShippingAddress_AddressLine2': 'AddressLine2',
        'ShippingAddress_CountryCode': 'CountryCode',
        'ShippingAddress_FirstName': 'FirstName',
        'ShippingAddress_LastName': 'LastName',
        'ShippingAddress_Postcode': 'Postcode',
        'ShippingAddress_Town': 'Town'
    }, inplace=True)

    # Convert OrderDate to date only
    orders_df['OrderDate'] = pd.to_datetime(orders_df['OrderDate']).dt.date

    # Normalize the Dispatches data
    dispatches_df = pd.json_normalize(orders, 'Dispatches', ['OrderId'], sep='_')

    # Convert DispatchDate to date only
    dispatches_df['DispatchDate'] = pd.to_datetime(dispatches_df['DispatchDate']).dt.date

    # Normalize the DispatchedLines data within Dispatches
    dispatched_lines_df = pd.json_normalize(dispatches_df.to_dict(orient='records')\
                            , 'DispatchedLines', ['OrderId', 'DispatchDate'\
                            , 'Carrier', 'DispatchReference', 'TrackingNumber'\
                            , 'TrackingURL'], sep='_')

    # Normalize the OrderLines data
    order_lines_df = pd.json_normalize(orders, 'OrderLines', ['OrderId'], sep='_')

    # Load Product dimension table
    product_df = order_lines_df[['ProductCode', 'ProductDescription']].drop_duplicates()
    print("Product DataFrame:")
    print(product_df.head())
    load_data(connection, product_df, 'Product', if_exists='replace')

    # Load Orders dimension table
    orders_dim_df = order_lines_df.merge(
        orders_df[['OrderId', 'CurrencyCode', 'OrderDate', 'OrderNumber', 'OrderSource'\
                 , 'AddressLine1', 'AddressLine2', 'CountryCode', 'FirstName'\
                 , 'LastName', 'Postcode', 'Town']],
        on='OrderId',
        how='left'
    )
    orders_dim_df.rename(columns={'Quantity': 'OrderQuantity'}, inplace=True)
    print("Orders DataFrame:")
    print(orders_dim_df.head())
    load_data(connection, orders_dim_df, 'Orders', if_exists='replace')

    # Load Shipment fact table
    shipment_fact_df = dispatched_lines_df.merge(
        orders_df[['OrderId', 'OrderSource']],
        on='OrderId',
        how='left'
    )
    shipment_fact_df.rename(columns={'Quantity': 'DispatchedQuantity'}, inplace=True)
    # Convert SerialNumbers to JSON strings
    shipment_fact_df['SerialNumbers'] = shipment_fact_df['SerialNumbers']\
                    .apply(lambda x: json.dumps(x) if isinstance(x, list) else x)

    print("Shipment DataFrame:")
    print(shipment_fact_df.head())
    load_data(connection, shipment_fact_df, 'Shipment', if_exists='replace')

    #Verify tables
    verify_schema(connection)

    # Close the connection
    connection.close()

if __name__ == '__main__':
    main()

