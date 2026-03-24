# Motor de Web Scraping

import asyncio
import base64
import os
import json
from datetime import datetime
from playwright.async_api import async_playwright, Page, BrowserContext

# Importação do arquivo de seletores
from src.bot.selectors import BuscaSelectors, PanoramaSelectors, DetalhesSelectors

class PortalTransferenciaBot:
    """
    Robô assíncrono para coleta de dados de benefícios no portal de transparência.
    """ 
    def __init__(self, headless: bool = True):
        self.base_url = os.getenv("PORTAL_BASE_URL", "https://portaldatransparencia.gov.br/pessoa/visao-geral")
        self.headless = headless
        self.browser = None
        self.context = None
        self.page = None

    async def _setup_browser(self):
        """Configura o navegador definindo medidas básicas de evasão e viewport."""
        self.playwright = await async_playwright().start()

        self.browser = await self.playwright.chromium.launch(headless=self.headless)

        self.context = await self.browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0;Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            accept_downloads=True,
            locale="pt-BR",
            timezone_id="America/Sao_Paulo"
        )
        self.page = await self.context.new_page()

        """ 
        Script "forçado" de iniciação, serve para mascarar a "identidade" do bot
        omitindo a flag webdriver e sobrescrevendo permissões do navegador
        """

        await self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            window.navigator.chrome = {
                runtime: {},
            };
        
            const originalQuery = window.navigator.permissions.query;
            return window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)

    async def _get_screenshot_bas64(self) -> str:
        """Captura screenshot da tela atual e converte para string base64."""
        screenshot_bytes = await self.page.screenshot(full_page=True)
        return base64.b64encode(screenshot_bytes).decode('utf-8')
    
    async def _extract_all_benefits(self, type_benefit: str, qt_rows: int) -> tuple:
        """
        Método privado para iterar sobre as linhas de benefícios, entrar em detalhes, 
        extrair a tabela de histórico e voltar para o panorama geral.
        Retorna uma tupla contendo (lista_recursos_recebidos, lista_detalhes_historico).
        """
        received_resources = []
        details_list = []

        for i in range(qt_rows):
            content_updated = self.page.locator(PanoramaSelectors.CONTEUDO_ACCORDION)
            current_row = content_updated.locator(PanoramaSelectors.LINHAS_TABELA).nth(i)
            
            value_received = await current_row.locator("td").nth(3).inner_text()
            value_clean = value_received.strip()

            received_resources.append({
                "tipo": type_benefit,
                "valor": value_clean
            })

            btn_detail = current_row.locator(PanoramaSelectors.BTN_DETALHAR)
            print(f"    -> Acessando detalhe {i+1} ({value_clean})...")
            
            await btn_detail.click()
            await self.page.wait_for_load_state("networkidle")

            print(f"    -> Aguardando tabela de detalhamento carregar")
            row_selector = DetalhesSelectors.LINHAS_TABELA_PAGAMENTOS
            await self.page.wait_for_selector(row_selector, state="visible")

            # Linhas de pagamento
            payment_rows = await self.page.locator(row_selector).all()
            payment_history = []

            for row in payment_rows:
                columns = await row.locator("td").all()
                if len(columns) >= 6:
                    payment_history.append({
                        "mes_disponibilizacao": (await columns[0].inner_text()).strip(),
                        "numero_parcela": (await columns[1].inner_text()).strip(),
                        "uf": (await columns[2].inner_text()).strip(),
                        "municipio": (await columns[3].inner_text()).strip(),
                        "enquadramento": (await columns[4].inner_text()).strip(),
                        "valor_parcela": (await columns[5].inner_text()).strip()
                    })

            details_list.append({
                "tipo": type_benefit,
                "valor_referencia_panorama": value_clean,
                "total_parcelas_extraidas": len(payment_history),
                "historico_pagamentos": payment_history
            })
            print(f"    -> {len(payment_history)} parcelas extraídas com sucesso!")

            await self.page.go_back(wait_until="networkidle")

            # Verificando se o accordion está aberto após retornar
            content_accordion_post_return = self.page.locator(PanoramaSelectors.CONTEUDO_ACCORDION)
            if not await content_accordion_post_return.is_visible():
                await self.page.locator(PanoramaSelectors.BTN_ACCORDION_RECURSOS).click()
                await content_accordion_post_return.wait_for(state="visible")
                
        return received_resources, details_list

    async def run(self, nome: str = None, cpf_nis: str = None):
        await self._setup_browser()

        result = {
            "query_time": datetime.now().isoformat(),
            "input_params": {"nome": nome, "cpf_nis": cpf_nis},
            "success": False,
            "error_msg": None,
            "data": {},
            "details": [],
            "screenshots_b64": None
        }

        try:
            # Navegação
            print("[*] Acessando portal...")
            await self.page.goto(self.base_url, wait_until="networkidle")

            await self.page.locator(BuscaSelectors.PERSON_BT_SEARCH).click()

            # User-input e filtragem
            print(f"[*] Preenchendo dados de busca: {cpf_nis if cpf_nis else nome}...")
            search_input = BuscaSelectors.INPUT_TERMO
            await self.page.fill(search_input, cpf_nis if cpf_nis else nome)
            

            # # Expandir accordion de busca refinada
            # await self.page.locator(BuscaSelectors.BTN_BUSCA_REFINADA).click()
            # # Aguarda o elemento estar disponível
            # await self.page.locator(BuscaSelectors.BOX_BUSCA_REFINADA).wait_for(state="visible")
            # # Marca filtro de beneficiario
            # await self.page.locator(BuscaSelectors.CHECK_BENEFICIARIO).check()

            # Tratamento de interação com a interface para o caso de ser exibido o modal dos cookies
            try: 
                cookie_btn = self.page.locator('button:has-text("Aceitar")').first
                if await cookie_btn.is_visible(timeout=2000):
                    await cookie_btn.click()
            except Exception:
                pass

            await self.page.wait_for_timeout(1000)
            btn_ref_search = self.page.locator(BuscaSelectors.BTN_BUSCA_REFINADA).locator("span.title")
            await btn_ref_search.scroll_into_view_if_needed()
            await btn_ref_search.click()
            # Pausa para dar tempo da página completar a animação do accordion
            await self.page.wait_for_timeout(1000)
            await self.page.locator(BuscaSelectors.CHECK_BENEFICIARIO).evaluate("node => node.checked = true")

            print("[*]Submetendo filtro...")
            btn_consult = self.page.locator(BuscaSelectors.BTN_CONSULTAR)
            await btn_consult.scroll_into_view_if_needed()
            await btn_consult.evaluate("node => node.click()")

            # Aguarda página carregar após submeter o formulário
            await self.page.wait_for_load_state("networkidle")

            # Aguarda até que o elemento dos resultados esteja visível na tela
            result_container = self.page.locator(BuscaSelectors.CONTAINER_RESULTADOS)
            await result_container.wait_for(state="visible", timeout=5000)

            # Fail verification: Verifica se algum resultado foi encontrado na busca
            if await self.page.locator(BuscaSelectors.MSG_SEM_RESULTADO).count() > 0:
                if cpf_nis: # Cenário de Erro: CPF
                    raise Exception("Não foi possível retornar os dados no tempo de resposta solicitado")
                else: # Cenário de Erro: Nome
                    raise Exception(f"Foram encontrados 0 resultados para o termo {nome}")
            
            # Acessando o primeiro elemento no container de resultados
            first_result = result_container.locator(BuscaSelectors.LINK_PRIMEIRO_RESULTADO).first
            result_name = await first_result.inner_text()
            print(f"[*] Acessando perfil de: {result_name}")
            await first_result.click()
            await self.page.wait_for_load_state("networkidle")

            # Coleta de dadoos na página de panorama
            await self.page.wait_for_selector(PanoramaSelectors.SECAO_DADOS, state="visible")

            async def get_header(label: str) -> str:
                selector = f"strong:text-is('{label}') + span"
                element = self.page.locator(PanoramaSelectors.SECAO_DADOS).locator(selector)
                text = await element.inner_text()
                return text.strip()
            
            print("[*] Extraindo dados básicos...")
            name = await get_header("Nome")
            cpf = await get_header("CPF")
            locale = await get_header("Localidade")

            result["data"] = {
                "nome": name,
                "cpf": cpf,
                "localidade": locale,
                "recursos_recebidos": []
            }

            print(f"    -> Nome: {name} | CPF: {cpf}")

            btn_accordion = self.page.locator(PanoramaSelectors.BTN_ACCORDION_RECURSOS)
            content_accordion = self.page.locator(PanoramaSelectors.CONTEUDO_ACCORDION)

            if not await content_accordion.is_visible():
                await btn_accordion.click()
                await content_accordion.wait_for(state="visible")

            type_benefit_locator = content_accordion.locator(PanoramaSelectors.TIPO_BENEFICIO).first
            type_benefit = await type_benefit_locator.inner_text() if await type_benefit_locator.count() > 0 else "Benefício Desconhecido"

            print("[*] Capturando screenshot...")
            result["screenshots_b64"] = await self._get_screenshot_bas64()

            # Navegação pelos detalhes dos Benefícios
            table_rows = await content_accordion.locator(PanoramaSelectors.LINHAS_TABELA).all()
            qt_rows = len(table_rows)

            print(f" Encontrados {qt_rows} registro(s) para {type_benefit.strip()}.")

            resources, details = await self._extract_all_benefits(type_benefit, qt_rows)

            result["data"]["recursos_recebidos"] = resources
            result["details"] = details
            result["success"] = True
        except Exception as e:
            print(f"[-] Erro crítico na automação: {e}")
            result["error_msg"] = str(e)
        finally:
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()

            return result
        
if __name__ == "__main__":
    async def run_local_test():
        os.makedirs("data", exist_ok=True)
        
        bot = PortalTransferenciaBot(headless=False)
        data = await bot.run(nome="JOAO DA SILVA")

        with open("data/test_output.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        
        if data['screenshots_b64']:
            print(f"[+] Imagem base64 gerada (tamanho: {len(data['screenshots_b64'])} caracteres)")

    asyncio.run(run_local_test())