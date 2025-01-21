# RO-Crate metadata storage with Apache Jena Fuseki

https://jena.apache.org/documentation/fuseki2


```
mkdir fuseki-data
docker compose up
```

Open http://localhost:3030 in a browser window to access the web UI.

Switch to another terminal window.

```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

python load_crate.py crate1
python load_crate.py crate2
python query_store.py query.txt
```
