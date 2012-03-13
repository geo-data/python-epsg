"""
Update a database with new data from the EPSG web service
"""

import schema

def update(objects, engine):
    from sqlalchemy.orm import sessionmaker

    Session = sessionmaker(engine)
    session = Session()
    session.begin(subtransactions=True)

    conn = session.connection()
    # wrap the database update in the current transaction
    schema.Base.metadata.drop_all(conn)
    schema.Base.metadata.create_all(conn)
    
    session.add_all(objects)

    session.commit()
