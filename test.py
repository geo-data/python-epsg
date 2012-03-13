from sqlalchemy import create_engine
import update, load

loader = load.Loader(load.XML.FromFile('/home/hrz/checkouts/medin-portal/db.xml'))
loader.load()

engine = create_engine('sqlite:///:memory:', echo=True)

update.update(loader.values(), engine)
