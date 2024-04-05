from fastapi import FastAPI, HTTPException, Form, Request
from fastapi.templating import Jinja2Templates
from typing import Optional
import uvicorn
from lp import Storage, Search

app = FastAPI()
storage = Storage("maas")
searcher = Search(storage)
templates = Jinja2Templates(directory="templates")


@app.get("/")
async def get_search_page(request: Request):
    """
    Serve the search page.
    """
    return templates.TemplateResponse("search.html", {"request": request})


@app.post("/search/")
async def search(request: Request, query: str = Form(...), limit: Optional[int] = 10):
    """
    Handle the search query and return results.
    """
    try:
        results = searcher.find_similar_issues(query, limit)
        return templates.TemplateResponse(
            "search.html", {"request": request, "results": results, "query": query}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Run with `uvicorn server:app --reload` for live updates

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
