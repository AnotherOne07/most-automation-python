"""
Módulo centralizado para armazenamento dee seletores CSS e XPath.
Facilita a manutenção caso a interface do Portal de Transparência sofra alterações.
"""

class BuscaSelectors:
    """Seletores da página inicial e de resultados da busca."""
    PERSON_BT_SEARCH = "#button-consulta-pessoa-fisica"
    INPUT_TERMO = "#termo"
    BTN_BUSCA_REFINADA = "button[aria-controls='box-busca-refinada']"
    BOX_BUSCA_REFINADA = "#box-busca-refinada"
    CHECK_BENEFICIARIO = "input#beneficiarioProgramaSocial"
    BTN_CONSULTAR = "button#btnConsultarPF"
    MSG_SEM_RESULTADO = "text='Nenhum resultado'"
    CONTAINER_RESULTADOS = "span#resultados"
    LINK_PRIMEIRO_RESULTADO = "a.link-busca-nome"

class PanoramaSelectors:
    """Seletores da página de Panorama da pessoa."""
    SECAO_DADOS = "section.dados-tabelados"
    
    CUSTOM_HEADER = "div:has(strong:text-is('{}')) span"
    
    BTN_ACCORDION_RECURSOS = 'button[aria-controls="accordion-recebimentos-recursos"]'
    CONTEUDO_ACCORDION = '#accordion-recebimentos-recursos'
    TIPO_BENEFICIO = "div.responsive strong"
    LINHAS_TABELA = "table tbody tr"
    BTN_DETALHAR = 'a.br-button:has-text("Detalhar")'

class DetalhesSelectors:
    """Seletores da página de detalhes do benefício."""
    LINHAS_TABELA_PAGAMENTOS = "section.dados-detalhados table tbody tr"