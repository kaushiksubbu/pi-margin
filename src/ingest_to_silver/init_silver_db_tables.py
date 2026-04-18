import duckdb
import os

# Update this path to match your config
SILVER_PATH = "/home/kaushik/pi-margin/data/databases/master_data.db"
GOLD_PATH = "/home/kaushik/pi-margin/data/databases/analytics.db"
BRONZE_PATH = "/home/kaushik/pi-margin/data/databases/raw_source.db"
# Ensure the directory exists
os.makedirs(os.path.dirname(SILVER_PATH), exist_ok=True)

def initialize_vault():
    print(f"Creating Silver DB at: {SILVER_PATH}")
    # Connecting to a file that doesn't exist creates it automatically
    con_s = duckdb.connect(SILVER_PATH)
    con_g = duckdb.connect(GOLD_PATH) 
    con_b= duckdb.connect(BRONZE_PATH)
    
    try:

        
        # Create the Satellite (The Historical Record)
        # con_s.execute("""
        #     DROP TABLE IF EXISTS sat_commodity_prices;
        #         CREATE TABLE sat_commodity_prices (
        #             hub_commodity_key  VARCHAR,
        #             hash_diff          VARCHAR,
        #             open_price         DOUBLE,
        #             high_price         DOUBLE,
        #             low_price          DOUBLE,
        #             close_price        DOUBLE,
        #             volume             BIGINT,
        #             load_timestamp     TIMESTAMP,
        #             record_source      VARCHAR,
        #             PRIMARY KEY (hub_commodity_key, load_timestamp)
        #         );
        # """)
        #         # Create the Hub (The Unique Identity)
        # con_s.execute("""
        #         DROP TABLE IF EXISTS hub_commodity;
        #         CREATE TABLE hub_commodity (
        #             hub_commodity_key  VARCHAR PRIMARY KEY,
        #             commodity_id       VARCHAR,
        #             load_timestamp     TIMESTAMP,
        #             record_source      VARCHAR
        #         );
        # """)
        con_s.execute("""CREATE TABLE IF NOT EXISTS margin_sensitivity (
                    category_name VARCHAR,
                    commodity_id  VARCHAR,
                    sensitivity_factor DOUBLE -- e.g., 0.05 means 1% gas hike = 0.05% margin drop
                    );
                    INSERT INTO margin_sensitivity VALUES ('Retail_Fuel', 'TTF_GAS', 0.12);
                    INSERT INTO margin_sensitivity VALUES ('Logistics_Freight', 'TTF_GAS', 0.08);
                    insert into margin_sensitivity values ('Airlines_Fuel', 'JET_FUEL', 0.15);
                    """)
        print("Success! Silver tables are ready.")
        print(con_s.execute("show tables;").fetchall())  
        print(con_g.execute("show tables;").fetchall())  
        print(con_s.execute("SELECT count(*) FROM sat_commodity_prices;").fetchall())
        print(con_s.execute("SELECT count(*) FROM hub_commodity;").fetchall())
        print(con_s.execute("select * from margin_sensitivity;").fetchall())
        #con_g.execute("drop table if exists sat_commodity_prices; drop table if exists hub_commodity;")
        #print(con_g.execute("show tables;").fetchall())  
        #print(con_b.execute("show tables;").fetchall())  
    except Exception as e:
        print(f"Error: {e}")
    finally:
        con_s.close()

if __name__ == "__main__":
    initialize_vault()