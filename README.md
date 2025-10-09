# Article Saver

JS function to save articles from a URL to a database in Firebase.

## Usage

### Read RSS

https://article-saver.vercel.app/api/rss.xml

### Save Article

Save articles by sending a POST request to the API endpoint with the article details in JSON format.

```shell
curl -X POST \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer key" \
     -d '{"url": "https://www.clearerthinking.org/post/believing-you-only-have-one-option-is-dangerous", "title": "Believing You Only Have One Option Is Dangerous", "content": "Un análisis de por qué tener múltiples opciones es crucial para la toma de decisiones."}' \
     https://article-saver.vercel.app/api/add-article

# Example Response
{
    "message":"Artículo añadido con éxito.",
    "article":{
        "url":"https://www.website.com",
        "title":"La Noticia del Día",
        "content":"Un resumen breve de la noticia más importante.",
        "createdAt":{}
    }
}
```

### JS Bookmarklet

Create a new bookmark and paste the content in bookmarklet.js. Minify it!
