# shipping-report dashboard
https://lookerstudio.google.com/reporting/101ace48-8060-4c47-9e3c-9c916670f5b0

## Overview
This project fetches JSON shipping data from the URL, normalizes it, loads it into a freesqldatabase.com, and creates an interactive dashboard using a Google Looker Studio. The dashboard allows users to see how many units were shipped by day and filter the data by Product, Order Source, and Date Range.

## Project Structure
shipping-dashboard/
├── shippingreportetl.py
├── database_tables_created.png
├── Shipping_Report___Prat_Shinge.pdf
└── README.md

- `shippingreportetl.py`: The main script that fetches, normalizes, and loads the data into the freesqldatabase.
- `database_tables_created.png`: A screenshot of the tables that are loaded through the script.
- `Shipping_Report___Prat_Shinge.pdf`: The dashboard saved as a PDF file (non-interactive)
- `README.md`: This file, providing an overview for the project and the link to the interactive dahsboard.
