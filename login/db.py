from sqlalchemy import create_engine

# Modify according to your own MySQL configuration
USER = "root"
PASSWORD = "your_mysql_password"
PORT = "3306"
DB = "local_databasejcdecaux"
URI = "127.0.0.1"

# Connection string: using pymysql with SQLAlchemy
connection_string = f"mysql+pymysql://{USER}:{PASSWORD}@{URI}:{PORT}/{DB}"
engine = create_engine(connection_string, echo=False)

# Return the engine instance
def get_engine():
    return engine