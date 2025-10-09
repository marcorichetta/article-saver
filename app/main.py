from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException, Header, Request, Depends
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from feedgen.feed import FeedGenerator
from firebase_admin import firestore
from pydantic import BaseModel

from .config import Config, initialize_firebase

app = FastAPI(title=Config.APP_TITLE, version=Config.APP_VERSION)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=Config.CORS_METHODS,
    allow_headers=Config.CORS_HEADERS,
)


# Pydantic models
class ArticleRequest(BaseModel):
    url: str
    title: Optional[str] = None
    content: Optional[str] = None


@app.get("/")
def home():
    return {
        "name": "Article Saver API",
        "version": Config.APP_VERSION,
    }


@app.post("/api/add_article")
async def add_article_handler(
    article: ArticleRequest,
    authorization: Optional[str] = Header(None),
    db=Depends(initialize_firebase),
):
    # --- Verificación de Clave API (¡MUY IMPORTANTE para seguridad!) ---
    # La clave API se debe configurar como una variable de entorno en Vercel.
    API_KEY = Config.ADD_ARTICLE_API_KEY

    if not API_KEY or not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")

    provided_key = authorization.split(" ")[1]
    if provided_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")

    # --- Procesamiento de la Petición ---
    if not db:
        raise HTTPException(
            status_code=500, detail="Database not initialized. Check server logs."
        )

    try:
        new_article = {
            "url": article.url,
            "title": article.title if article.title else "Sin Título",
            "content": article.content if article.content else "",
            "createdAt": firestore.firestore.SERVER_TIMESTAMP,  # Firestore gestiona el timestamp
        }
        # Guarda en la colección 'articles'
        doc_ref = db.collection("articles").add(new_article)

        # Retorna el artículo guardado (sin el createdAt real hasta que se complete)
        # Para una respuesta más precisa, podrías hacer un get() después de add()
        response_article = {
            "id": doc_ref[1].id,  # doc_ref[1] es la referencia del documento
            "url": article.url,
            "title": article.title if article.title else "Sin Título",
            "content": article.content if article.content else "",
            "createdAt": datetime.now(timezone.utc).isoformat()
            + "Z",  # Timestamp aproximado para la respuesta
        }

        return {"message": "Artículo añadido con éxito.", "article": response_article}

    except Exception as e:
        print(f"Error al añadir artículo: {e}")
        raise HTTPException(status_code=500, detail=f"Fallo al añadir artículo: {e}")


@app.get("/api/rss_feed")
async def rss_feed_handler(request: Request, db=Depends(initialize_firebase)):
    # --- Generación del Feed RSS ---
    if not db:
        return Response(
            content="<error>Database not initialized. Check server logs.</error>",
            media_type="application/xml",
            status_code=500,
        )

    try:
        # Crea una nueva instancia de FeedGenerator
        fg = FeedGenerator()
        fg.title(Config.RSS_FEED_TITLE)
        fg.link(
            href=str(request.url).replace("http://", "https://"),
            rel="self",
        )  # Asegura HTTPS
        fg.description(Config.RSS_FEED_DESCRIPTION)
        fg.language(Config.RSS_FEED_LANGUAGE)

        # Opcional: Puedes establecer un autor o un logo si quieres
        # fg.author({'name': 'Tu Nombre', 'email': 'tu.email@ejemplo.com'})
        # fg.logo('http://example.com/logo.png')

        # Obtiene los artículos de Firestore
        articles_ref = db.collection("articles")
        snapshot = (
            articles_ref.order_by(
                "createdAt", direction=firestore.firestore.Query.DESCENDING
            )
            .limit(Config.RSS_FEED_LIMIT)
            .stream()
        )

        # Añade cada artículo como una entrada al feed
        for doc in snapshot:
            article = doc.to_dict()
            fe = fg.add_entry()  # Crea una nueva entrada de feed

            fe.title(article.get("title", "Sin Título"))
            fe.link(href=article.get("url", "#"), rel="alternate")  # link del artículo
            fe.guid(
                article.get("url") or doc.id, permalink=True
            )  # GUID para identificar el artículo

            # Convierte el timestamp de Firestore a un objeto datetime si existe
            if article.get("createdAt"):
                if isinstance(article["createdAt"], datetime):
                    fe.pubDate(article["createdAt"].astimezone(timezone.utc))
                elif hasattr(
                    article["createdAt"], "toDate"
                ):  # Para objetos Timestamp de Firestore
                    fe.pubDate(article["createdAt"].toDate().astimezone(timezone.utc))
            else:
                fe.pubDate(
                    datetime.now(timezone.utc)
                )  # Fecha actual si no hay createdAt

            # Contenido HTML para la descripción
            fe.content(article.get("content", ""), type="html")

        # Genera el XML del feed RSS
        rss_feed_xml = fg.rss_str(pretty=True)  # pretty=True para un XML legible

        # Envía la respuesta con el Content-Type correcto
        return Response(
            rss_feed_xml,
            media_type="application/rss+xml; charset=utf-8",
            status_code=200,
        )

    except Exception as e:
        print(f"Error al generar el feed RSS: {e}")
        # En caso de error, devuelve un XML de error para que los clientes RSS puedan manejarlo
        error_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
    <title>Error en Mi Feed de Artículos Personal</title>
    <link>#</link>
    <description>Fallo al generar el feed RSS: {str(e)}</description>
</channel>
</rss>"""
        return Response(error_xml, media_type="application/xml", status_code=500)
