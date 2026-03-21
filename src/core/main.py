import os
import sys
import asyncio
from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security.api_key import APIKeyHeader
from src.api.schemas import ConsultRequest, ConsultResponse
from src.bot.web_bot import PortalTransferenciaBot
from dotenv import load_dotenv

load_dotenv()

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

API_KEY_NAME = "Api-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def get_api_key(api_key_header: str = Security(api_key_header)):
    expected_key = os.getenv("API_SECRET_KEY")
    if api_key_header != expected_key:
        raise HTTPException(status_code=401, detail="Acesso Negado: API Key inválida ou ausente")
    return api_key_header

app = FastAPI(
    title="API para bot do Portal de Transparência",
    description="API para automação de extração de dados governamentais",
    version="1.0.0"
)

@app.post("/consultar", response_model=ConsultResponse)
async def consultar_portal(request: ConsultRequest, api_key: str = Depends(get_api_key)):
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