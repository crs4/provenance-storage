# Apache Jena Fuseki

https://jena.apache.org/documentation/fuseki2


## Fuseki Docker Tools

https://jena.apache.org/documentation/fuseki2/fuseki-docker.html

Download [jena-fuseki-docker-5.1.0.zip](https://repo1.maven.org/maven2/org/apache/jena/jena-fuseki-docker/5.2.0/jena-fuseki-docker-5.2.0.zip)

```
unzip jena-fuseki-docker-5.2.0.zip
cd jena-fuseki-docker-5.2.0
docker compose build --build-arg JENA_VERSION=5.2.0
docker compose run --rm --service-ports fuseki --mem /ds
```

Switch to another terminal window.

```console
cd ..
git clone https://github.com/hectorcorrea/fuseki_demo
cd fuseki_demo
curl -X POST -d @the_raven.n3 localhost:3030/ds/update
<html>
<head>
</head>
<body>
<h1>Success</h1>
<p>
Update succeeded
</p>
</body>
</html>
curl -X POST -d "query=select ?s where { ?s ?p ?o . }" localhost:3030/ds/query
{ "head": {
    "vars": [ "s" ]
  } ,
  "results": {
    "bindings": [
      { 
        "s": { "type": "uri" , "value": "http://demo/book1" }
      } ,
      { 
        "s": { "type": "uri" , "value": "http://demo/book1" }
      }
    ]
  }
}
```
