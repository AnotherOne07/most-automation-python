from fastapi import FastAPI, HTTPException
from src.api.schemas import ConsultRequest, ConsultResponse
from src.bot.web_bot import PortalTransferenciaBot
import os, sys
import asyncio
from dotenv import load_dotenv

load_dotenv()

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

app = FastAPI(
    title="API para bot do Portal de Transparência",
    description="API para automação de extração de dados governamentais",
    version="1.0.0"
)

@app.post("/consultar", response_model=ConsultResponse)
async def consultar_portal(request: ConsultRequest):
    bot = PortalTransferenciaBot(headless=True)

    try:
        result = await bot.run(nome=request.name, cpf_nis=request.cpf_nis)

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error_msg"])
        
        return ConsultResponse(
            success=True,
            data=result.get("data"),
            details=result.get("details")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
if __name__ == "__main__":
    import uvicorn
    import os

    port = int(os.getenv("API_PORT", 8000))
    host = os.getenv("API_HOST", "0.0.0.0")
    uvicorn.run("src.core.main:app", host=host, port=port)